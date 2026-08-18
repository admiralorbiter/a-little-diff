"""MOOSEDev RDF/N-Quads epistemic adapter."""

from pathlib import Path
from typing import Any, Optional
import rdflib
from rdflib import RDF, RDFS, Namespace, URIRef, Literal as RDFLiteral

from alittlediff.adapters.base import EpistemicAdapter
from alittlediff.domain.evidence import Evidence
from alittlediff.domain.record import EpistemicRecord
from alittlediff.domain.relation import Relation
from alittlediff.domain.state import EpistemicState
from alittlediff.git.exceptions import GitError, MissingKnowledgeSnapshotError
from alittlediff.git.snapshots import load_moosedev_snapshot

# Common namespace definitions
DCTERMS = Namespace("http://purl.org/dc/terms/")
DC = Namespace("http://purl.org/dc/elements/1.1/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
MOOSE = Namespace("https://moosedev.org/ontology/")

GENERIC_TYPES = {
    "Resource",
    "NamedIndividual",
    "InformationRecord",
    "Record",
    "Thing",
    "Entity",
}


def _extract_local_name(uri_or_str: str | URIRef) -> str:
    """Extract clean local name from URI or URN."""
    s = str(uri_or_str)
    if "#" in s:
        return s.rsplit("#", 1)[-1]
    if "/" in s:
        return s.rsplit("/", 1)[-1]
    if ":" in s:
        return s.rsplit(":", 1)[-1]
    return s


class MOOSEDevAdapter:
    """Adapter for loading and normalizing MOOSEDev N-Quads epistemic snapshots."""

    def __init__(self, filename: str = ".moosedev/kg.nq"):
        self.filename = filename

    def can_load(self, repo_path: Path, revision: str) -> bool:
        """Check if MOOSEDev snapshot file exists at the given Git revision."""
        try:
            load_moosedev_snapshot(repo_path, revision, self.filename)
            return True
        except (GitError, Exception):
            return False

    def load_state(self, repo_path: Path, revision: str) -> EpistemicState:
        """Load and normalize MOOSEDev epistemic state from a Git revision."""
        nquads_text = load_moosedev_snapshot(repo_path, revision, self.filename)
        return self.parse_nquads(nquads_text, revision=revision, file_path=self.filename)

    def parse_nquads(
        self,
        nquads_text: str,
        revision: str = "snapshot",
        file_path: str = ".moosedev/kg.nq",
    ) -> EpistemicState:
        """Parse raw N-Quads string into a deterministic EpistemicState."""
        dataset = rdflib.Dataset()
        try:
            dataset.parse(data=nquads_text, format="nquads")
        except Exception:
            # Fallback to NTriples / general parser if dataset nquads parser encounters format quirks
            dataset.parse(data=nquads_text, format="nt")

        # Collect all triples/quads grouped by subject across all named graphs
        quads_by_subject: dict[URIRef, list[tuple[Any, Any]]] = {}
        for s, p, o, _ in dataset.quads((None, None, None)):
            if isinstance(s, URIRef):
                quads_by_subject.setdefault(s, []).append((p, o))

        records: dict[str, EpistemicRecord] = {}

        for subj, pred_objs in quads_by_subject.items():
            subj_id = str(subj)
            types: list[str] = []
            # Priority-keyed title/claim/status buckets (lower number = higher priority)
            title_candidates: dict[int, str] = {}
            claim_candidates: dict[int, str] = {}
            status_candidates: dict[int, str] = {}
            relations: list[Relation] = []
            metadata: dict[str, list[Any]] = {}

            # Examine all properties of this subject
            for pred, obj in pred_objs:
                pred_str = str(pred)
                pred_name = _extract_local_name(pred)

                if pred == RDF.type:
                    type_name = _extract_local_name(obj)
                    types.append(type_name)
                    continue

                if isinstance(obj, RDFLiteral):
                    val = str(obj.value if obj.value is not None else obj)
                    pn = pred_name.lower()

                    # Title properties (priority: hasTitle > dcterms:title > rdfs:label > skos:prefLabel > other)
                    if pn == "hastitle":
                        title_candidates.setdefault(0, val)
                    elif pred == DCTERMS.title or pred == DC.title:
                        title_candidates.setdefault(1, val)
                    elif pred == RDFS.label or pn in ("label", "name"):
                        title_candidates.setdefault(2, val)
                    elif pred == SKOS.prefLabel:
                        title_candidates.setdefault(3, val)
                    elif pn == "title":
                        title_candidates.setdefault(4, val)
                    # Claim / Description properties (priority: hasDescription > dcterms:description > rdfs:comment > skos:definition > other)
                    elif pn == "hasdescription":
                        claim_candidates.setdefault(0, val)
                    elif pred == DCTERMS.description or pred == DC.description:
                        claim_candidates.setdefault(1, val)
                    elif pred == RDFS.comment:
                        claim_candidates.setdefault(2, val)
                    elif pred == SKOS.definition:
                        claim_candidates.setdefault(3, val)
                    elif pn in ("description", "claim", "body", "proposition", "summary", "comment"):
                        claim_candidates.setdefault(4, val)
                    # Status / Lifecycle properties (priority: hasLifecycleStatus > hasStatus > other)
                    elif pn == "haslifecyclestatus":
                        status_candidates.setdefault(0, val.lower())
                    elif pn in ("lifecyclestatus", "lifecyclestate"):
                        status_candidates.setdefault(1, val.lower())
                    elif pn in ("hasstatus", "status", "state"):
                        status_candidates.setdefault(2, val.lower())
                    else:
                        metadata.setdefault(pred_name, []).append(val)
                elif isinstance(obj, URIRef):
                    obj_id = str(obj)
                    # Relationship
                    rel_evidence = [
                        Evidence(
                            source_type="moosedev",
                            source_id=subj_id,
                            revision=revision,
                            path=file_path,
                            locator=pred_str,
                            excerpt=f"{subj_id} {pred_name} {obj_id}",
                        )
                    ]
                    relations.append(
                        Relation(
                            predicate=pred_name,
                            subject_id=subj_id,
                            object_id=obj_id,
                            evidence=rel_evidence,
                        )
                    )

            # Determine kind
            kind = "Record"
            specific_types = [t for t in types if t not in GENERIC_TYPES]
            if specific_types:
                kind = specific_types[0]
            elif types:
                kind = types[0]

            # Determine primary title, claim, and status by priority
            primary_title = title_candidates[min(title_candidates)] if title_candidates else None
            primary_claim = claim_candidates[min(claim_candidates)] if claim_candidates else None
            primary_status = status_candidates[min(status_candidates)] if status_candidates else "accepted"

            # Sort relations deterministically
            relations.sort(key=lambda r: (r.predicate, r.object_id))

            record_evidence = [
                Evidence(
                    source_type="moosedev",
                    source_id=subj_id,
                    revision=revision,
                    path=file_path,
                    locator=subj_id,
                    excerpt=primary_claim or primary_title or subj_id,
                )
            ]

            clean_metadata = {k: v[0] if len(v) == 1 else v for k, v in sorted(metadata.items())}

            records[subj_id] = EpistemicRecord(
                id=subj_id,
                kind=kind,
                title=primary_title,
                claim=primary_claim,
                status=primary_status,
                relations=relations,
                evidence=record_evidence,
                source_metadata=clean_metadata,
            )

        # Sort records deterministically by ID
        sorted_records = {k: records[k] for k in sorted(records.keys())}

        return EpistemicState(
            source="moosedev",
            revision=revision,
            records=sorted_records,
        )
