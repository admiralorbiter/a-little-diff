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
    """Execute Core Bench oracle tests against strict BenchmarkManifest schema."""
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = BenchmarkManifest.model_validate_json(f.read())

    adapter = MOOSEDevAdapter()
    state_a = adapter.parse_nquads(manifest.state_a_nquads, revision="rev_a")
    state_b = adapter.parse_nquads(manifest.state_b_nquads, revision="rev_b")

    changes = diff_states(state_a, state_b)
    # If scenario requires 2-hop propagation, allow max_depth=2
    max_depth = 2 if "two_hop" in manifest.id else 1
    impacts = find_impacts(changes, state_a, state_b, max_depth=max_depth)

    # 1. Validate Change Count
    assert len(changes) == len(manifest.expected_changes), (
        f"Manifest {manifest.id}: expected {len(manifest.expected_changes)} changes, got {len(changes)}"
    )

    # 2. Validate Change Signatures (order-independent set/matching)
    # Signature: (structural_type, before_id or None, after_id or None)
    actual_change_sigs = []
    for c in changes:
        b_id = c.before.id if c.before else None
        a_id = c.after.id if c.after else None
        actual_change_sigs.append((c.structural_type, b_id, a_id))

    for exp_chg in manifest.expected_changes:
        # If before_id or after_id are specified, match them; otherwise match structural_type
        matched = False
        for actual_sig in actual_change_sigs:
            stype_match = actual_sig[0] == exp_chg.structural_type
            before_match = (exp_chg.before_id is None) or (actual_sig[1] == exp_chg.before_id)
            after_match = (exp_chg.after_id is None) or (actual_sig[2] == exp_chg.after_id)
            if stype_match and before_match and after_match:
                matched = True
                break
        assert matched, (
            f"Manifest {manifest.id}: expected change ({exp_chg.structural_type}, {exp_chg.before_id}, {exp_chg.after_id}) "
            f"not found in actual changes: {actual_change_sigs}"
        )

    # 3. Validate Impact Count & Signatures (Core Bench pass criteria)
    assert len(impacts) == len(manifest.expected_impacts), (
        f"Manifest {manifest.id}: expected {len(manifest.expected_impacts)} impacts, got {len(impacts)}"
    )

    for exp_imp in manifest.expected_impacts:
        matched = False
        for actual_imp in impacts:
            target_match = actual_imp.target_record_id == exp_imp.target_id
            effect_match = actual_imp.effect == exp_imp.effect
            confidence_match = actual_imp.confidence == exp_imp.confidence
            pred_match = (
                actual_imp.path
                and any(r.predicate == exp_imp.predicate for r in actual_imp.path)
            )
            if target_match and effect_match and confidence_match and pred_match:
                matched = True
                break
        assert matched, (
            f"Manifest {manifest.id}: expected impact for target '{exp_imp.target_id}' "
            f"with effect '{exp_imp.effect}', predicate '{exp_imp.predicate}', confidence '{exp_imp.confidence}' "
            f"not matched in actual impacts: {[(i.target_record_id, i.effect, i.confidence) for i in impacts]}"
        )

    # 4. Validate Non-Impacts
    impacted_targets = {imp.target_record_id for imp in impacts}
    for non_impact_id in manifest.expected_non_impacts:
        assert non_impact_id not in impacted_targets, (
            f"Manifest {manifest.id}: non-impact {non_impact_id} was unexpectedly flagged"
        )
