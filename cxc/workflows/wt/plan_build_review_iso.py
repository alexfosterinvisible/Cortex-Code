#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
CXC Plan Build Review Iso - Compositional workflow for isolated planning, building, and reviewing

Usage: uv run python -m cxc.workflows.wt.plan_build_review_iso <issue-number> [cxc-id] [--skip-resolution]

This script runs:
1. cxc plan - Planning phase (isolated)
2. cxc build - Implementation phase (isolated)
3. cxc review - Review phase (isolated) - with up to 3 auto-fix loops for blocking issues

The scripts are chained together via persistent state (cxc_state.json).
"""

import subprocess
import sys
from cxc.integrations.workflow_ops import ensure_cxc_id
from cxc.core.utils import print_phase_title


def main():
    """Main entry point."""
    # Check for --skip-resolution flag
    skip_resolution = "--skip-resolution" in sys.argv
    if skip_resolution:
        sys.argv.remove("--skip-resolution")
    
    if len(sys.argv) < 2:
        print("Usage: uv run python -m cxc.workflows.wt.plan_build_review_iso <issue-number> [cxc-id] [--skip-resolution]")
        print("\nThis runs the isolated plan, build, and review workflow:")
        print("  1. Plan (isolated)")
        print("  2. Build (isolated)")
        print("  3. Review (isolated)")
        sys.exit(1)

    issue_number = sys.argv[1]
    cxc_id = sys.argv[2] if len(sys.argv) > 2 else None

    # Ensure CXC ID exists with initialized state
    cxc_id = ensure_cxc_id(issue_number, cxc_id)
    print(f"Using CXC ID: {cxc_id}")

    # Run isolated plan with the CXC ID
    plan_cmd = [
        "uv",
        "run",
        "python",
        "-m",
        "cxc.workflows.wt.plan_iso",
        issue_number,
        cxc_id,
    ]
print_phase_title("=== ISOLATED PLAN PHASE ===")
    print(f"Running: {' '.join(plan_cmd)}")
    plan = subprocess.run(plan_cmd)
    if plan.returncode != 0:
        print("Isolated plan phase failed")
        sys.exit(1)

    # Run isolated build with the CXC ID
    build_cmd = [
        "uv",
        "run",
        "python",
        "-m",
        "cxc.workflows.wt.build_iso",
        issue_number,
        cxc_id,
    ]
print_phase_title("=== ISOLATED BUILD PHASE ===")
    print(f"Running: {' '.join(build_cmd)}")
    build = subprocess.run(build_cmd)
    if build.returncode != 0:
        print("Isolated build phase failed")
        sys.exit(1)

    # Run isolated review with the CXC ID
    review_cmd = [
        "uv",
        "run",
        "python",
        "-m",
        "cxc.workflows.wt.review_iso",
        issue_number,
        cxc_id,
    ]
    if skip_resolution:
        review_cmd.append("--skip-resolution")
print_phase_title("=== ISOLATED REVIEW PHASE ===")
    print(f"Running: {' '.join(review_cmd)}")
    review = subprocess.run(review_cmd)
    if review.returncode != 0:
        print("Isolated review phase failed")
        sys.exit(1)
print_phase_title("=== ISOLATED WORKFLOW COMPLETED ===")
    print(f"CXC ID: {cxc_id}")
    print(f"All phases completed successfully!")


if __name__ == "__main__":
    main()
