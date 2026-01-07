#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
CXC Build Iso - Cortex Code for agentic building in isolated worktrees

Usage:
  uv run python -m cxc.workflows.wt.build_iso <issue-number> <cxc-id>

Workflow:
1. Load state and validate worktree exists
2. Find existing plan (from state)
3. Implement the solution based on plan in worktree
4. Commit implementation in worktree
5. Push and update PR

This workflow REQUIRES that cxc plan or cxc patch has been run first
to create the worktree. It cannot create worktrees itself.
"""

import sys
import os
import logging
import json
import subprocess
from typing import Optional
from dotenv import load_dotenv

from cxc.core.state import CxcState
from cxc.integrations.git_ops import commit_changes, finalize_git_operations, get_current_branch
from cxc.integrations.github import fetch_issue, make_issue_comment, get_repo_url, extract_repo_path
from cxc.integrations.workflow_ops import (
    implement_plan,
    create_commit,
    format_issue_message,
    post_artifact_to_issue,
    post_state_to_issue,
    AGENT_IMPLEMENTOR,
)
from cxc.core.utils import setup_logger, check_env_vars
from cxc.core.data_types import GitHubIssue
from cxc.integrations.worktree_ops import validate_worktree




def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()
    
    # Parse command line args
    # INTENTIONAL: cxc-id is REQUIRED - we need it to find the worktree
    if len(sys.argv) < 3:
        print("Usage: uv run python -m cxc.workflows.wt.build_iso <issue-number> <cxc-id>")
        print("\nError: cxc-id is required to locate the worktree and plan file")
        print("Run cxc plan or cxc patch first to create the worktree")
        sys.exit(1)
    
    issue_number = sys.argv[1]
    cxc_id = sys.argv[2]
    
    # Try to load existing state
    temp_logger = setup_logger(cxc_id, "cxc_build_iso")
    state = CxcState.load(cxc_id, temp_logger)
    if state:
        # Found existing state - use the issue number from state if available
        issue_number = state.get("issue_number", issue_number)
        post_state_to_issue(issue_number, cxc_id, state.data, "🔍 Found existing state - resuming isolated build")
    else:
        # No existing state found
        logger = setup_logger(cxc_id, "cxc_build_iso")
        logger.error(f"No state found for CXC ID: {cxc_id}")
        logger.error("Run cxc plan first to create the worktree and state")
        print(f"\nError: No state found for CXC ID: {cxc_id}")
        print("Run cxc plan first to create the worktree and state")
        sys.exit(1)
    
    # Track that this CXC workflow has run
    state.append_cxc_id("cxc_build_iso")
    
    # Set up logger with CXC ID from command line
    logger = setup_logger(cxc_id, "cxc_build_iso")
    logger.info(f"CXC Build Iso starting - ID: {cxc_id}, Issue: {issue_number}")
    
    # Validate environment
    check_env_vars(logger)
    
    # Validate worktree exists
    valid, error = validate_worktree(cxc_id, state)
    if not valid:
        logger.error(f"Worktree validation failed: {error}")
        logger.error("Run cxc plan or cxc patch first")
        make_issue_comment(
            issue_number,
            format_issue_message(cxc_id, "ops", f"❌ Worktree validation failed: {error}\n"
                               "Run cxc plan or cxc patch first")
        )
        sys.exit(1)
    
    # Get worktree path for explicit context
    worktree_path = state.get("worktree_path")
    logger.info(f"Using worktree at: {worktree_path}")
    
    # Get repo information
    try:
        github_repo_url = get_repo_url()
        repo_path = extract_repo_path(github_repo_url)
    except ValueError as e:
        logger.error(f"Error getting repository URL: {e}")
        sys.exit(1)
    
    # Ensure we have required state fields
    if not state.get("branch_name"):
        error_msg = "No branch name in state - run cxc plan first"
        logger.error(error_msg)
        make_issue_comment(
            issue_number,
            format_issue_message(cxc_id, "ops", f"❌ {error_msg}")
        )
        sys.exit(1)
    
    if not state.get("plan_file"):
        error_msg = "No plan file in state - run cxc plan first"
        logger.error(error_msg)
        make_issue_comment(
            issue_number,
            format_issue_message(cxc_id, "ops", f"❌ {error_msg}")
        )
        sys.exit(1)
    
    # Checkout the branch in the worktree
    branch_name = state.get("branch_name")
    result = subprocess.run(["git", "checkout", branch_name], capture_output=True, text=True, cwd=worktree_path)
    if result.returncode != 0:
        logger.error(f"Failed to checkout branch {branch_name} in worktree: {result.stderr}")
        make_issue_comment(
            issue_number,
            format_issue_message(cxc_id, "ops", f"❌ Failed to checkout branch {branch_name} in worktree")
        )
        sys.exit(1)
    logger.info(f"Checked out branch in worktree: {branch_name}")
    
    # Get the plan file from state
    plan_file = state.get("plan_file")
    logger.info(f"Using plan file: {plan_file}")
    
    # Get port information for display
    backend_port = state.get("backend_port", "9100")
    frontend_port = state.get("frontend_port", "9200")
    
    make_issue_comment(
        issue_number, 
        format_issue_message(cxc_id, "ops", f"✅ Starting isolated implementation phase\n"
                           f"🏠 Worktree: {worktree_path}\n"
                           f"🔌 Ports - Backend: {backend_port}, Frontend: {frontend_port}")
    )
    
    # Implement the plan (executing in worktree)
    logger.info("Implementing solution in worktree")
    make_issue_comment(
        issue_number,
        format_issue_message(cxc_id, AGENT_IMPLEMENTOR, "✅ Implementing solution in isolated environment")
    )


    # <CALLING_AGENT> >> cxc/integrations/workflow_ops.py::implement_plan >> cxc/core/agent.py::execute_template
    implement_response = implement_plan(plan_file, cxc_id, logger, working_dir=worktree_path)
    # </CALLING_AGENT>


    if not implement_response.success:
        logger.error(f"Error implementing solution: {implement_response.output}")
        make_issue_comment(
            issue_number,
            format_issue_message(cxc_id, AGENT_IMPLEMENTOR, f"❌ Error implementing solution: {implement_response.output}")
        )
        sys.exit(1)
    
    logger.debug(f"Implementation response: {implement_response.output}")
    make_issue_comment(
        issue_number,
        format_issue_message(cxc_id, AGENT_IMPLEMENTOR, "✅ Solution implemented")
    )
    
    # Post the implementation report to the issue for visibility
    if implement_response.output and implement_response.output.strip():
        post_artifact_to_issue(
            issue_number=issue_number,
            cxc_id=cxc_id,
            agent_name=AGENT_IMPLEMENTOR,
            title="🔨 Implementation Report",
            content=implement_response.output,
            file_path=plan_file,
            collapsible=True,
        )
        logger.info("Posted implementation report to issue")
    
    # Fetch issue data for commit message generation
    logger.info("Fetching issue data for commit message")
    issue = fetch_issue(issue_number, repo_path)
    
    # Get issue classification from state or classify if needed
    issue_command = state.get("issue_class")
    if not issue_command:
        logger.info("No issue classification in state, running classify_issue")
        from cxc.integrations.workflow_ops import classify_issue
        issue_command, error = classify_issue(issue, cxc_id, logger)
        if error:
            logger.error(f"Error classifying issue: {error}")
            # Default to feature if classification fails
            issue_command = "/feature"
            logger.warning("Defaulting to /feature after classification error")
        else:
            # Save the classification for future use
            state.update(issue_class=issue_command)
            state.save("cxc_build_iso")
    
    # Create commit message
    logger.info("Creating implementation commit")
    commit_msg, error = create_commit(AGENT_IMPLEMENTOR, issue, issue_command, cxc_id, logger, worktree_path)
    
    if error:
        logger.error(f"Error creating commit message: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(cxc_id, AGENT_IMPLEMENTOR, f"❌ Error creating commit message: {error}")
        )
        sys.exit(1)
    
    # Commit the implementation (in worktree)
    success, error = commit_changes(commit_msg, cwd=worktree_path)
    
    if not success:
        logger.error(f"Error committing implementation: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(cxc_id, AGENT_IMPLEMENTOR, f"❌ Error committing implementation: {error}")
        )
        sys.exit(1)
    
    logger.info(f"Committed implementation: {commit_msg}")
    make_issue_comment(
        issue_number, format_issue_message(cxc_id, AGENT_IMPLEMENTOR, "✅ Implementation committed")
    )
    
    # Finalize git operations (push and PR)
    # Note: This will work from the worktree context
    finalize_git_operations(state, logger, cwd=worktree_path)
    
    logger.info("Isolated implementation phase completed successfully")
    make_issue_comment(
        issue_number, format_issue_message(cxc_id, "ops", "✅ Isolated implementation phase completed")
    )
    
    # Save final state
    state.save("cxc_build_iso")
    
    # Post final state summary to issue
    post_state_to_issue(issue_number, cxc_id, state.data, "📋 Final build state")


if __name__ == "__main__":
    main()
