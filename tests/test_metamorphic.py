"""Metamorphic testing suite for epistemic diffing and causal impact invariance."""

import random
from alittlediff.adapters.moosedev import MOOSEDevAdapter
from alittlediff.diff.structural import diff_states
from alittlediff.impact import find_impacts
from tests.fixtures.moosedev_fixtures import NQUADS_STATE_A, NQUADS_STATE_B


def test_metamorphic_nquads_line_reordering():
    """Invariance 1: Permuting N-Quads line order must not alter diff or impact results."""
    adapter = MOOSEDevAdapter()

    lines_a = [line for line in NQUADS_STATE_A.splitlines() if line.strip()]
    lines_b = [line for line in NQUADS_STATE_B.splitlines() if line.strip()]

    # Baseline run
    baseline_state_a = adapter.parse_nquads("\n".join(lines_a), revision="base_a")
    baseline_state_b = adapter.parse_nquads("\n".join(lines_b), revision="base_b")
    baseline_changes = diff_states(baseline_state_a, baseline_state_b)
    baseline_impacts = find_impacts(baseline_changes, baseline_state_a, baseline_state_b)

    # Test 5 random permutations
    for seed in range(5):
        rng = random.Random(seed)
        shuffled_a = list(lines_a)
        shuffled_b = list(lines_b)
        rng.shuffle(shuffled_a)
        rng.shuffle(shuffled_b)

        permuted_state_a = adapter.parse_nquads("\n".join(shuffled_a), revision=f"perm_a_{seed}")
        permuted_state_b = adapter.parse_nquads("\n".join(shuffled_b), revision=f"perm_b_{seed}")

        changes = diff_states(permuted_state_a, permuted_state_b)
        impacts = find_impacts(changes, permuted_state_a, permuted_state_b)

        assert len(changes) == len(baseline_changes)
        assert len(impacts) == len(baseline_impacts)

        for c_base, c_perm in zip(baseline_changes, changes):
            assert c_base.change_id == c_perm.change_id
            assert c_base.structural_type == c_perm.structural_type

        for i_base, i_perm in zip(baseline_impacts, impacts):
            assert i_base.target_record_id == i_perm.target_record_id
            assert i_base.effect == i_perm.effect
            assert i_base.confidence == i_perm.confidence


def test_metamorphic_substrate_code_entity_isolation():
    """Invariance 2: Injecting arbitrary CodeEntity triples into State B must not alter architectural changes/impacts."""
    adapter = MOOSEDevAdapter()

    state_a = adapter.parse_nquads(NQUADS_STATE_A, revision="state_a")
    state_b = adapter.parse_nquads(NQUADS_STATE_B, revision="state_b")

    base_changes = diff_states(state_a, state_b)
    base_impacts = find_impacts(base_changes, state_a, state_b)

    # Inject 50 synthetic CodeEntity triples
    injected_lines = [NQUADS_STATE_B]
    for i in range(50):
        injected_lines.append(f"<urn:code:fn_{i}> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/CodeEntity> .")
        injected_lines.append(f"<urn:code:fn_{i}> <https://moosedev.org/ontology/hasTitle> \"function_{i}\" .")

    state_b_injected = adapter.parse_nquads("\n".join(injected_lines), revision="state_b_injected")

    changes = diff_states(state_a, state_b_injected)
    impacts = find_impacts(changes, state_a, state_b_injected)

    # All primary architectural changes & high/med impacts must remain identical
    arch_changes = [c for c in changes if (c.after and c.after.kind != "CodeEntity") or (c.before and c.before.kind != "CodeEntity")]
    arch_impacts = [i for i in impacts if i.confidence in ("high", "medium")]

    assert len(arch_changes) == len(base_changes)
    assert len(arch_impacts) == len(base_impacts)


