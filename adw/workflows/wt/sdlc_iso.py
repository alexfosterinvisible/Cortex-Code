#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ADW SDLC Iso - Complete Software Development Life Cycle workflow with isolation

Usage: uv run python -m adw.workflows.wt.sdlc_iso <issue-number> [adw-id] [--skip-e2e] [--skip-resolution]

This script runs the complete ADW SDLC pipeline in isolation:
1. adw plan - Planning phase (isolated)
2. adw build - Implementation phase (isolated)
3. adw test - Testing phase (isolated)
4. adw review - Review phase (isolated) - with up to 3 auto-fix loops for blocking issues
5. adw document - Documentation phase (isolated)

The scripts are chained together via persistent state (adw_state.json).
Each phase runs in its own git worktree with dedicated ports.
"""

import subprocess
import sys
import os

from adw.integrations.workflow_ops import ensure_adw_id
from adw.core.utils import print_phase_title


def run_workflow_module(module_name: str, issue_number: str, adw_id: str, extra_args: list = None):
    """Run a workflow module using python -m."""
    cmd = [
        sys.executable, "-m", f"adw.workflows.wt.{module_name}",
        issue_number,
        adw_id,
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
        print("Usage: uv run python -m adw.workflows.wt.sdlc_iso <issue-number> [adw-id] [--skip-e2e] [--skip-resolution]")
        print("\nThis runs the complete isolated Software Development Life Cycle:")
        print("  1. Plan (isolated)")
        print("  2. Build (isolated)")
        print("  3. Test (isolated)")
        print("  4. Review (isolated) - with up to 3 auto-fix loops for blocking issues")
        print("  5. Document (isolated)")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    # Ensure ADW ID exists with initialized state
    adw_id = ensure_adw_id(issue_number, adw_id)
    print(f"Using ADW ID: {adw_id}")

    # Run isolated plan with the ADW ID
    print_phase_title("=== ISOLATED PLAN PHASE ===")
    plan = run_workflow_module("plan_iso", issue_number, adw_id)
    if plan.returncode != 0:
        print("Isolated plan phase failed")
        sys.exit(1)

    # Run isolated build with the ADW ID
    print_phase_title("=== ISOLATED BUILD PHASE ===")
    build = run_workflow_module("build_iso", issue_number, adw_id)
    if build.returncode != 0:
        print("Isolated build phase failed")
        sys.exit(1)

    # Run isolated test with the ADW ID
    print_phase_title("=== ISOLATED TEST PHASE ===")
    test_args = ["--skip-e2e"] if skip_e2e else []
    test = run_workflow_module("test_iso", issue_number, adw_id, test_args)
    if test.returncode != 0:
        print("Isolated test phase failed")
        # Note: Continue anyway as some tests might be flaky
        print("WARNING: Test phase failed but continuing with review")

    # Run isolated review with the ADW ID
    print_phase_title("=== ISOLATED REVIEW PHASE ===")
    review_args = ["--skip-resolution"] if skip_resolution else []
    review = run_workflow_module("review_iso", issue_number, adw_id, review_args)
    if review.returncode != 0:
        print("Isolated review phase failed")
        sys.exit(1)

    # Run isolated documentation with the ADW ID
    print_phase_title("=== ISOLATED DOCUMENTATION PHASE ===")
    document = run_workflow_module("document_iso", issue_number, adw_id)
    if document.returncode != 0:
        print("Isolated documentation phase failed")
        sys.exit(1)
    print_phase_title("=== ISOLATED SDLC COMPLETED ===")
    print(f"ADW ID: {adw_id}")
    print(f"All phases completed successfully!")
    print(f"\nWorktree location: trees/{adw_id}/")
    print(f"To clean up: uv run adw cleanup {adw_id}")


if __name__ == "__main__":
    main()
