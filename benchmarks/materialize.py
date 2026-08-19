#!/usr/bin/env python3
"""Materialize a benchmark scenario into a live Git repository on disk.

Translates an alittlediff-bench JSON manifest into a concrete Git repository
with two commits tagged 'state_a' and 'state_b', allowing manual inspection,
CLI testing, and prospective development trials.

Usage:
    python -m benchmarks.materialize 02_workflow_confirmation_refinement
    python -m benchmarks.materialize benchmarks/manifests/02_workflow_confirmation_refinement.json --output-dir /tmp/my-repo
"""

import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

from benchmarks.schema import BenchmarkManifest

SENTINEL_FILENAME = ".alittlediff_materialized"


def _validate_safe_path(target_path: Path) -> None:
    """Ensure we never write or delete dangerous system paths."""
    resolved = target_path.resolve()
    # Refuse root or drive root
    if resolved == resolved.parent:
        raise ValueError(f"Refusing to materialize into filesystem root: {resolved}")
    # Refuse user home directory
    if resolved == Path.home().resolve():
        raise ValueError(f"Refusing to materialize directly into home directory: {resolved}")
    # Refuse repo root (directory containing pyproject.toml)
    repo_root = Path(__file__).resolve().parent.parent
    if resolved == repo_root:
        raise ValueError(f"Refusing to materialize into A Little Diff repository root: {resolved}")


def _is_safe_to_overwrite(target_path: Path) -> bool:
    """Check if an existing directory is safe to overwrite under --force."""
    if not target_path.exists():
        return True
    if not any(target_path.iterdir()):
        return True
    return (target_path / SENTINEL_FILENAME).is_file()


def materialize_scenario(
    scenario_id_or_path: str,
    output_dir: Path | str | None = None,
    force: bool = False,
) -> Path:
    """Materialize a benchmark scenario manifest into a Git repository."""
    p = Path(scenario_id_or_path)
    if not p.exists():
        # Try finding in benchmarks/manifests/
        manifests_dir = Path(__file__).parent / "manifests"
        p = manifests_dir / f"{scenario_id_or_path}.json"
        if not p.exists():
            raise FileNotFoundError(f"Benchmark scenario not found: {scenario_id_or_path}")

    with open(p, "r", encoding="utf-8") as f:
        manifest = BenchmarkManifest.model_validate_json(f.read())

    if output_dir is None:
        temp_parent = Path(tempfile.gettempdir()) / "alittlediff_materialized"
        temp_parent.mkdir(parents=True, exist_ok=True)
        target_dir = temp_parent / manifest.id
    else:
        target_dir = Path(output_dir)

    _validate_safe_path(target_dir)

    if target_dir.exists() and any(target_dir.iterdir()):
        if not force:
            raise FileExistsError(f"Target directory {target_dir} exists and is not empty. Use --force to overwrite.")
        if not _is_safe_to_overwrite(target_dir):
            raise ValueError(
                f"Refusing to force-overwrite {target_dir}: directory does not contain '{SENTINEL_FILENAME}'. "
                f"Please provide an empty directory or a previously materialized repository."
            )
        shutil.rmtree(target_dir)

    target_dir.mkdir(parents=True, exist_ok=True)

    def run_git(*args: str):
        subprocess.run(["git", *args], cwd=str(target_dir), capture_output=True, text=True, check=True)

    # Initialize repository
    run_git("init", "-b", "main")
    run_git("config", "user.name", "Benchmark Materializer")
    run_git("config", "user.email", "bench@alittlediff.local")

    # Write sentinel file
    (target_dir / SENTINEL_FILENAME).write_text(f"Scenario: {manifest.id}\nName: {manifest.name}\n", encoding="utf-8")

    # State A
    moose_dir = target_dir / ".moosedev"
    moose_dir.mkdir(parents=True, exist_ok=True)
    (moose_dir / "kg.nq").write_text(manifest.state_a_nquads, encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "--allow-empty", "-m", f"State A: {manifest.name}")
    run_git("tag", "state_a")

    # State B
    (moose_dir / "kg.nq").write_text(manifest.state_b_nquads, encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "--allow-empty", "-m", f"State B: {manifest.name}")
    run_git("tag", "state_b")

    return target_dir


def main():
    parser = argparse.ArgumentParser(description="Materialize a benchmark scenario into a live Git repository.")
    parser.add_argument("scenario", help="Scenario ID (e.g. 02_workflow_confirmation_refinement) or manifest path")
    parser.add_argument("--output-dir", "-o", help="Target directory for the materialized repository (defaults to tempdir)")
    parser.add_argument("--force", "-f", action="store_true", help="Overwrite existing non-empty output directory")
    args = parser.parse_args()

    try:
        out_path = materialize_scenario(args.scenario, output_dir=args.output_dir, force=args.force)
        print(f"✅ Materialized scenario '{args.scenario}' to: {out_path}")
        print("\nTo test with A Little Diff CLI:")
        print(f"  alittlediff diff state_a..state_b --repo {out_path}")
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
