import io
from pathlib import Path
from rich.console import Console
from typer.testing import CliRunner

from alittlediff.cli import app
from alittlediff.domain import (
    EpistemicRecord,
    EpistemicChange,
    Evidence,
    Impact,
    Relation,
)
from alittlediff.report import DiffReport, render_console_report

runner = CliRunner()


def test_console_report_empty():
    out = io.StringIO()
    console = Console(file=out, force_terminal=True, width=100)
    report = DiffReport(
        base_revision="abcdef123456",
        head_revision="123456abcdef",
        source="moosedev",
        changes=[],
        impacts=[],
    )
    render_console_report(report, console=console)
    output = out.getvalue()
    assert "A LITTLE DIFF" in output
    assert "No epistemic changes detected" in output


def test_console_report_rich_rendering_with_impacts():
    out = io.StringIO()
    console = Console(file=out, force_terminal=True, width=100)

    ev = Evidence(source_type="git", path=".moosedev/kg.nq", excerpt="Change excerpt")
    rec_before = EpistemicRecord(id="urn:rec:c1", kind="Constraint", claim="Old constraint", evidence=[ev])
    rec_after = EpistemicRecord(id="urn:rec:c2", kind="Constraint", claim="New constraint", evidence=[ev])
    rec_target = EpistemicRecord(id="urn:rec:d1", kind="Decision", title="Attendance decision", claim="Manual screen")

    chg_sup = EpistemicChange(
        change_id="chg-1",
        structural_type="superseded",
        before=rec_before,
        after=rec_after,
        evidence=[ev],
        judgment_source="deterministic",
    )
    chg_add = EpistemicChange(
        change_id="chg-2",
        structural_type="added",
        after=rec_after,
        evidence=[ev],
        judgment_source="deterministic",
    )
    chg_rem = EpistemicChange(
        change_id="chg-3",
        structural_type="removed",
        before=rec_before,
        evidence=[ev],
        judgment_source="deterministic",
    )
    chg_status = EpistemicChange(
        change_id="chg-4",
        structural_type="status_changed",
        before=rec_before,
        after=rec_after,
        evidence=[ev],
        judgment_source="deterministic",
        details={"old_status": "active", "new_status": "retracted"},
    )
    chg_mod = EpistemicChange(
        change_id="chg-5",
        structural_type="modified",
        before=rec_before,
        after=rec_after,
        evidence=[ev],
        judgment_source="deterministic",
        details={"changed_fields": {"claim": ("old", "new")}},
    )
    chg_rel = EpistemicChange(
        change_id="chg-6",
        structural_type="relation_added",
        before=rec_before,
        after=rec_after,
        evidence=[ev],
        judgment_source="deterministic",
    )

    rel = Relation(predicate="isMotivatedBy", subject_id="urn:rec:d1", object_id="urn:rec:c1")
    impact = Impact(
        impact_id="imp-1",
        source_change_id="chg-1",
        target_record_id="urn:rec:d1",
        target_record=rec_target,
        effect="justification_may_have_changed",
        path=[rel],
        evidence=[ev],
        confidence="high",
        rationale="Motivating premise changed",
    )

    report = DiffReport(
        base_revision="abcdef1234567890",
        head_revision="1234567890abcdef",
        source="moosedev",
        changes=[chg_sup, chg_add, chg_rem, chg_status, chg_mod, chg_rel],
        impacts=[impact],
        warnings=["Test warning message"],
    )

    render_console_report(report, console=console, verbose=True)
    output = out.getvalue()

    assert "A LITTLE DIFF" in output
    assert "BELIEF SUPERSEDED" in output
    assert "BEFORE:" in output
    assert "AFTER:" in output
    assert "ADDED" in output
    assert "REMOVED" in output
    assert "STATUS CHANGED" in output
    assert "MODIFIED" in output
    assert "DOWNSTREAM ITEMS WORTH RECONSIDERING" in output
    assert "Attendance decision" in output
    assert "isMotivatedBy" in output


import subprocess
from tests.fixtures.moosedev_fixtures import NQUADS_STATE_A, NQUADS_STATE_B

def test_cli_diff_console_output_modified(temp_git_repo: Path):
    result = runner.invoke(
        app,
        ["diff", "v0.1..HEAD", "--repo", str(temp_git_repo)],
    )
    assert result.exit_code == 0
    assert "A LITTLE DIFF" in result.stdout
    assert "MODIFIED" in result.stdout


