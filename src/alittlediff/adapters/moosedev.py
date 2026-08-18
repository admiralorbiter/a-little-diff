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

        # Collect all unique subject entities
        subjects: set[URIRef] = {s for s in dataset.subjects() if isinstance(s, URIRef)}

        records: dict[str, EpistemicRecord] = {}

        for subj in subjects:
            subj_id = str(subj)
            types: list[str] = []
            titles: list[str] = []
            claims: list[str] = []
            statuses: list[str] = []
            relations: list[Relation] = []
            metadata: dict[str, list[Any]] = {}

            # Examine all properties of this subject
            for pred, obj in dataset.predicate_objects(subject=subj):
                pred_str = str(pred)
                pred_name = _extract_local_name(pred)

                if pred == RDF.type:
                    type_name = _extract_local_name(obj)
                    types.append(type_name)
                    continue

                if isinstance(obj, RDFLiteral):
                    val = str(obj.value if obj.value is not None else obj)
                    
                    # Title properties
                    if pred in (RDFS.label, DCTERMS.title, DC.title, SKOS.prefLabel) or pred_name.lower() in ("hastitle", "title", "label", "name"):
                        titles.append(val)
                    # Claim / Description properties
                    elif pred in (RDFS.comment, DCTERMS.description, DC.description, SKOS.definition) or pred_name.lower() in ("hasdescription", "description", "claim", "body", "proposition", "summary", "comment"):
                        claims.append(val)
                    # Status / Lifecycle properties
                    elif pred_name.lower() in ("haslifecyclestatus", "lifecyclestatus", "lifecyclestate", "hasstatus", "status", "state"):
                        statuses.append(val.lower())
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

            # Determine primary title, claim, and status
            primary_title = titles[0] if titles else None
            primary_claim = claims[0] if claims else None
            primary_status = statuses[0] if statuses else "accepted"

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
