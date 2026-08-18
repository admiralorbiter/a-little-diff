from typing import Optional
from pathlib import Path
import typer
from rich.console import Console

from alittlediff import __version__
from alittlediff.adapters.moosedev import MOOSEDevAdapter
from alittlediff.diff.structural import diff_states
from alittlediff.git.exceptions import GitError
from alittlediff.git.refs import parse_revision_range
from alittlediff.impact.traversal import find_impacts
from alittlediff.report.diff_report import DiffReport
from alittlediff.report.json_report import render_json_report
from alittlediff.report.console import render_console_report

app = typer.Typer(
    name="alittlediff",
    help="A Little Diff — An epistemic diff tool for comparing project understanding across Git revisions.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()
err_console = Console(stderr=True)


def version_callback(value: bool):
    if value:
        console.print(f"[bold cyan]alittlediff[/bold cyan] version [green]{__version__}[/green]")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show application version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
):
    """A Little Diff CLI entry point."""
    pass


@app.command()
def diff(
    revision_range: str = typer.Argument(
        ...,
        help="Revision range to compare in format <base>..<head> (e.g. HEAD~1..HEAD or main..feat-branch).",
    ),
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        "-r",
        help="Path to the Git repository.",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output raw JSON diff report.",
    ),
    no_model: bool = typer.Option(
        True,
        "--no-model",
        help="Disable LLM-based semantic classification and explanations (default in V0).",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Enable detailed diagnostic logging.",
    ),
):
    """Compute an epistemic diff between two project revisions."""
    try:
        base_sha, head_sha = parse_revision_range(repo, revision_range)
    except (ValueError, GitError) as exc:
        err_console.print(f"[bold red]Error resolving revision range:[/bold red] {exc}")
        raise typer.Exit(code=1)

    adapter = MOOSEDevAdapter()

    if not adapter.can_load(repo, base_sha):
        err_console.print(f"[bold red]Cannot compute epistemic diff:[/bold red] base revision {base_sha[:8]} has no MOOSEDev snapshot.")
        raise typer.Exit(code=1)

    if not adapter.can_load(repo, head_sha):
        err_console.print(f"[bold red]Cannot compute epistemic diff:[/bold red] head revision {head_sha[:8]} has no MOOSEDev snapshot.")
        raise typer.Exit(code=1)

    base_state = adapter.load_state(repo, base_sha)
    head_state = adapter.load_state(repo, head_sha)

    # Compute diff and downstream impacts
    changes = diff_states(base_state, head_state)
    impacts = find_impacts(changes, base_state, head_state)

    report = DiffReport(
        base_revision=base_sha,
        head_revision=head_sha,
        source="moosedev",
        changes=changes,
        impacts=impacts,
        warnings=[],
    )

    if json_output:
        print(render_json_report(report))
        return

    # Rich human-readable console report
    render_console_report(report, console=console, verbose=verbose)


if __name__ == "__main__":
    app()
