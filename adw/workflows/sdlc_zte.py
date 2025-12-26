#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ADW SDLC ZTE Iso - Zero Touch Execution: Complete SDLC with automatic shipping

Usage: uv run adw zte <issue-number> [adw-id] [--skip-e2e] [--skip-resolution]

This script runs the complete ADW SDLC pipeline with automatic shipping:
1. plan.py - Planning phase (isolated)
2. build.py - Implementation phase (isolated)
3. test.py - Testing phase (isolated)
4. review.py - Review phase (isolated)
5. document.py - Documentation phase (isolated)
6. ship.py - Ship phase (approve & merge PR)

ZTE = Zero Touch Execution: The entire workflow runs to completion without
human intervention, automatically shipping code to production if all phases pass.

The scripts are chained together via persistent state (adw_state.json).
Each phase runs on the same git worktree with dedicated ports.
"""

import subprocess
import sys

from adw.workflow_ops import ensure_adw_id
from adw.github import make_issue_comment


def run_workflow_module(module_name: str, issue_number: str, adw_id: str, extra_args: list = None):
    """Run a workflow module using python -m."""
    cmd = [
        sys.executable, "-m", f"adw.workflows.{module_name}",
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
        print("Usage: uv run adw zte <issue-number> [adw-id] [--skip-e2e] [--skip-resolution]")
        print("\nZero Touch Execution: Complete SDLC with automatic shipping")
        print("\nThis runs the complete isolated Software Development Life Cycle:")
        print("  1. Plan (isolated)")
        print("  2. Build (isolated)")
        print("  3. Test (isolated)")
        print("  4. Review (isolated)")
        print("  5. Document (isolated)")
        print("  6. Ship (approve & merge PR)")
        print("\nWARNING: This will automatically merge to main if all phases pass!")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    # Ensure ADW ID exists with initialized state
    adw_id = ensure_adw_id(issue_number, adw_id)
    print(f"Using ADW ID: {adw_id}")

    # Post initial ZTE message
    try:
        make_issue_comment(
            issue_number,
            f"{adw_id}_ops: **Starting Zero Touch Execution (ZTE)**\n\n"
            "This workflow will automatically:\n"
            "1. Plan the implementation\n"
            "2. Build the solution\n"
            "3. Test the code\n"
            "4. Review the implementation\n"
            "5. Generate documentation\n"
            "6. **Ship to production** (approve & merge PR)\n\n"
            "Code will be automatically merged if all phases pass!",
        )
    except Exception as e:
        print(f"Warning: Failed to post initial comment: {e}")

    # Run isolated plan with the ADW ID
    print(f"\n=== ISOLATED PLAN PHASE ===")
    plan = run_workflow_module("plan", issue_number, adw_id)
    if plan.returncode != 0:
        print("Isolated plan phase failed")
        sys.exit(1)

    # Run isolated build with the ADW ID
    print(f"\n=== ISOLATED BUILD PHASE ===")
    build = run_workflow_module("build", issue_number, adw_id)
    if build.returncode != 0:
        print("Isolated build phase failed")
        sys.exit(1)

    # Run isolated test with the ADW ID
    print(f"\n=== ISOLATED TEST PHASE ===")
    test_args = ["--skip-e2e"] if skip_e2e else []
    test = run_workflow_module("test", issue_number, adw_id, test_args)
    if test.returncode != 0:
        print("Isolated test phase failed")
        # For ZTE, we should stop if tests fail
        try:
            make_issue_comment(
                issue_number,
                f"{adw_id}_ops: **ZTE Aborted** - Test phase failed\n\n"
                "Automatic shipping cancelled due to test failures.\n"
                "Please fix the tests and run the workflow again.",
            )
        except:
            pass
        sys.exit(1)

    # Run isolated review with the ADW ID
    print(f"\n=== ISOLATED REVIEW PHASE ===")
    review_args = ["--skip-resolution"] if skip_resolution else []
    review = run_workflow_module("review", issue_number, adw_id, review_args)
    if review.returncode != 0:
        print("Isolated review phase failed")
        try:
            make_issue_comment(
                issue_number,
                f"{adw_id}_ops: **ZTE Aborted** - Review phase failed\n\n"
                "Automatic shipping cancelled due to review failures.\n"
                "Please address the review issues and run the workflow again.",
            )
        except:
            pass
        sys.exit(1)

    # Run isolated documentation with the ADW ID
    print(f"\n=== ISOLATED DOCUMENTATION PHASE ===")
    document = run_workflow_module("document", issue_number, adw_id)
    if document.returncode != 0:
        print("Isolated documentation phase failed")
        # Documentation failure shouldn't block shipping
        print("WARNING: Documentation phase failed but continuing with shipping")

    # Run isolated ship with the ADW ID
    print(f"\n=== ISOLATED SHIP PHASE (APPROVE & MERGE) ===")
    ship = run_workflow_module("ship", issue_number, adw_id)
    if ship.returncode != 0:
        print("Isolated ship phase failed")
        try:
            make_issue_comment(
                issue_number,
                f"{adw_id}_ops: **ZTE Failed** - Ship phase failed\n\n"
                "Could not automatically approve and merge the PR.\n"
                "Please check the ship logs and merge manually if needed.",
            )
        except:
            pass
        sys.exit(1)

    print(f"\n=== ZERO TOUCH EXECUTION COMPLETED ===")
    print(f"ADW ID: {adw_id}")
    print(f"All phases completed successfully!")
    print(f"Code has been shipped to production!")
    print(f"\nWorktree location: trees/{adw_id}/")
    print(f"To clean up: uv run adw cleanup {adw_id}")

    try:
        make_issue_comment(
            issue_number,
            f"{adw_id}_ops: **Zero Touch Execution Complete!**\n\n"
            "- Plan phase completed\n"
            "- Build phase completed\n"
            "- Test phase completed\n"
            "- Review phase completed\n"
            "- Documentation phase completed\n"
            "- Ship phase completed\n\n"
            "**Code has been automatically shipped to production!**",
        )
    except:
        pass


if __name__ == "__main__":
    main()
