from pathlib import Path
import pytest
from typer.testing import CliRunner

from alittlediff.cli import app
from benchmarks.materialize import SENTINEL_FILENAME, materialize_scenario

runner = CliRunner()


def test_materialize_refuses_unsafe_target(tmp_path: Path):
    with pytest.raises(ValueError, match="Refusing to materialize into"):
        materialize_scenario("01_exact_noop", output_dir=Path(__file__).parent.parent)


def test_materialize_refuses_existing_dir_without_force(tmp_path: Path):
    target = tmp_path / "existing_dir"
    target.mkdir()
    (target / "dummy.txt").write_text("hello")

    with pytest.raises(FileExistsError, match="Use --force"):
        materialize_scenario("01_exact_noop", output_dir=target, force=False)


def test_materialize_refuses_foreign_dir_even_with_force(tmp_path: Path):
    target = tmp_path / "foreign_dir"
    target.mkdir()
    (target / "important_unrelated_file.txt").write_text("critical data")

    with pytest.raises(ValueError, match="does not contain '.alittlediff_materialized'"):
        materialize_scenario("01_exact_noop", output_dir=target, force=True)


def test_materialize_overwrites_with_force_when_sentinel_present(tmp_path: Path):
    target = tmp_path / "materialized_dir"
    target.mkdir()
    (target / SENTINEL_FILENAME).write_text("previous scenario")

    out_path = materialize_scenario("01_exact_noop", output_dir=target, force=True)
    assert out_path == target
    assert (target / ".moosedev" / "kg.nq").exists()
    assert (target / SENTINEL_FILENAME).exists()


def test_materialize_and_diff_cli(tmp_path: Path):
    target = tmp_path / "materialized_scenario_02"
    out_path = materialize_scenario("02_workflow_confirmation_refinement", output_dir=target)

    result = runner.invoke(app, ["diff", "state_a..state_b", "--repo", str(out_path)])
    assert result.exit_code == 0
    assert "A LITTLE DIFF" in result.stdout
    assert "RECORD SUPERSEDED" in result.stdout
    assert "Automatic session promotion" in result.stdout
    assert "isMotivatedBy" in result.stdout
