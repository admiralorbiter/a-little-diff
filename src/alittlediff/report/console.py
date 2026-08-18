"""Rich console renderer for human-readable epistemic diff reports."""

from typing import Optional
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from alittlediff.domain.change import EpistemicChange
from alittlediff.domain.impact import Impact
from alittlediff.report.diff_report import DiffReport


def render_console_report(
    report: DiffReport,
    console: Optional[Console] = None,
    verbose: bool = False,
):
    """Render a DiffReport to the terminal with Rich styling.
    
    Args:
        report: The DiffReport instance to render.
        console: Optional Rich Console instance (defaults to standard console).
        verbose: Whether to show detailed evidence and metadata trees.
    """
    if console is None:
        console = Console(legacy_windows=False)

    base_short = report.base_revision[:8]
    head_short = report.head_revision[:8]

    # Header
    console.print()
    console.print("[bold cyan]════════════════════════════════════════════════════════════[/bold cyan]")
    console.print(f"[bold white] A LITTLE DIFF [/bold white] [dim]({escape(report.source)})[/dim]")
    console.print(f" [yellow]{base_short}[/yellow] ──► [green]{head_short}[/green]")
    console.print("[bold cyan]════════════════════════════════════════════════════════════[/bold cyan]\n")

    # Warnings
    if report.warnings:
        for w in report.warnings:
            console.print(f"[bold yellow]▲ Warning:[/bold yellow] {escape(w)}")
        console.print()

    # Summary metric lines
    supersession_count = sum(1 for c in report.changes if c.structural_type == "superseded")
    console.print(
        f"[bold white]{report.change_count}[/bold white] meaningful knowledge changes  •  "
        f"[bold yellow]{supersession_count}[/bold yellow] explicit supersessions  •  "
        f"[bold magenta]{report.impact_count}[/bold magenta] downstream items worth inspecting\n"
    )

    if report.change_count == 0 and report.impact_count == 0:
        console.print("[green]✓ No epistemic changes detected between revisions.[/green]\n")
        return

    # Section 1: Epistemic Changes
    for chg in report.changes:
        _render_change_card(chg, console, verbose=verbose)

    # Section 2: Downstream Impacts
    if report.impacts:
        high_med_impacts = [i for i in report.impacts if i.confidence in ("high", "medium")]
        low_impacts = [i for i in report.impacts if i.confidence == "low"]

        if high_med_impacts or low_impacts:
            console.print("\n[bold magenta]▼ DOWNSTREAM ITEMS WORTH RECONSIDERING[/bold magenta]\n")

        for imp in high_med_impacts:
            _render_impact_card(imp, console, verbose=verbose)

        if low_impacts:
            if verbose:
                for imp in low_impacts:
                    _render_impact_card(imp, console, verbose=verbose)
            else:
                # Group low-confidence targets by kind compactly
                grouped_targets: dict[str, list[str]] = {}
                for imp in low_impacts:
                    t = imp.target_record
                    kind = t.kind if t else "Record"
                    title = (t.title or imp.target_record_id) if t else imp.target_record_id
                    if title not in grouped_targets.setdefault(kind, []):
                        grouped_targets[kind].append(title)

                summary_lines = []
                for kind, titles in sorted(grouped_targets.items()):
                    items_str = ", ".join(escape(t) for t in titles[:5])
                    suffix = f" ... (+{len(titles) - 5} more)" if len(titles) > 5 else ""
                    summary_lines.append(f"[bold cyan]{kind} ({len(titles)}):[/bold cyan] {items_str}{suffix}")

                console.print(
                    Panel(
                        "\n".join(summary_lines),
                        title="[dim]BROAD CONTEXT & COMPONENT ASSOCIATIONS (LOW CONFIDENCE)[/dim]",
                        border_style="dim",
                        expand=False,
                    )
                )

    console.print()


