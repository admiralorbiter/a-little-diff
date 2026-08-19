"""Hypothesis stateful testing simulating temporal software project evolution."""

from hypothesis import settings, strategies as st
from hypothesis.stateful import Bundle, RuleBasedStateMachine, invariant, rule

from alittlediff.adapters.moosedev import MOOSEDevAdapter
from alittlediff.diff.structural import diff_states
from alittlediff.impact import find_impacts
from tests.reference_evaluator import reference_find_impacts

KINDS = ["Decision", "Constraint", "Requirement", "Lesson", "Consequence"]
PREDICATES = ["constrains", "isConstrainedBy", "isMotivatedBy", "resultsIn", "learnedFrom"]


class EpistemicHistoryMachine(RuleBasedStateMachine):
    """Simulates a sequence of knowledge-graph mutations over project history."""

    def __init__(self):
        super().__init__()
        self.records: dict[str, dict] = {}
        self.counter = 0
        self.prev_nquads: str | None = None
        self.last_op: str = "init"

    records_bundle = Bundle("records_bundle")

    def _snapshot(self):
        self.prev_nquads = self._to_nquads()

    @rule(
        target=records_bundle,
        kind=st.sampled_from(KINDS),
        title=st.text(min_size=3, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    )
    def add_record(self, kind: str, title: str) -> str:
        self._snapshot()
        self.counter += 1
        rec_id = f"urn:rec:item_{self.counter}"
        self.records[rec_id] = {
            "id": rec_id,
            "kind": kind,
            "title": title or "Record",
            "status": "accepted",
            "relations": [],
        }
        self.last_op = "add"
        return rec_id

    @rule(
        target=records_bundle,
        old_id=records_bundle,
        new_title=st.text(min_size=3, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    )
    def supersede_record(self, old_id: str, new_title: str) -> str:
        self._snapshot()
        if old_id not in self.records or self.records[old_id]["status"] != "accepted":
            self.last_op = "noop"
            return old_id

        self.counter += 1
        new_id = f"urn:rec:item_{self.counter}"
        kind = self.records[old_id]["kind"]

        self.records[old_id]["status"] = "superseded"
        self.records[old_id]["relations"].append(("isSupersededBy", new_id))

        self.records[new_id] = {
            "id": new_id,
            "kind": kind,
            "title": new_title or "Updated Record",
            "status": "accepted",
            "relations": [("supersedes", old_id)],
        }
        self.last_op = "supersede"
        return new_id

    @rule(rec_id=records_bundle)
    def retract_record(self, rec_id: str):
        self._snapshot()
        if rec_id in self.records and self.records[rec_id]["status"] == "accepted":
            self.records[rec_id]["status"] = "retracted"
            self.last_op = "retract"
        else:
            self.last_op = "noop"

    @rule(src_id=records_bundle, dst_id=records_bundle, pred=st.sampled_from(PREDICATES))
    def relate_records(self, src_id: str, dst_id: str, pred: str):
        self._snapshot()
        if src_id in self.records and dst_id in self.records and src_id != dst_id:
            if (pred, dst_id) not in self.records[src_id]["relations"]:
                self.records[src_id]["relations"].append((pred, dst_id))
                self.last_op = "relate"
                return
        self.last_op = "noop"

    def _to_nquads(self) -> str:
        lines = []
        for rec in self.records.values():
            r_id = rec["id"]
            lines.append(f"<{r_id}> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/{rec['kind']}> .")
            lines.append(f"<{r_id}> <https://moosedev.org/ontology/hasTitle> \"{rec['title']}\" .")
            lines.append(f"<{r_id}> <https://moosedev.org/ontology/hasLifecycleStatus> \"{rec['status']}\" .")
            for pred, target in rec["relations"]:
                lines.append(f"<{r_id}> <https://moosedev.org/ontology/{pred}> <{target}> .")
        return "\n".join(lines) + "\n"

    @invariant()
    def check_temporal_and_differential_invariants(self):
        curr_nquads = self._to_nquads()
        adapter = MOOSEDevAdapter()
        curr_state = adapter.parse_nquads(curr_nquads, revision="current")

        # 1. Identity Invariant: Diffing current state against itself is empty
        self_changes = diff_states(curr_state, curr_state)
        self_impacts = find_impacts(self_changes, curr_state, curr_state)
        assert len(self_changes) == 0, f"Self-diff yielded non-empty changes: {self_changes}"
        assert len(self_impacts) == 0, f"Self-diff yielded non-empty impacts: {self_impacts}"

        # 2. Temporal Transition Invariant: Diffing previous snapshot against current
        if self.prev_nquads is not None:
            prev_state = adapter.parse_nquads(self.prev_nquads, revision="previous")
            step_changes = diff_states(prev_state, curr_state)
            step_impacts = find_impacts(step_changes, prev_state, curr_state, max_depth=1)

            # Differential reference engine verification on temporal step
            ref_impact_sigs = reference_find_impacts(step_changes, prev_state, curr_state, max_depth=1)
            prod_impact_sigs = {
                (imp.source_change_id, imp.target_record_id, imp.effect, imp.confidence)
                for imp in step_impacts
            }
            assert prod_impact_sigs == ref_impact_sigs, (
                f"Temporal step differential mismatch (op: {self.last_op}):\n"
                f"  Production: {prod_impact_sigs}\n"
                f"  Reference:  {ref_impact_sigs}"
            )

            # Inactive records are never alerted as active reconsideration targets
            for imp in step_impacts:
                tgt = curr_state.get_record(imp.target_record_id) or prev_state.get_record(imp.target_record_id)
                assert tgt is not None and tgt.status == "accepted", (
                    f"Inactive record {imp.target_record_id} with status {getattr(tgt, 'status', None)} "
                    f"was alerted for reconsideration in step {self.last_op}"
                )


TestHistoryMachine = EpistemicHistoryMachine.TestCase
TestHistoryMachine.settings = settings(max_examples=20, stateful_step_count=25, deadline=None)
