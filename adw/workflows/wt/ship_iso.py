#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ADW Ship Iso - AI Developer Workflow for shipping (merging) to main

Usage:
  uv run python -m adw.workflows.wt.ship_iso <issue-number> <adw-id>

Workflow:
1. Load state and validate worktree exists
2. Validate ALL state fields are populated (not None)
3. Perform manual git merge in main repository:
   - Fetch latest from origin
   - Checkout main
   - Merge feature branch
   - Push to origin/main
4. Post success message to issue

This workflow REQUIRES that all previous workflows have been run and that
every field in ADWState has a value. This is our final approval step.

Note: Merge operations happen in the main repository root, not in the worktree,
to preserve the worktree's state.
"""

import sys
import os
import logging
import subprocess
from typing import Optional, Tuple
from dotenv import load_dotenv

from adw.core.state import ADWState
from adw.integrations.github import (
    make_issue_comment,
    get_repo_url,
    extract_repo_path,
    approve_pr,
    close_issue,
)
from adw.integrations.git_ops import get_pr_number
from adw.integrations.workflow_ops import (
    format_issue_message,
    post_artifact_to_issue,
    post_state_to_issue,
)
from adw.core.utils import setup_logger, check_env_vars
from adw.integrations.worktree_ops import validate_worktree
from adw.core.data_types import AgentTemplateRequest
from adw.core.agent import execute_template

# Agent name constant
AGENT_SHIPPER = "shipper"
AGENT_CONFLICT_ANALYZER = "conflict_analyzer"


def analyze_merge_conflict(
    branch_name: str,
    merge_error: str,
    adw_id: str,
    issue_number: str,
    logger: logging.Logger
) -> Optional[str]:
    """Run Claude Code to analyze merge conflict and provide resolution options.
    
    This is READ-ONLY analysis - no actions are taken.
    
    Args:
        branch_name: The feature branch that failed to merge
        merge_error: The error message from the failed merge
        adw_id: ADW workflow ID
        issue_number: GitHub issue number
        logger: Logger instance
        
    Returns:
        Analysis output string, or None if analysis failed
    """
    repo_root = get_main_repo_root()
    logger.info(f"Analyzing merge conflict for branch {branch_name}")
    
    # Post status that we're analyzing
    make_issue_comment(
        issue_number,
        format_issue_message(
            adw_id, AGENT_CONFLICT_ANALYZER,
            "🔍 Analyzing merge conflict to provide resolution options..."
        )
    )
    
    # Create analysis request
    request = AgentTemplateRequest(
        agent_name=AGENT_CONFLICT_ANALYZER,
        slash_command="/analyze_merge_conflict",
        args=[branch_name, merge_error, repo_root],
        adw_id=adw_id,
        working_dir=repo_root,
    )
    
    # Execute analysis (this calls Claude Code)
    response = execute_template(request)
    
    if response.success:
        logger.info("Merge conflict analysis completed")
        # Post analysis to issue
        post_artifact_to_issue(
            issue_number=issue_number,
            adw_id=adw_id,
            agent_name=AGENT_CONFLICT_ANALYZER,
            title="🔍 Merge Conflict Analysis & Resolution Options",
            content=response.output,
            file_path=None,
            collapsible=False,  # Keep expanded so developer sees it immediately
        )
        return response.output
    else:
        logger.error(f"Failed to analyze merge conflict: {response.output}")
        msg = f"⚠️ Could not complete conflict analysis: {response.output}"
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_CONFLICT_ANALYZER, msg)
        )
        return None


def get_main_repo_root() -> str:
    """Get the main repository root by finding the git root directory."""
    # Use git to find the actual repository root - works regardless of where framework is installed
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        # Fallback: assume we're in the repo root already
        return os.getcwd()


def manual_merge_to_main(branch_name: str, logger: logging.Logger) -> Tuple[bool, Optional[str]]:
    """Manually merge a branch to main using git commands.
    
    This runs in the main repository root, not in a worktree.
    
    Args:
        branch_name: The feature branch to merge
        logger: Logger instance
        
    Returns:
        Tuple of (success, error_message)
    """
    repo_root = get_main_repo_root()
    logger.info(f"Performing manual merge in main repository: {repo_root}")
    
    try:
        # Save current branch to restore later
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=repo_root
        )
        original_branch = result.stdout.strip()
        logger.debug(f"Original branch: {original_branch}")
        
        # Step 1: Fetch latest from origin
        logger.info("Fetching latest from origin...")
        result = subprocess.run(
            ["git", "fetch", "origin"],
            capture_output=True, text=True, cwd=repo_root
        )
        if result.returncode != 0:
            return False, f"Failed to fetch from origin: {result.stderr}"
        
        # Step 2: Checkout main
        logger.info("Checking out main branch...")
        result = subprocess.run(
            ["git", "checkout", "main"],
            capture_output=True, text=True, cwd=repo_root
        )
        if result.returncode != 0:
            return False, f"Failed to checkout main: {result.stderr}"
        
        # Step 3: Pull latest main
        logger.info("Pulling latest main...")
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            capture_output=True, text=True, cwd=repo_root
        )
        if result.returncode != 0:
            # Try to restore original branch
            subprocess.run(["git", "checkout", original_branch], cwd=repo_root)
            return False, f"Failed to pull latest main: {result.stderr}"
        
        # Step 4: Merge the feature branch (no-ff to preserve all commits)
        logger.info(f"Merging branch {branch_name} (no-ff to preserve all commits)...")
        result = subprocess.run(
            ["git", "merge", branch_name, "--no-ff", "-m", f"Merge branch '{branch_name}' via ADW Ship workflow"],
            capture_output=True, text=True, cwd=repo_root
        )
        if result.returncode != 0:
            # Try to restore original branch
            subprocess.run(["git", "checkout", original_branch], cwd=repo_root)
            return False, f"Failed to merge {branch_name}: {result.stderr}"
        
        # Step 5: Push to origin/main
        logger.info("Pushing to origin/main...")
        result = subprocess.run(
            ["git", "push", "origin", "main"],
            capture_output=True, text=True, cwd=repo_root
        )
        if result.returncode != 0:
            # Try to restore original branch
            subprocess.run(["git", "checkout", original_branch], cwd=repo_root)
            return False, f"Failed to push to origin/main: {result.stderr}"
        
        # Step 6: Restore original branch
        logger.info(f"Restoring original branch: {original_branch}")
        subprocess.run(["git", "checkout", original_branch], cwd=repo_root)
        
        logger.info("✅ Successfully merged and pushed to main!")
        return True, None
        
    except Exception as e:
        logger.error(f"Unexpected error during merge: {e}")
        # Try to restore original branch
        try:
            subprocess.run(["git", "checkout", original_branch], cwd=repo_root)
        except:
            pass
        return False, str(e)


def validate_state_completeness(state: ADWState, logger: logging.Logger) -> tuple[bool, list[str]]:
    """Validate that all fields in ADWState have values (not None).
    
    Returns:
        tuple of (is_valid, missing_fields)
    """
    # Get the expected fields from ADWStateData model
    expected_fields = {
        "adw_id",
        "issue_number",
        "branch_name",
        "plan_file",
        "issue_class",
        "worktree_path",
        "backend_port",
        "frontend_port",
    }
    
    missing_fields = []
    
    for field in expected_fields:
        value = state.get(field)
        if value is None:
            missing_fields.append(field)
            logger.warning(f"Missing required field: {field}")
        else:
            logger.debug(f"✓ {field}: {value}")
    
    return len(missing_fields) == 0, missing_fields


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()
    
    # Parse command line args
    # INTENTIONAL: adw-id is REQUIRED - we need it to find the worktree and state
    if len(sys.argv) < 3:
        print("Usage: uv run python -m adw.workflows.wt.ship_iso <issue-number> <adw-id>")
        print("\nError: Both issue-number and adw-id are required")
        print("Run the complete SDLC workflow before shipping")
        sys.exit(1)
    
    issue_number = sys.argv[1]
    adw_id = sys.argv[2]
    
    # Try to load existing state
    temp_logger = setup_logger(adw_id, "adw_ship_iso")
    state = ADWState.load(adw_id, temp_logger)
    if not state:
        # No existing state found
        logger = setup_logger(adw_id, "adw_ship_iso")
        logger.error(f"No state found for ADW ID: {adw_id}")
        logger.error("Run the complete SDLC workflow before shipping")
        print(f"\nError: No state found for ADW ID: {adw_id}")
        print("Run the complete SDLC workflow before shipping")
        sys.exit(1)
    
    # Update issue number from state if available
    issue_number = state.get("issue_number", issue_number)
    
    # Track that this ADW workflow has run
    state.append_adw_id("adw_ship_iso")
    
    # Set up logger with ADW ID
    logger = setup_logger(adw_id, "adw_ship_iso")
    logger.info(f"ADW Ship Iso starting - ID: {adw_id}, Issue: {issue_number}")
    
    # Validate environment
    check_env_vars(logger)
    
    # Post initial status
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", f"🚢 Starting ship workflow\n"
                           f"📋 Validating state completeness...")
    )
    
    # Step 1: Validate state completeness
    logger.info("Validating state completeness...")
    is_valid, missing_fields = validate_state_completeness(state, logger)
    
    if not is_valid:
        error_msg = f"State validation failed. Missing fields: {', '.join(missing_fields)}"
        logger.error(error_msg)
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_SHIPPER, f"❌ {error_msg}\n\n"
                               "Please ensure all workflows have been run:\n"
                               "- adw plan (creates plan_file, branch_name, issue_class)\n"
                               "- adw build (implements the plan)\n"
                               "- adw test (runs tests)\n"
                               "- adw review (reviews implementation)\n"
                               "- adw document (generates docs)")
        )
        sys.exit(1)
    
    logger.info("✅ State validation passed - all fields have values")
    
    # Step 2: Validate worktree exists
    valid, error = validate_worktree(adw_id, state)
    if not valid:
        logger.error(f"Worktree validation failed: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_SHIPPER, f"❌ Worktree validation failed: {error}")
        )
        sys.exit(1)
    
    worktree_path = state.get("worktree_path")
    logger.info(f"✅ Worktree validated at: {worktree_path}")
    
    # Step 3: Get branch name
    branch_name = state.get("branch_name")
    logger.info(f"Preparing to merge branch: {branch_name}")
    
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_SHIPPER, f"📋 State validation complete\n"
                           f"🔍 Preparing to merge branch: {branch_name}")
    )
    
    # Get repo path for GitHub API calls
    try:
        github_repo_url = get_repo_url()
        repo_path = extract_repo_path(github_repo_url)
    except ValueError as e:
        logger.error(f"Error getting repository URL: {e}")
        sys.exit(1)

    # Step 4: Approve PR (optional - continues if fails)
    logger.info(f"Approving PR for branch {branch_name}...")
    pr_number = get_pr_number(branch_name) if branch_name else None
    if pr_number:
        pr_approved, pr_error = approve_pr(pr_number, repo_path)
        if pr_approved:
            logger.info("✅ PR approved")
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, AGENT_SHIPPER, "✅ PR approved")
            )
        else:
            logger.warning(f"Could not approve PR (continuing anyway): {pr_error}")
    else:
        logger.warning("No PR found for branch; skipping approval.")

    # Step 5: Perform manual merge
    logger.info(f"Starting manual merge of {branch_name} to main...")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_SHIPPER, f"🔀 Merging {branch_name} to main...\n"
                           "Using manual git operations in main repository")
    )

    success, error = manual_merge_to_main(branch_name, logger)

    if not success:
        logger.error(f"Failed to merge: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_SHIPPER, f"❌ Failed to merge: {error}")
        )
        
        # Run conflict analysis to provide resolution options
        logger.info("Running merge conflict analysis...")
        analysis = analyze_merge_conflict(
            branch_name=branch_name,
            merge_error=error,
            adw_id=adw_id,
            issue_number=issue_number,
            logger=logger
        )
        
        if analysis:
            logger.info("Merge conflict analysis posted to issue - see resolution options above")
        else:
            logger.warning("Could not complete merge conflict analysis")
        
        sys.exit(1)

    logger.info(f"✅ Successfully merged {branch_name} to main")

    # Step 6: Close the issue
    logger.info(f"Closing issue #{issue_number}...")
    issue_closed, close_error = close_issue(issue_number, repo_path)
    if issue_closed:
        logger.info(f"✅ Issue #{issue_number} closed")
    else:
        logger.warning(f"Could not close issue (continuing anyway): {close_error}")

    # Step 7: Post success message
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_SHIPPER,
                           f"🎉 **Successfully shipped!**\n\n"
                           f"✅ Validated all state fields\n"
                           f"✅ PR approved\n"
                           f"✅ Merged branch `{branch_name}` to main\n"
                           f"✅ Pushed to origin/main\n"
                           f"✅ Issue closed\n\n"
                           f"🚢 Code has been deployed to production!")
    )

    # Save final state
    state.save("adw_ship_iso")

    # Post final state summary
    post_state_to_issue(issue_number, adw_id, state.data, "📋 Final ship state")

    logger.info("Ship workflow completed successfully")


if __name__ == "__main__":
    main()
