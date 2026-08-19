#!/usr/bin/env python3
"""Unified Benchmark and Verification Runner for A Little Diff.

Executes test suites across profiles ('fast' and 'full'), collects execution metrics,
renders a terminal dashboard, and writes benchmark-results/latest.json and benchmark-results/latest.md.

Usage:
    python -m benchmarks.run
    python -m benchmarks.run --profile full
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import time

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


SUITE_DEFINITIONS = {
    "unit_and_contract": {
        "name": "Core Unit & MOOSEDev Contract Suite",
        "files": [
            "tests/test_cli.py",
            "tests/test_console_report.py",
            "tests/test_diff_structural.py",
            "tests/test_domain.py",
            "tests/test_edge_cases.py",
            "tests/test_git.py",
            "tests/test_impact_engine.py",
            "tests/test_json_report.py",
            "tests/test_moosedev_adapter.py",
            "tests/test_moosedev_contract.py",
        ],
        "profile": "fast",
    },
    "canonical_manifests": {
        "name": "Canonical Benchmark Manifests (Core Bench Oracles)",
        "files": ["tests/test_benchmark_manifests.py"],
        "profile": "fast",
    },
    "metamorphic_invariants": {
        "name": "Manifest-Driven Metamorphic Invariants",
        "files": ["tests/test_metamorphic_manifests.py", "tests/test_metamorphic.py"],
        "profile": "fast",
    },
    "materializer_cli": {
        "name": "Materializer & CLI Integration",
        "files": ["tests/test_materialize.py"],
        "profile": "fast",
    },
    "hypothesis_properties": {
        "name": "Hypothesis Property & Differential Evaluator Suite",
        "files": ["tests/test_properties.py"],
        "profile": "full",
    },
    "stateful_histories": {
        "name": "Stateful Epistemic Lifecycle History Simulation",
        "files": ["tests/test_stateful_history.py"],
        "profile": "full",
    },
}


def run_suite(files: list[str]) -> dict:
    """Run pytest on a list of test files and return detailed result metrics."""
    cmd = [sys.executable, "-m", "pytest", "-q", "--tb=short"] + files
    start_time = time.perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True)
    duration = time.perf_counter() - start_time

    output = proc.stdout + proc.stderr
    passed = proc.returncode == 0

    # Parse counts with regex from pytest summary line
    passed_count = 0
    failed_count = 0
    skipped_count = 0
    error_count = 0

    for line in output.splitlines():
        # Match lines like "57 passed, 2 failed, 1 skipped in 1.23s"
        m_pass = re.search(r"(\d+)\s+passed", line)
        if m_pass:
            passed_count = int(m_pass.group(1))

        m_fail = re.search(r"(\d+)\s+failed", line)
        if m_fail:
            failed_count = int(m_fail.group(1))

        m_skip = re.search(r"(\d+)\s+skipped", line)
        if m_skip:
            skipped_count = int(m_skip.group(1))

        m_err = re.search(r"(\d+)\s+error", line)
        if m_err:
            error_count = int(m_err.group(1))

    total_executed = passed_count + failed_count + error_count

    # Extract failure lines if any
    failures_summary = []
    if not passed:
        capture = False
        for line in output.splitlines():
            if "FAILURES" in line or "ERRORS" in line:
                capture = True
            if capture:
                failures_summary.append(line)

    return {
        "passed": passed,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "skipped_count": skipped_count,
        "error_count": error_count,
        "total_executed": total_executed,
        "duration_seconds": round(duration, 2),
        "return_code": proc.returncode,
        "raw_output": output if not passed else "",
        "failures_summary": "\n".join(failures_summary[:30]) if failures_summary else "",
    }


def main():
    parser = argparse.ArgumentParser(description="A Little Diff Verification and Benchmark Runner")
    parser.add_argument("--profile", choices=["fast", "full"], default="fast", help="Execution profile ('fast' or 'full')")
    args = parser.parse_args()

    console = Console()
    console.print(Panel(f"[bold cyan]A LITTLE DIFF VERIFICATION HARNESS[/bold cyan]\nProfile: [bold yellow]{args.profile.upper()}[/bold yellow]  •  Timestamp: {datetime.now(timezone.utc).isoformat()}", border_style="cyan"))

    results_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "profile": args.profile,
        "suites": {},
        "summary": {
            "total_suites": 0,
            "passed_suites": 0,
            "failed_suites": 0,
            "total_tests_passed": 0,
            "total_tests_failed": 0,
            "total_duration_seconds": 0.0,
            "status": "PASS",
        }
    }

    table = Table(title="Verification Suite Results", expand=True)
    table.add_column("Layer / Suite Name", style="cyan")
    table.add_column("Profile", justify="center")
    table.add_column("Passed", justify="right")
    table.add_column("Failed", justify="right")
    table.add_column("Duration", justify="right")
    table.add_column("Status", justify="center")

    total_duration = 0.0
    all_passed = True

    for suite_key, suite_info in SUITE_DEFINITIONS.items():
        if args.profile == "fast" and suite_info["profile"] == "full":
            table.add_row(suite_info["name"], "full", "-", "-", "-", "[dim]SKIPPED[/dim]")
            continue

        res = run_suite(suite_info["files"])
        total_duration += res["duration_seconds"]
        results_data["summary"]["total_suites"] += 1
        results_data["summary"]["total_tests_passed"] += res["passed_count"]
        results_data["summary"]["total_tests_failed"] += res["failed_count"] + res["error_count"]

        results_data["suites"][suite_key] = {
            "name": suite_info["name"],
            "profile": suite_info["profile"],
            "passed_count": res["passed_count"],
            "failed_count": res["failed_count"],
            "skipped_count": res["skipped_count"],
            "error_count": res["error_count"],
            "duration_seconds": res["duration_seconds"],
            "passed": res["passed"],
            "failures_summary": res["failures_summary"],
        }

        if res["passed"]:
            results_data["summary"]["passed_suites"] += 1
            status_text = "[bold green]PASS[/bold green]"
        else:
            all_passed = False
            results_data["summary"]["failed_suites"] += 1
            status_text = "[bold red]FAIL[/bold red]"

        table.add_row(
            suite_info["name"],
            suite_info["profile"],
            str(res["passed_count"]),
            str(res["failed_count"] + res["error_count"]),
            f"{res['duration_seconds']}s",
            status_text,
        )

    results_data["summary"]["total_duration_seconds"] = round(total_duration, 2)
    results_data["summary"]["status"] = "PASS" if all_passed else "FAIL"

    console.print(table)

    if not all_passed:
        console.print("\n[bold red]Suite Failure Diagnostics:[/bold red]")
        for s_key, s_data in results_data["suites"].items():
            if not s_data["passed"] and s_data["failures_summary"]:
                console.print(Panel(f"[bold]{s_data['name']}[/bold]\n\n{s_data['failures_summary']}", border_style="red"))

    summary_panel = (
        f"[bold]Total Tests Passed:[/bold] {results_data['summary']['total_tests_passed']}\n"
        f"[bold]Total Tests Failed:[/bold] {results_data['summary']['total_tests_failed']}\n"
        f"[bold]Suites Passing:[/bold] {results_data['summary']['passed_suites']}/{results_data['summary']['total_suites']}\n"
        f"[bold]Total Duration:[/bold] {results_data['summary']['total_duration_seconds']} seconds\n"
        f"[bold]Overall Status:[/bold] {'[bold green]VERIFIED READY[/bold green]' if all_passed else '[bold red]REVIEW REQUIRED[/bold red]'}"
    )
    console.print(Panel(summary_panel, border_style="green" if all_passed else "red"))

    # Persist results
    results_dir = Path("benchmark-results")
    results_dir.mkdir(exist_ok=True)

    json_path = results_dir / "latest.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2)

    md_lines = [
        f"# A Little Diff Verification Report",
        f"**Profile:** `{args.profile}`  ",
        f"**Timestamp:** `{results_data['timestamp']}`  ",
        f"**Overall Status:** **{results_data['summary']['status']}** ({results_data['summary']['total_tests_passed']} passed, {results_data['summary']['total_tests_failed']} failed in {results_data['summary']['total_duration_seconds']}s)  \n",
        "| Layer / Suite Name | Profile | Passed | Failed | Duration | Status |",
        "|---|---|---|---|---|---|",
    ]
    for s_key, s_data in results_data["suites"].items():
        st_icon = "✅ PASS" if s_data["passed"] else "❌ FAIL"
        md_lines.append(f"| {s_data['name']} | `{s_data['profile']}` | {s_data['passed_count']} | {s_data['failed_count']} | {s_data['duration_seconds']}s | {st_icon} |")

    md_path = results_dir / "latest.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    console.print(f"[dim]Persisted results to {json_path} and {md_path}[/dim]\n")
    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