def test_metamorphic_inverse_predicate_equivalence():
    """Invariance 3: Forward constrains and inverse isConstrainedBy must produce identical impact consequences."""
    adapter = MOOSEDevAdapter()

    # Forward version: Constraint constrains Decision
    fwd_a = """<urn:rec:c1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Constraint> .
<urn:rec:c1> <https://moosedev.org/ontology/hasTitle> "Constraint C1" .
<urn:rec:c1> <https://moosedev.org/ontology/hasLifecycleStatus> "accepted" .
<urn:rec:c1> <https://moosedev.org/ontology/constrains> <urn:rec:d1> .

<urn:rec:d1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Decision> .
<urn:rec:d1> <https://moosedev.org/ontology/hasTitle> "Decision D1" .
<urn:rec:d1> <https://moosedev.org/ontology/hasLifecycleStatus> "accepted" ."""

    fwd_b = """<urn:rec:c1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Constraint> .
<urn:rec:c1> <https://moosedev.org/ontology/hasTitle> "Constraint C1" .
<urn:rec:c1> <https://moosedev.org/ontology/hasLifecycleStatus> "superseded" .
<urn:rec:c1> <https://moosedev.org/ontology/isSupersededBy> <urn:rec:c2> .

<urn:rec:c2> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Constraint> .
<urn:rec:c2> <https://moosedev.org/ontology/hasTitle> "Constraint C2" .
<urn:rec:c2> <https://moosedev.org/ontology/hasLifecycleStatus> "accepted" .
<urn:rec:c2> <https://moosedev.org/ontology/supersedes> <urn:rec:c1> .
<urn:rec:c2> <https://moosedev.org/ontology/constrains> <urn:rec:d1> .

<urn:rec:d1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Decision> .
<urn:rec:d1> <https://moosedev.org/ontology/hasTitle> "Decision D1" .
<urn:rec:d1> <https://moosedev.org/ontology/hasLifecycleStatus> "accepted" ."""

    # Inverse version: Decision isConstrainedBy Constraint
    inv_a = """<urn:rec:c1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Constraint> .
<urn:rec:c1> <https://moosedev.org/ontology/hasTitle> "Constraint C1" .
<urn:rec:c1> <https://moosedev.org/ontology/hasLifecycleStatus> "accepted" .

<urn:rec:d1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Decision> .
<urn:rec:d1> <https://moosedev.org/ontology/hasTitle> "Decision D1" .
<urn:rec:d1> <https://moosedev.org/ontology/hasLifecycleStatus> "accepted" .
<urn:rec:d1> <https://moosedev.org/ontology/isConstrainedBy> <urn:rec:c1> ."""

    inv_b = """<urn:rec:c1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Constraint> .
<urn:rec:c1> <https://moosedev.org/ontology/hasTitle> "Constraint C1" .
<urn:rec:c1> <https://moosedev.org/ontology/hasLifecycleStatus> "superseded" .
<urn:rec:c1> <https://moosedev.org/ontology/isSupersededBy> <urn:rec:c2> .

<urn:rec:c2> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Constraint> .
<urn:rec:c2> <https://moosedev.org/ontology/hasTitle> "Constraint C2" .
<urn:rec:c2> <https://moosedev.org/ontology/hasLifecycleStatus> "accepted" .
<urn:rec:c2> <https://moosedev.org/ontology/supersedes> <urn:rec:c1> .

<urn:rec:d1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Decision> .
<urn:rec:d1> <https://moosedev.org/ontology/hasTitle> "Decision D1" .
<urn:rec:d1> <https://moosedev.org/ontology/hasLifecycleStatus> "accepted" .
<urn:rec:d1> <https://moosedev.org/ontology/isConstrainedBy> <urn:rec:c2> ."""

    state_fwd_a = adapter.parse_nquads(fwd_a, revision="fwd_a")
    state_fwd_b = adapter.parse_nquads(fwd_b, revision="fwd_b")
    changes_fwd = diff_states(state_fwd_a, state_fwd_b)
    impacts_fwd = find_impacts(changes_fwd, state_fwd_a, state_fwd_b)

    state_inv_a = adapter.parse_nquads(inv_a, revision="inv_a")
    state_inv_b = adapter.parse_nquads(inv_b, revision="inv_b")
    changes_inv = diff_states(state_inv_a, state_inv_b)
    impacts_inv = find_impacts(changes_inv, state_inv_a, state_inv_b)

    assert len(impacts_fwd) == 1
    assert len(impacts_inv) == 1
    assert impacts_fwd[0].target_record_id == impacts_inv[0].target_record_id == "urn:rec:d1"
    assert impacts_fwd[0].effect == impacts_inv[0].effect == "constraint_context_changed"
    assert impacts_fwd[0].confidence == impacts_inv[0].confidence == "high"


def test_metamorphic_unrelated_record_neutrality():
    """Invariance 4: Adding unrelated active or retired records must not alter causal consequence chains."""
    adapter = MOOSEDevAdapter()

    state_a = adapter.parse_nquads(NQUADS_STATE_A, revision="a")
    state_b = adapter.parse_nquads(NQUADS_STATE_B, revision="b")

    base_impacts = find_impacts(diff_states(state_a, state_b), state_a, state_b)

    # Inject unrelated records
    noise_a = NQUADS_STATE_A + """
<urn:rec:unrelated:1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Requirement> .
<urn:rec:unrelated:1> <https://moosedev.org/ontology/hasTitle> "Unrelated requirement" .
<urn:rec:unrelated:1> <https://moosedev.org/ontology/hasLifecycleStatus> "accepted" ."""

    noise_b = NQUADS_STATE_B + """
<urn:rec:unrelated:1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Requirement> .
<urn:rec:unrelated:1> <https://moosedev.org/ontology/hasTitle> "Unrelated requirement" .
<urn:rec:unrelated:1> <https://moosedev.org/ontology/hasLifecycleStatus> "accepted" ."""

    state_noise_a = adapter.parse_nquads(noise_a, revision="na")
    state_noise_b = adapter.parse_nquads(noise_b, revision="nb")

    noisy_impacts = find_impacts(diff_states(state_noise_a, state_noise_b), state_noise_a, state_noise_b)

    assert len(base_impacts) == len(noisy_impacts)
    assert base_impacts[0].target_record_id == noisy_impacts[0].target_record_id
    assert base_impacts[0].effect == noisy_impacts[0].effect
