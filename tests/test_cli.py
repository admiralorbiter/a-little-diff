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


import subprocess

def test_cli_diff_missing_snapshot(tmp_path: Path):
    non_moose_repo = tmp_path / "plain_dir"
    non_moose_repo.mkdir()
    result = runner.invoke(app, ["diff", "v0.1..HEAD", "--repo", str(non_moose_repo)])
    assert result.exit_code == 1


def test_cli_diff_base_or_head_missing_snapshot(tmp_path: Path):
    repo = tmp_path / "asym_repo"
    repo.mkdir()

    def run_git(*args: str):
        subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True, check=True)

    run_git("init", "-b", "main")
    run_git("config", "user.name", "Test")
    run_git("config", "user.email", "test@test.com")
    (repo / "README.md").write_text("v1\n", encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "-m", "Commit 1 without snapshot")
    run_git("tag", "v1")

    moose_dir = repo / ".moosedev"
    moose_dir.mkdir()
    (moose_dir / "kg.nq").write_text("<urn:rec:1> <https://moosedev.org/ontology/hasTitle> \"T\" .\n", encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "-m", "Commit 2 with snapshot")

    # Base (v1) lacks snapshot
    result_base = runner.invoke(app, ["diff", "v1..HEAD", "--repo", str(repo)])
    assert result_base.exit_code == 1
    assert "base revision" in result_base.stderr or "Cannot compute" in result_base.stderr

    # Head (v1) lacks snapshot
    result_head = runner.invoke(app, ["diff", "HEAD..v1", "--repo", str(repo)])
    assert result_head.exit_code == 1
    assert "head revision" in result_head.stderr or "Cannot compute" in result_head.stderr
