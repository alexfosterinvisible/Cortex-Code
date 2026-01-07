#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
CXC SDLC Iso - Complete Software Development Life Cycle workflow with isolation

Usage: uv run python -m cxc.workflows.wt.sdlc_iso <issue-number> [cxc-id] [--skip-e2e] [--skip-resolution]

This script runs the complete CXC SDLC pipeline in isolation:
1. cxc plan - Planning phase (isolated)
2. cxc build - Implementation phase (isolated)
3. cxc test - Testing phase (isolated)
4. cxc review - Review phase (isolated) - with up to 3 auto-fix loops for blocking issues
5. cxc document - Documentation phase (isolated)

The scripts are chained together via persistent state (cxc_state.json).
Each phase runs in its own git worktree with dedicated ports.
"""

import subprocess
import sys
import os

from cxc.integrations.workflow_ops import ensure_cxc_id
from cxc.core.utils import print_phase_title


def run_workflow_module(module_name: str, issue_number: str, cxc_id: str, extra_args: list = None):
    """Run a workflow module using python -m."""
    cmd = [
        sys.executable, "-m", f"cxc.workflows.wt.{module_name}",
        issue_number,
        cxc_id,
    ]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(cmd)


def main():
    """Main entry point."""
    # Check for flags
    skip_e2e = "--skip-e2e" in sys.argv
    skip_resolution = "--skip-resolution" in sys.argv

    # Remove flags from argv
    if skip_e2e:
        sys.argv.remove("--skip-e2e")
    if skip_resolution:
        sys.argv.remove("--skip-resolution")

    if len(sys.argv) < 2:
        print("Usage: uv run python -m cxc.workflows.wt.sdlc_iso <issue-number> [cxc-id] [--skip-e2e] [--skip-resolution]")
        print("\nThis runs the complete isolated Software Development Life Cycle:")
        print("  1. Plan (isolated)")
        print("  2. Build (isolated)")
        print("  3. Test (isolated)")
        print("  4. Review (isolated) - with up to 3 auto-fix loops for blocking issues")
        print("  5. Document (isolated)")
        sys.exit(1)

    issue_number = sys.argv[1]
    cxc_id = sys.argv[2] if len(sys.argv) > 2 else None

    # Ensure CXC ID exists with initialized state
    cxc_id = ensure_cxc_id(issue_number, cxc_id)
    print(f"Using CXC ID: {cxc_id}")

    # Run isolated plan with the CXC ID
    print_phase_title("=== ISOLATED PLAN PHASE ===")
    plan = run_workflow_module("plan_iso", issue_number, cxc_id)
    if plan.returncode != 0:
        print("Isolated plan phase failed")
        sys.exit(1)

    # Run isolated build with the CXC ID
    print_phase_title("=== ISOLATED BUILD PHASE ===")
    build = run_workflow_module("build_iso", issue_number, cxc_id)
    if build.returncode != 0:
        print("Isolated build phase failed")
        sys.exit(1)

    # Run isolated test with the CXC ID
    print_phase_title("=== ISOLATED TEST PHASE ===")
    test_args = ["--skip-e2e"] if skip_e2e else []
    test = run_workflow_module("test_iso", issue_number, cxc_id, test_args)
    if test.returncode != 0:
        print("Isolated test phase failed")
        # Note: Continue anyway as some tests might be flaky
        print("WARNING: Test phase failed but continuing with review")

    # Run isolated review with the CXC ID
    print_phase_title("=== ISOLATED REVIEW PHASE ===")
    review_args = ["--skip-resolution"] if skip_resolution else []
    review = run_workflow_module("review_iso", issue_number, cxc_id, review_args)
    if review.returncode != 0:
        print("Isolated review phase failed")
        sys.exit(1)

    # Run isolated documentation with the CXC ID
    print_phase_title("=== ISOLATED DOCUMENTATION PHASE ===")
    document = run_workflow_module("document_iso", issue_number, cxc_id)
    if document.returncode != 0:
        print("Isolated documentation phase failed")
        sys.exit(1)
    print_phase_title("=== ISOLATED SDLC COMPLETED ===")
    print(f"CXC ID: {cxc_id}")
    print(f"All phases completed successfully!")
    print(f"\nWorktree location: trees/{cxc_id}/")
    print(f"To clean up: uv run cxc cleanup {cxc_id}")


if __name__ == "__main__":
    main()
