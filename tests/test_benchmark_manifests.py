import json
from pathlib import Path
import pytest

from alittlediff.adapters.moosedev import MOOSEDevAdapter
from alittlediff.diff.structural import diff_states
from alittlediff.impact import find_impacts

MANIFESTS_DIR = Path(__file__).parent.parent / "benchmarks" / "manifests"
MANIFEST_FILES = sorted(MANIFESTS_DIR.glob("*.json"))


@pytest.mark.parametrize("manifest_path", MANIFEST_FILES, ids=lambda p: p.stem)
def test_benchmark_manifest_oracle(manifest_path: Path):
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    adapter = MOOSEDevAdapter()
    state_a = adapter.parse_nquads(data["state_a_nquads"], revision="rev_a")
    state_b = adapter.parse_nquads(data["state_b_nquads"], revision="rev_b")

    changes = diff_states(state_a, state_b)
    impacts = find_impacts(changes, state_a, state_b)

    # Validate changes
    expected_changes = data.get("expected_changes", [])
    assert len(changes) == len(expected_changes), (
        f"Manifest {data['id']}: expected {len(expected_changes)} changes, got {len(changes)}"
    )
    for exp_chg, actual_chg in zip(expected_changes, changes):
        if "structural_type" in exp_chg:
            assert actual_chg.structural_type == exp_chg["structural_type"]

    # Validate impacts (Core Bench deterministic pass criteria)
    expected_impacts = data.get("expected_impacts", [])
    assert len(impacts) == len(expected_impacts), (
        f"Manifest {data['id']}: expected {len(expected_impacts)} impacts, got {len(impacts)}"
    )
    for exp_imp, actual_imp in zip(expected_impacts, impacts):
        if "target_id" in exp_imp:
            assert actual_imp.target_record_id == exp_imp["target_id"]
        if "effect" in exp_imp:
            assert actual_imp.effect == exp_imp["effect"]
        if "confidence" in exp_imp:
            assert actual_imp.confidence == exp_imp["confidence"]
        if "predicate" in exp_imp and actual_imp.path:
            assert any(r.predicate == exp_imp["predicate"] for r in actual_imp.path)

    # Validate non-impacts
    for non_impact_id in data.get("expected_non_impacts", []):
        impacted_targets = {imp.target_record_id for imp in impacts}
        assert non_impact_id not in impacted_targets, (
            f"Manifest {data['id']}: non-impact {non_impact_id} was unexpectedly flagged"
        )
