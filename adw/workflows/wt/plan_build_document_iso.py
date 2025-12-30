#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ADW Plan Build Document Iso - Compositional workflow for isolated planning, building, and documentation

Usage: uv run python -m adw.workflows.wt.plan_build_document_iso <issue-number> [adw-id]

This script runs:
1. adw plan - Planning phase (isolated)
2. adw build - Implementation phase (isolated)
3. adw document - Documentation phase (isolated)

The scripts are chained together via persistent state (adw_state.json).
"""

import subprocess
import sys
from adw.integrations.workflow_ops import ensure_adw_id


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: uv run python -m adw.workflows.wt.plan_build_document_iso <issue-number> [adw-id]")
        print("\nThis runs the isolated plan, build, and document workflow:")
        print("  1. Plan (isolated)")
        print("  2. Build (isolated)")
        print("  3. Document (isolated)")
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
    print(f"\n=== ISOLATED PLAN PHASE ===")
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
    print(f"\n=== ISOLATED BUILD PHASE ===")
    print(f"Running: {' '.join(build_cmd)}")
    build = subprocess.run(build_cmd)
    if build.returncode != 0:
        print("Isolated build phase failed")
        sys.exit(1)

    # Run isolated documentation with the ADW ID
    document_cmd = [
        "uv",
        "run",
        "python",
        "-m",
        "adw.workflows.wt.document_iso",
        issue_number,
        adw_id,
    ]
    print(f"\n=== ISOLATED DOCUMENTATION PHASE ===")
    print(f"Running: {' '.join(document_cmd)}")
    document = subprocess.run(document_cmd)
    if document.returncode != 0:
        print("Isolated documentation phase failed")
        sys.exit(1)

    print(f"\n=== ISOLATED WORKFLOW COMPLETED ===")
    print(f"ADW ID: {adw_id}")
    print(f"All phases completed successfully!")


if __name__ == "__main__":
    main()
