#!/usr/bin/env python3
"""Benchmark Scenario Materializer.

Materializes any canonical alittlediff-bench manifest into a standalone,
reproducible Git repository for live interactive inspection and evaluation.

Usage:
    python benchmarks/materialize.py 02_workflow_confirmation_refinement
    python benchmarks/materialize.py 02_workflow_confirmation_refinement --output-dir ./demo-repo --force
"""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def _validate_safe_path(target_path: Path):
    """Refuse dangerous target directories to prevent accidental data loss."""
    resolved = target_path.resolve()
    
    # Disallow root directories
    if resolved == resolved.parent:
        raise ValueError(f"Refusing to materialize into filesystem root: {resolved}")

    # Disallow user home directory
    home = Path.home().resolve()
    if resolved == home:
        raise ValueError(f"Refusing to materialize directly into user home directory: {resolved}")

    # Disallow repository root
    repo_root = Path(__file__).parent.parent.resolve()
    if resolved == repo_root:
        raise ValueError(f"Refusing to materialize into the a-little-diff repository root: {resolved}")


def materialize_scenario(
    manifest_input: str,
    output_dir: Path | None = None,
    force: bool = False,
) -> Path:
    """Materialize a benchmark scenario into a git repository."""
    # Resolve manifest path
    manifest_path = Path(manifest_input)
    if not manifest_path.is_file():
        # Check in standard manifests directory
        candidate = Path(__file__).parent / "manifests" / f"{manifest_input}.json"
        if candidate.is_file():
            manifest_path = candidate
        else:
            # Check with .json suffix
            candidate = Path(__file__).parent / "manifests" / manifest_input
            if candidate.is_file():
                manifest_path = candidate
            else:
                raise FileNotFoundError(f"Cannot find manifest for '{manifest_input}'")

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    scenario_id = data.get("id", manifest_path.stem)
    name = data.get("name", scenario_id)

    if output_dir is None:
        target_dir = Path(tempfile.gettempdir()) / "alittlediff-bench" / scenario_id
    else:
        target_dir = Path(output_dir)

    _validate_safe_path(target_dir)

    if target_dir.exists():
        if not force and any(target_dir.iterdir()):
            raise FileExistsError(
                f"Target directory '{target_dir}' already exists and is not empty. Use --force to overwrite."
            )
        shutil.rmtree(target_dir)

    target_dir.mkdir(parents=True, exist_ok=True)

    def run_git(*args: str):
        subprocess.run(["git", *args], cwd=str(target_dir), capture_output=True, text=True, check=True)

    # Initialize repository
    run_git("init", "-b", "main")
    run_git("config", "user.name", "Benchmark Materializer")
    run_git("config", "user.email", "bench@alittlediff.local")

    # State A
    moose_dir = target_dir / ".moosedev"
    moose_dir.mkdir(parents=True, exist_ok=True)
    (moose_dir / "kg.nq").write_text(data["state_a_nquads"], encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "--allow-empty", "-m", f"State A: {name}")
    run_git("tag", "state_a")

    # State B
    (moose_dir / "kg.nq").write_text(data["state_b_nquads"], encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "--allow-empty", "-m", f"State B: {name}")
    run_git("tag", "state_b")

    return target_dir


def main():
    parser = argparse.ArgumentParser(description="Materialize a benchmark scenario into a live Git repository.")
    parser.add_argument("scenario", help="Scenario ID (e.g. 02_workflow_confirmation_refinement) or manifest path")
    parser.add_argument("--output-dir", "-o", help="Target directory for the materialized repository (defaults to tempdir)")
    parser.add_argument("--force", "-f", action="store_true", help="Overwrite existing non-empty output directory")
    args = parser.parse_args()

    try:
        out_path = materialize_scenario(args.scenario, Path(args.output_dir) if args.output_dir else None, force=args.force)
        print(f"\nSuccessfully materialized scenario '{args.scenario}'!")
        print(f"Location: {out_path.resolve()}\n")
        print("Run epistemic diff with:")
        print(f"  alittlediff diff state_a..state_b --repo \"{out_path.resolve()}\"\n")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
