from typer.testing import CliRunner
from alittlediff import __version__
from alittlediff.cli import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "A Little Diff" in result.stdout
    assert "Revision range to compare" in result.stdout or "diff" in result.stdout


def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "alittlediff" in result.stdout
    assert __version__ in result.stdout


from pathlib import Path

def test_cli_diff_subcommand(temp_git_repo: Path):
    result = runner.invoke(app, ["diff", "v0.1..HEAD", "--repo", str(temp_git_repo)])
    assert result.exit_code == 0
    assert "A LITTLE DIFF" in result.stdout
    assert "meaningful knowledge changes" in result.stdout


def test_cli_diff_missing_snapshot(tmp_path: Path):
    non_moose_repo = tmp_path / "plain_dir"
    non_moose_repo.mkdir()
    result = runner.invoke(app, ["diff", "v0.1..HEAD", "--repo", str(non_moose_repo)])
    assert result.exit_code == 1
