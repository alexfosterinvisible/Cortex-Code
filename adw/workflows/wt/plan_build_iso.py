#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ADW Plan Build Iso - Compositional workflow for isolated planning and building

Usage: uv run python -m adw.workflows.wt.plan_build_iso <issue-number> [adw-id]

This script runs:
1. adw plan - Planning phase (isolated)
2. adw build - Implementation phase (isolated)

The scripts are chained together via persistent state (adw_state.json).
"""

import subprocess
import sys
from adw.integrations.workflow_ops import ensure_adw_id
from adw.core.utils import print_phase_title


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: uv run python -m adw.workflows.wt.plan_build_iso <issue-number> [adw-id]")
        print("\nThis runs the isolated plan and build workflow:")
        print("  1. Plan (isolated)")
        print("  2. Build (isolated)")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    # Ensure ADW ID exists with initialized state
    adw_id = ensure_adw_id(issue_number, adw_id)
    print(f"Using ADW ID: {adw_id}")

    # Run isolated plan with the ADW ID
    plan_cmd = [
        "uv",
        "run",
        "python",
        "-m",
        "adw.workflows.wt.plan_iso",
        issue_number,
        adw_id,
    ]
print_phase_title("=== ISOLATED PLAN PHASE ===")
    print(f"Running: {' '.join(plan_cmd)}")
    plan = subprocess.run(plan_cmd)
    if plan.returncode != 0:
        print("Isolated plan phase failed")
        sys.exit(1)

    # Run isolated build with the ADW ID
    build_cmd = [
        "uv",
        "run",
        "python",
        "-m",
        "adw.workflows.wt.build_iso",
        issue_number,
        adw_id,
    ]
print_phase_title("=== ISOLATED BUILD PHASE ===")
    print(f"Running: {' '.join(build_cmd)}")
    build = subprocess.run(build_cmd)
    if build.returncode != 0:
        print("Isolated build phase failed")
        sys.exit(1)
print_phase_title("=== ISOLATED WORKFLOW COMPLETED ===")
    print(f"ADW ID: {adw_id}")
    print(f"All phases completed successfully!")


if __name__ == "__main__":
    main()
