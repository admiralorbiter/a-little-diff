from collections import Counter
import json
from pathlib import Path
import pytest

from alittlediff.adapters.moosedev import MOOSEDevAdapter
from alittlediff.diff.structural import diff_states
from alittlediff.impact import find_impacts
from benchmarks.schema import BenchmarkManifest

MANIFESTS_DIR = Path(__file__).parent.parent / "benchmarks" / "manifests"
MANIFEST_FILES = sorted(MANIFESTS_DIR.glob("*.json"))


@pytest.mark.parametrize("manifest_path", MANIFEST_FILES, ids=lambda p: p.stem)
def test_benchmark_manifest_oracle(manifest_path: Path):
    """Execute Core Bench oracle tests using exact multiset Counter matching."""
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = BenchmarkManifest.model_validate_json(f.read())

    adapter = MOOSEDevAdapter()
    state_a = adapter.parse_nquads(manifest.state_a_nquads, revision="rev_a")
    state_b = adapter.parse_nquads(manifest.state_b_nquads, revision="rev_b")

    changes = diff_states(state_a, state_b)
    max_depth = 2 if "two_hop" in manifest.id else 1
    impacts = find_impacts(changes, state_a, state_b, max_depth=max_depth)

    # 1. Exact Multiset Change Comparison
    actual_change_sigs = Counter(
        (c.structural_type, c.before.id if c.before else None, c.after.id if c.after else None)
        for c in changes
    )
    expected_change_sigs = Counter(
        (exp.structural_type, exp.before_id, exp.after_id)
        for exp in manifest.expected_changes
    )
    assert actual_change_sigs == expected_change_sigs, (
        f"Manifest {manifest.id}: structural change signature mismatch:\n"
        f"  Actual:   {dict(actual_change_sigs)}\n"
        f"  Expected: {dict(expected_change_sigs)}"
    )

    # 2. Exact Multiset Impact Comparison
    actual_impact_sigs = Counter(
        (
            imp.target_record_id,
            imp.effect,
            imp.confidence,
            imp.path[0].predicate if imp.path else ""
        )
        for imp in impacts
    )
    expected_impact_sigs = Counter(
        (exp.target_id, exp.effect, exp.confidence, exp.predicate)
        for exp in manifest.expected_impacts
    )
    assert actual_impact_sigs == expected_impact_sigs, (
        f"Manifest {manifest.id}: causal impact signature mismatch:\n"
        f"  Actual:   {dict(actual_impact_sigs)}\n"
        f"  Expected: {dict(expected_impact_sigs)}"
    )

    # 3. Non-Impact Verification
    impacted_target_ids = {imp.target_record_id for imp in impacts}
    for non_impact_id in manifest.expected_non_impacts:
        assert non_impact_id not in impacted_target_ids, (
            f"Manifest {manifest.id}: non-impact {non_impact_id} was unexpectedly flagged"
        )