def test_cli_diff_console_output_supersession_and_impact(tmp_path: Path):
    repo = tmp_path / "moose_diff_repo"
    repo.mkdir()

    def run_git(*args: str):
        subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True, check=True)

    run_git("init", "-b", "main")
    run_git("config", "user.name", "Test")
    run_git("config", "user.email", "test@test.com")

    moose_dir = repo / ".moosedev"
    moose_dir.mkdir()
    (moose_dir / "kg.nq").write_text(NQUADS_STATE_A, encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "-m", "State A")
    run_git("tag", "state_a")

    (moose_dir / "kg.nq").write_text(NQUADS_STATE_B, encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "-m", "State B")

    result = runner.invoke(app, ["diff", "state_a..HEAD", "--repo", str(repo)])
    assert result.exit_code == 0
    assert "A LITTLE DIFF" in result.stdout
    assert "BELIEF SUPERSEDED" in result.stdout
    assert "RECONSIDER" in result.stdout
    assert "Manual attendance workflow" in result.stdout


def test_console_report_grouped_low_confidence_impacts_normal_mode():
    """Low-confidence concerns impacts should be collapsed into a compact grouped summary by default."""
    out = io.StringIO()
    console = Console(file=out, force_terminal=True, width=100)

    ev = Evidence(source_type="git", path=".moosedev/kg.nq")
    rec_c1 = EpistemicRecord(id="urn:rec:c1", kind="Constraint", claim="Changed constraint")
    chg = EpistemicChange(change_id="chg-1", structural_type="modified", before=rec_c1, after=rec_c1)

    tgt1 = EpistemicRecord(id="urn:comp:http", kind="SystemComponent", title="HTTP API")
    tgt2 = EpistemicRecord(id="urn:comp:mcp", kind="SystemComponent", title="MCP Server")
    tgt3 = EpistemicRecord(id="urn:code:fn1", kind="CodeEntity", title="parse_uri")

    imp1 = Impact(impact_id="i1", source_change_id="chg-1", target_record_id="urn:comp:http", target_record=tgt1, confidence="low", effect="inspect")
    imp2 = Impact(impact_id="i2", source_change_id="chg-1", target_record_id="urn:comp:mcp", target_record=tgt2, confidence="low", effect="inspect")
    imp3 = Impact(impact_id="i3", source_change_id="chg-1", target_record_id="urn:code:fn1", target_record=tgt3, confidence="low", effect="inspect")

    report = DiffReport(
        base_revision="abc",
        head_revision="def",
        source="moosedev",
        changes=[chg],
        impacts=[imp1, imp2, imp3],
    )

    render_console_report(report, console=console, verbose=False)
    output = out.getvalue()

    assert "BROAD CONTEXT & COMPONENT ASSOCIATIONS (LOW CONFIDENCE)" in output
    assert "SystemComponents (2):" in output
    assert "HTTP API" in output
    assert "MCP Server" in output
    assert "CodeEntitys (1):" in output
    assert "parse_uri" in output
    # Must NOT render individual high/medium RECONSIDER cards for low-confidence items
    assert "RECONSIDER (" not in output


def test_console_report_grouped_low_confidence_impacts_verbose_mode():
    """In verbose mode, low-confidence impacts render individual detailed cards."""
    out = io.StringIO()
    console = Console(file=out, force_terminal=True, width=100)

    rec_c1 = EpistemicRecord(id="urn:rec:c1", kind="Constraint", claim="Changed constraint")
    chg = EpistemicChange(change_id="chg-1", structural_type="modified", before=rec_c1, after=rec_c1)
    tgt1 = EpistemicRecord(id="urn:comp:http", kind="SystemComponent", title="HTTP API")
    imp1 = Impact(impact_id="i1", source_change_id="chg-1", target_record_id="urn:comp:http", target_record=tgt1, confidence="low", effect="inspect")

    report = DiffReport(
        base_revision="abc",
        head_revision="def",
        source="moosedev",
        changes=[chg],
        impacts=[imp1],
    )

    render_console_report(report, console=console, verbose=True)
    output = out.getvalue()

    # In verbose mode, full card is rendered
    assert "RECONSIDER" in output
    assert "LOW confidence" in output
    assert "HTTP API" in output
