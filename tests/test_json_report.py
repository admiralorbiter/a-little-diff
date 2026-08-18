import json
from pathlib import Path
from typer.testing import CliRunner

from alittlediff.cli import app
from alittlediff.domain import EpistemicRecord, EpistemicChange
from alittlediff.report import DiffReport, render_json_report

runner = CliRunner()


def test_render_json_report():
    rec_before = EpistemicRecord(id="urn:rec:1", kind="Constraint", title="Old")
    rec_after = EpistemicRecord(id="urn:rec:2", kind="Constraint", title="New")

    chg = EpistemicChange(
        change_id="chg-1",
        structural_type="superseded",
        before=rec_before,
        after=rec_after,
        judgment_source="deterministic",
    )

    report = DiffReport(
        base_revision="rev_a",
        head_revision="rev_b",
        source="moosedev",
        changes=[chg],
        impacts=[],
        warnings=["Test warning"],
    )

    assert report.change_count == 1
    assert report.impact_count == 0

    json_str = render_json_report(report)
    parsed = json.loads(json_str)

    assert parsed["base_revision"] == "rev_a"
    assert parsed["head_revision"] == "rev_b"
    assert len(parsed["changes"]) == 1
    assert parsed["changes"][0]["structural_type"] == "superseded"
    assert parsed["warnings"] == ["Test warning"]


def test_cli_diff_json_output(temp_git_repo: Path):
    result = runner.invoke(
        app,
        ["diff", "v0.1..HEAD", "--repo", str(temp_git_repo), "--json"],
    )
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert "changes" in parsed
    assert parsed["source"] == "moosedev"
    assert len(parsed["changes"]) >= 1
