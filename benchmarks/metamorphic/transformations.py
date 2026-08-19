"""Executable metamorphic transformations for epistemic state representations."""

import random
import re

INVERSE_PREDICATE_MAP = {
    "constrains": "isConstrainedBy",
    "isConstrainedBy": "constrains",
    "constrainedBy": "constrains",
    "motivates": "isMotivatedBy",
    "isMotivatedBy": "motivates",
    "resultsIn": "resultsFrom",
    "resultsFrom": "resultsIn",
}


def line_order_permutation(nquads: str, seed: int = 42) -> str:
    """Permute line order of N-Quads."""
    clean = nquads.lstrip("\ufeff")
    lines = [line.strip() for line in clean.splitlines() if line.strip()]
    rng = random.Random(seed)
    rng.shuffle(lines)
    return "\n".join(lines) + "\n"


def whitespace_normalization(nquads: str, seed: int = 42) -> str:
    """Inject extra whitespace between tokens."""
    clean = nquads.lstrip("\ufeff")
    lines = [line.strip() for line in clean.splitlines() if line.strip()]
    transformed = []
    for line in lines:
        parts = line.split(" ", 2)
        if len(parts) == 3:
            transformed.append(f"  {parts[0]}   {parts[1]}   {parts[2]}")
        else:
            transformed.append(f"   {line}")
    return "\n".join(transformed) + "\n"


def crlf_vs_lf(nquads: str, seed: int = 42) -> str:
    """Ensure Windows CRLF line endings."""
    clean = nquads.replace("\r\n", "\n").replace("\r", "\n")
    return clean.replace("\n", "\r\n")


def named_graph_equivalence(nquads: str, seed: int = 42) -> str:
    """Wrap triples into named graph quads."""
    clean = nquads.lstrip("\ufeff")
    lines = [line.strip() for line in clean.splitlines() if line.strip()]
    transformed = []
    for line in lines:
        if line.endswith("."):
            core = line[:-1].strip()
            transformed.append(f"{core} <urn:graph:metamorphic> .")
        else:
            transformed.append(line)
    return "\n".join(transformed) + "\n"


def duplicate_triple_injection(nquads: str, seed: int = 42) -> str:
    """Inject duplicate triples."""
    clean = nquads.lstrip("\ufeff")
    lines = [line.strip() for line in clean.splitlines() if line.strip()]
    dup_lines = list(lines)
    if lines:
        dup_lines.append(lines[0])
        if len(lines) > 1:
            dup_lines.append(lines[1])
    return "\n".join(dup_lines) + "\n"


def irrelevant_record_injection(nquads: str, seed: int = 42) -> str:
    """Inject an unlinked active Requirement."""
    noise = """
<urn:rec:noise:requirement> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Requirement> .
<urn:rec:noise:requirement> <https://moosedev.org/ontology/hasTitle> "Unrelated audit log policy" .
<urn:rec:noise:requirement> <https://moosedev.org/ontology/hasLifecycleStatus> "accepted" .
"""
    return nquads + "\n" + noise


def irrelevant_metadata_injection(nquads: str, seed: int = 42) -> str:
    """Inject non-functional metadata triples (e.g. comments/notes) on existing subjects."""
    clean = nquads.lstrip("\ufeff")
    lines = [line.strip() for line in clean.splitlines() if line.strip()]
    subjects = set()
    for line in lines:
        if line.startswith("<"):
            subj = line.split(">", 1)[0] + ">"
            subjects.add(subj)

    meta_lines = []
    for subj in sorted(subjects):
        meta_lines.append(f'{subj} <http://www.w3.org/2000/01/rdf-schema#comment> "Metamorphic annotation note." .')
    return nquads + "\n" + "\n".join(meta_lines) + "\n"


def unrelated_retired_noise(nquads: str, seed: int = 42) -> str:
    """Inject an unlinked retired decision."""
    noise = """
<urn:rec:noise:retired> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Decision> .
<urn:rec:noise:retired> <https://moosedev.org/ontology/hasTitle> "Deprecated local store" .
<urn:rec:noise:retired> <https://moosedev.org/ontology/hasLifecycleStatus> "retracted" .
"""
    return nquads + "\n" + noise


def unrelated_substrate_isolation(nquads: str, seed: int = 42) -> str:
    """Inject 10 low-level CodeEntity triples."""
    noise_lines = []
    for i in range(10):
        noise_lines.append(f"<urn:code:fn:meta_{i}> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/CodeEntity> .")
        noise_lines.append(f"<urn:code:fn:meta_{i}> <https://moosedev.org/ontology/hasTitle> \"meta_fn_{i}\" .")
    return nquads + "\n" + "\n".join(noise_lines) + "\n"


def direct_inverse_relation_equivalence(nquads: str, seed: int = 42) -> str:
    """Swap causal relationship predicates with their exact inverse representation."""
    clean = nquads.lstrip("\ufeff")
    lines = [line.strip() for line in clean.splitlines() if line.strip()]
    transformed = []
    for line in lines:
        m = re.match(r"^(\s*<[^>]+>)\s+<https://moosedev\.org/ontology/([^>]+)>\s+(<[^>]+>)\s*\.\s*$", line)
        if m:
            subj, pred, obj = m.group(1), m.group(2), m.group(3)
            if pred in INVERSE_PREDICATE_MAP:
                inv_pred = INVERSE_PREDICATE_MAP[pred]
                transformed.append(f"{obj} <https://moosedev.org/ontology/{inv_pred}> {subj} .")
                continue
        transformed.append(line)
    return "\n".join(transformed) + "\n"


def inverse_relation_equivalence(nquads: str, seed: int = 42) -> str:
    """Alias for direct_inverse_relation_equivalence."""
    return direct_inverse_relation_equivalence(nquads, seed=seed)


TRANSFORMATION_REGISTRY = {
    "line_order_permutation": line_order_permutation,
    "whitespace_normalization": whitespace_normalization,
    "crlf_vs_lf": crlf_vs_lf,
    "named_graph_equivalence": named_graph_equivalence,
    "direct_inverse_relation_equivalence": direct_inverse_relation_equivalence,
    "inverse_relation_equivalence": inverse_relation_equivalence,
    "duplicate_triple_injection": duplicate_triple_injection,
    "irrelevant_record_injection": irrelevant_record_injection,
    "irrelevant_metadata_injection": irrelevant_metadata_injection,
    "unrelated_retired_noise": unrelated_retired_noise,
    "unrelated_substrate_isolation": unrelated_substrate_isolation,
}
