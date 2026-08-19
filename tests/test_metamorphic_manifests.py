import json
from pathlib import Path
import pytest
from collections import Counter

from alittlediff.adapters.moosedev import MOOSEDevAdapter
from alittlediff.diff.structural import diff_states
from alittlediff.impact import find_impacts
from benchmarks.schema import BenchmarkManifest
from benchmarks.metamorphic.transformations import TRANSFORMATION_REGISTRY

MANIFESTS_DIR = Path(__file__).parent.parent / "benchmarks" / "manifests"
MANIFEST_FILES = sorted(MANIFESTS_DIR.glob("*.json"))

# Collect all (manifest_path, invariant_name) pairs and strictly fail if any invariant is unsupported
PARAMETRIZED_CASES = []
for m_path in MANIFEST_FILES:
    with open(m_path, "r", encoding="utf-8") as f:
        m = BenchmarkManifest.model_validate_json(f.read())
    for inv in m.metamorphic_invariants:
        inv_str = inv.value if hasattr(inv, "value") else str(inv)
        if inv_str not in TRANSFORMATION_REGISTRY:
            raise ValueError(
                f"Manifest '{m.id}' declares unsupported metamorphic invariant '{inv_str}'. "
                f"Must be one of {sorted(TRANSFORMATION_REGISTRY.keys())}"
            )
        PARAMETRIZED_CASES.append((m_path, inv_str))


@pytest.mark.parametrize(
    "manifest_path,invariant_name",
    PARAMETRIZED_CASES,
    ids=[f"{p[0].stem}__x__{p[1]}" for p in PARAMETRIZED_CASES],
)
def test_manifest_metamorphic_invariance(manifest_path: Path, invariant_name: str):
    """Execute declared metamorphic transformation on manifest and verify invariant preservation.
    
    Because the same transformation is applied to both State A and State B,
    the resulting primary structural changes and downstream causal impacts must be identical.
    """
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = BenchmarkManifest.model_validate_json(f.read())

    adapter = MOOSEDevAdapter()
    transform_fn = TRANSFORMATION_REGISTRY[invariant_name]

    # Baseline run
    base_a = adapter.parse_nquads(manifest.state_a_nquads, revision="base_a")
    base_b = adapter.parse_nquads(manifest.state_b_nquads, revision="base_b")
    max_depth = 2 if "two_hop" in manifest.id else 1
    base_changes = diff_states(base_a, base_b)
    base_impacts = find_impacts(base_changes, base_a, base_b, max_depth=max_depth)

    # Transformed run
    trans_nquads_a = transform_fn(manifest.state_a_nquads, seed=42)
    trans_nquads_b = transform_fn(manifest.state_b_nquads, seed=42)

    trans_a = adapter.parse_nquads(trans_nquads_a, revision="trans_a")
    trans_b = adapter.parse_nquads(trans_nquads_b, revision="trans_b")
    trans_changes = diff_states(trans_a, trans_b)
    trans_impacts = find_impacts(trans_changes, trans_a, trans_b, max_depth=max_depth)

    # 1. Structural change multiset invariance (no kind-based filtering)
    base_change_sigs = Counter(
        (c.structural_type, c.before.id if c.before else None, c.after.id if c.after else None)
        for c in base_changes
    )
    trans_change_sigs = Counter(
        (c.structural_type, c.before.id if c.before else None, c.after.id if c.after else None)
        for c in trans_changes
    )
    assert base_change_sigs == trans_change_sigs, (
        f"Change signature divergence under {invariant_name}:\n"
        f"  Baseline:    {dict(base_change_sigs)}\n"
        f"  Transformed: {dict(trans_change_sigs)}"
    )

    # 2. Impact multiset invariance
    base_impact_sigs = Counter(
        (imp.target_record_id, imp.effect, imp.confidence)
        for imp in base_impacts
    )
    trans_impact_sigs = Counter(
        (imp.target_record_id, imp.effect, imp.confidence)
        for imp in trans_impacts
    )
    assert base_impact_sigs == trans_impact_sigs, (
        f"Impact signature divergence under {invariant_name}:\n"
        f"  Baseline:    {dict(base_impact_sigs)}\n"
        f"  Transformed: {dict(trans_impact_sigs)}"
    )
