"""Hypothesis stateful testing simulating real software project evolution."""

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
        self.history = []

    records_bundle = Bundle("records_bundle")

    @rule(target=records_bundle, kind=st.sampled_from(KINDS), title=st.text(min_size=3, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    def add_record(self, kind: str, title: str) -> str:
        self.counter += 1
        rec_id = f"urn:rec:item_{self.counter}"
        self.records[rec_id] = {
            "id": rec_id,
            "kind": kind,
            "title": title or "Record",
            "status": "accepted",
            "relations": [],
        }
        return rec_id

    @rule(target=records_bundle, old_id=records_bundle, new_title=st.text(min_size=3, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    def supersede_record(self, old_id: str, new_title: str) -> str:
        if old_id not in self.records or self.records[old_id]["status"] != "accepted":
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
        return new_id

    @rule(rec_id=records_bundle)
    def retract_record(self, rec_id: str):
        if rec_id in self.records and self.records[rec_id]["status"] == "accepted":
            self.records[rec_id]["status"] = "retracted"

    @rule(src_id=records_bundle, dst_id=records_bundle, pred=st.sampled_from(PREDICATES))
    def relate_records(self, src_id: str, dst_id: str, pred: str):
        if src_id in self.records and dst_id in self.records and src_id != dst_id:
            self.records[src_id]["relations"].append((pred, dst_id))

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
    def check_identity_invariants(self):
        nquads = self._to_nquads()
        adapter = MOOSEDevAdapter()
        state = adapter.parse_nquads(nquads, revision="current")

        # Identity invariant: Diffing state with itself produces 0 changes, 0 impacts
        changes = diff_states(state, state)
        impacts = find_impacts(changes, state, state)
        assert len(changes) == 0
        assert len(impacts) == 0


TestHistoryMachine = EpistemicHistoryMachine.TestCase
TestHistoryMachine.settings = settings(max_examples=15, stateful_step_count=20, deadline=None)