def _render_change_card(chg: EpistemicChange, console: Console, verbose: bool = False):
    """Render an individual epistemic change card."""
    stype = chg.structural_type

    if stype == "superseded":
        title_text = "[bold yellow]BELIEF SUPERSEDED[/bold yellow]"
        content = []
        if chg.before:
            claim_text = escape(chg.before.claim or chg.before.title or "Unknown")
            content.append(f"[bold red]BEFORE:[/bold red] [dim]{escape(chg.before.kind)}[/dim]\n  {claim_text}")
        if chg.after:
            claim_text = escape(chg.after.claim or chg.after.title or "Unknown")
            content.append(f"[bold green]AFTER:[/bold green]  [dim]{escape(chg.after.kind)}[/dim]\n  {claim_text}")
        
        panel_body = "\n\n".join(content)
        console.print(Panel(panel_body, title=title_text, border_style="yellow", expand=False))

    elif stype == "status_changed":
        old_s = escape(str(chg.details.get("old_status", "unknown")))
        new_s = escape(str(chg.details.get("new_status", "unknown")))
        rec_title = escape(str(chg.before.title if chg.before and chg.before.title else (chg.after.title if chg.after and chg.after.title else "Record")))
        rec_kind = escape(str(chg.before.kind if chg.before else "Record"))
        console.print(f" [bold magenta]STATUS CHANGED[/bold magenta]  [dim]{rec_kind}[/dim] {rec_title} ([red]{old_s}[/red] ──► [green]{new_s}[/green])")

    elif stype == "added":
        rec = chg.after
        title = escape(str(rec.title or rec.claim if rec else "Unknown"))
        kind = escape(str(rec.kind if rec else "Record"))
        console.print(f" [bold green]+ ADDED {kind.upper()}[/bold green]  {title}")

    elif stype == "removed":
        rec = chg.before
        title = escape(str(rec.title or rec.claim if rec else "Unknown"))
        kind = escape(str(rec.kind if rec else "Record"))
        console.print(f" [bold red]- REMOVED {kind.upper()}[/bold red]  {title}")

    elif stype == "modified":
        rec = chg.after or chg.before
        title = escape(str(rec.title if rec and rec.title else "Record"))
        kind = escape(str(rec.kind if rec else "Record"))
        fields = [escape(str(f)) for f in chg.details.get("changed_fields", {}).keys()]
        console.print(f" [bold blue]MODIFIED {kind.upper()}[/bold blue]  {title} [dim](fields: {', '.join(fields)})[/dim]")

    elif stype in ("relation_added", "relation_removed"):
        rec = chg.after or chg.before
        rel_action = "+ RELATION ADDED" if stype == "relation_added" else "- RELATION REMOVED"
        title = escape(str(rec.title if rec and rec.title else "Record"))
        console.print(f" [dim cyan]{rel_action}[/dim cyan] on {title}")

    if verbose and chg.evidence:
        tree = Tree("[dim]Evidence[/dim]")
        for ev in chg.evidence:
            tree.add(f"[dim]{escape(ev.source_type)} | {escape(ev.path or '')} | {escape(ev.excerpt or '')}[/dim]")
        console.print(tree)


def _render_impact_card(imp: Impact, console: Console, verbose: bool = False):
    """Render a downstream impact consequence card."""
    target = imp.target_record
    target_kind = escape(target.kind if target else "Record")
    target_title = escape(target.title if target and target.title else imp.target_record_id)
    target_claim = escape(target.claim if target and target.claim else "")

    effect_display = escape(imp.effect.replace("_", " ").title())
    path_chain = " ──► ".join(f"({escape(r.predicate)})" for r in imp.path) if imp.path else "direct"

    body_lines = [
        f"[bold cyan]Target:[/bold cyan] {target_kind}: [bold white]{target_title}[/bold white]",
    ]
    if target_claim and target_claim != target_title:
        body_lines.append(f"[dim]Claim:[/dim] {target_claim}")
    
    body_lines.append(f"[bold yellow]Effect:[/bold yellow] {effect_display}")
    body_lines.append(f"[bold]Path:[/bold] {path_chain}")
    if imp.rationale:
        body_lines.append(f"[dim]Why:[/dim] {escape(imp.rationale)}")

    console.print(Panel("\n".join(body_lines), title=f"[bold magenta]RECONSIDER[/bold magenta] ({escape(imp.confidence.upper())} confidence)", border_style="magenta", expand=False))
