"""Executable metamorphic transformations for epistemic state representations."""

import random
import re


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
    lines = [line.strip() for line in nquads.splitlines() if line.strip()]
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
    lines = [line.strip() for line in nquads.splitlines() if line.strip()]
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


TRANSFORMATION_REGISTRY = {
    "line_order_permutation": line_order_permutation,
    "whitespace_normalization": whitespace_normalization,
    "crlf_vs_lf": crlf_vs_lf,
    "named_graph_equivalence": named_graph_equivalence,
    "duplicate_triple_injection": duplicate_triple_injection,
    "irrelevant_record_injection": irrelevant_record_injection,
    "unrelated_retired_noise": unrelated_retired_noise,
    "unrelated_substrate_isolation": unrelated_substrate_isolation,
}
