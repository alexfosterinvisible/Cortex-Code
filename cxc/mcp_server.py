"""(Claude) CXC Framework MCP Server - exposes CXC CLI functionality via MCP protocol.

This server provides MCP tools for:
- SDLC orchestration (plan, build, test, review, document, ship, sdlc, zte)
- GitHub operations (fetch issues, post comments, list issues)
- Git operations (branches, commits, PRs)
- Workflow state management
"""
import importlib
import logging
import sys
import os
from typing import Optional, Literal

from mcp.server.fastmcp import FastMCP

# Setup logging to stderr (stdout reserved for MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("cxc-mcp")

# Initialize MCP server
mcp = FastMCP("cxc")

# Import CXC modules
from cxc.core.config import CxcConfig
from cxc.core.state import CxcState
from cxc.core.data_types import GitHubIssue
from cxc.integrations import github, git_ops


# ============================================================================
# SDLC ORCHESTRATION TOOLS
# ============================================================================

def _run_workflow(module_name: str, args: list) -> str:
    """Run a workflow module and capture output."""
    # Patch sys.argv for the workflow
    original_argv = sys.argv
    sys.argv = [f"cxc {module_name}"] + args

    try:
        module = importlib.import_module(f"cxc.workflows.{module_name}")
        if hasattr(module, "main"):
            module.main()
            return f"Workflow {module_name} completed successfully"
        else:
            return f"Error: Module cxc.workflows.{module_name} has no main() function"
    except ImportError as e:
        return f"Error: Could not import workflow '{module_name}': {e}"
    except Exception as e:
        return f"Error running workflow '{module_name}': {e}"
    finally:
        sys.argv = original_argv


@mcp.tool()
def cxc_plan(issue_number: str, cxc_id: Optional[str] = None) -> str:
    """Plan implementation for a GitHub issue.

    Creates an implementation plan based on the issue requirements.
    This is the first step in the SDLC workflow.

    Args:
        issue_number: GitHub issue number to plan
        cxc_id: Optional CXC workflow ID (auto-generated if not provided)

    Returns:
        Status message with plan file location
    """
    args = [issue_number]
    if cxc_id:
        args.append(cxc_id)
    return _run_workflow("wt.plan_iso", args)


@mcp.tool()
def cxc_build(issue_number: str, cxc_id: str) -> str:
    """Build implementation from an existing plan.

    Executes the implementation plan created by cxc_plan.

    Args:
        issue_number: GitHub issue number
        cxc_id: CXC workflow ID from the planning phase

    Returns:
        Status message with implementation results
    """
    return _run_workflow("wt.build_iso", [issue_number, cxc_id])


@mcp.tool()
def cxc_test(issue_number: str, cxc_id: str, skip_e2e: bool = False) -> str:
    """Run tests for the implementation.

    Executes the test suite to validate the implementation.

    Args:
        issue_number: GitHub issue number
        cxc_id: CXC workflow ID
        skip_e2e: Skip end-to-end tests if True

    Returns:
        Test results summary
    """
    args = [issue_number, cxc_id]
    if skip_e2e:
        args.append("--skip-e2e")
    return _run_workflow("wt.test_iso", args)


@mcp.tool()
def cxc_review(issue_number: str, cxc_id: str, skip_resolution: bool = False) -> str:
    """Review implementation against the specification.

    Validates that the implementation matches the plan requirements.

    Args:
        issue_number: GitHub issue number
        cxc_id: CXC workflow ID
        skip_resolution: Skip auto-resolution of issues if True

    Returns:
        Review results summary
    """
    args = [issue_number, cxc_id]
    if skip_resolution:
        args.append("--skip-resolution")
    return _run_workflow("wt.review_iso", args)


@mcp.tool()
def cxc_document(issue_number: str, cxc_id: str) -> str:
    """Generate documentation for the implementation.

    Creates or updates documentation based on the changes made.

    Args:
        issue_number: GitHub issue number
        cxc_id: CXC workflow ID

    Returns:
        Documentation generation status
    """
    return _run_workflow("wt.document_iso", [issue_number, cxc_id])


@mcp.tool()
def cxc_ship(issue_number: str, cxc_id: str) -> str:
    """Ship changes by merging the pull request.

    Approves and merges the PR after validation.

    Args:
        issue_number: GitHub issue number
        cxc_id: CXC workflow ID

    Returns:
        Ship status with PR merge result
    """
    return _run_workflow("wt.ship_iso", [issue_number, cxc_id])


@mcp.tool()
def cxc_sdlc(
    issue_number: str,
    cxc_id: Optional[str] = None,
    skip_e2e: bool = False,
    skip_resolution: bool = False
) -> str:
    """Run complete SDLC workflow for an issue.

    Executes the full software development lifecycle:
    Plan -> Build -> Test -> Review -> Document

    Args:
        issue_number: GitHub issue number to process
        cxc_id: Optional CXC workflow ID (auto-generated if not provided)
        skip_e2e: Skip end-to-end tests if True
        skip_resolution: Skip auto-resolution of review issues if True

    Returns:
        Complete SDLC execution summary
    """
    args = [issue_number]
    if cxc_id:
        args.append(cxc_id)
    if skip_e2e:
        args.append("--skip-e2e")
    if skip_resolution:
        args.append("--skip-resolution")
    return _run_workflow("wt.sdlc_iso", args)


@mcp.tool()
def cxc_zte(
    issue_number: str,
    cxc_id: Optional[str] = None,
    skip_e2e: bool = False,
    skip_resolution: bool = False
) -> str:
    """Zero Touch Execution - Full SDLC with automatic ship.

    Runs the complete SDLC workflow AND automatically merges the PR.
    This is the fully autonomous issue-to-production pipeline.

    Args:
        issue_number: GitHub issue number to process
        cxc_id: Optional CXC workflow ID (auto-generated if not provided)
        skip_e2e: Skip end-to-end tests if True
        skip_resolution: Skip auto-resolution of review issues if True

    Returns:
        Complete ZTE execution summary including merge status
    """
    args = [issue_number]
    if cxc_id:
        args.append(cxc_id)
    if skip_e2e:
        args.append("--skip-e2e")
    if skip_resolution:
        args.append("--skip-resolution")
    return _run_workflow("wt.sdlc_zte_iso", args)


@mcp.tool()
def cxc_patch(issue_number: str, cxc_id: Optional[str] = None) -> str:
    """Create and implement a patch for an issue.

    Generates a patch plan and implements it directly.
    Useful for quick fixes and small changes.

    Args:
        issue_number: GitHub issue number
        cxc_id: Optional CXC workflow ID (auto-generated if not provided)

    Returns:
        Patch implementation status
    """
    args = [issue_number]
    if cxc_id:
        args.append(cxc_id)
    return _run_workflow("wt.patch_iso", args)


# ============================================================================
# GITHUB OPERATION TOOLS
# ============================================================================

@mcp.tool()
def fetch_github_issue(issue_number: str) -> dict:
    """Fetch a GitHub issue with full details.

    Retrieves issue data including title, body, labels, comments, and metadata.

    Args:
        issue_number: GitHub issue number to fetch

    Returns:
        Dictionary containing issue data (title, body, state, labels, comments, etc.)
    """
    repo_url = github.get_repo_url()
    repo_path = github.extract_repo_path(repo_url)
    issue = github.fetch_issue(issue_number, repo_path)
    return issue.model_dump(by_alias=True)


@mcp.tool()
def post_issue_comment(issue_number: str, comment: str) -> str:
    """Post a comment to a GitHub issue.

    Args:
        issue_number: GitHub issue number
        comment: Comment text to post

    Returns:
        Success message
    """
    github.make_issue_comment(issue_number, comment)
    return f"Comment posted to issue #{issue_number}"


@mcp.tool()
def list_open_issues() -> list:
    """List all open issues in the repository.

    Returns:
        List of open issues with number, title, body, and labels
    """
    repo_url = github.get_repo_url()
    repo_path = github.extract_repo_path(repo_url)
    issues = github.fetch_open_issues(repo_path)
    return [issue.model_dump(by_alias=True) for issue in issues]


@mcp.tool()
def get_repository_url() -> str:
    """Get the GitHub repository URL.

    Returns:
        Repository URL from git remote origin
    """
    return github.get_repo_url()


@mcp.tool()
def close_github_issue(issue_number: str) -> str:
    """Close a GitHub issue.

    Args:
        issue_number: GitHub issue number to close

    Returns:
        Success or error message
    """
    success, error = github.close_issue(issue_number)
    if success:
        return f"Issue #{issue_number} closed successfully"
    return f"Failed to close issue: {error}"


# ============================================================================
# GIT OPERATION TOOLS
# ============================================================================

@mcp.tool()
def get_current_branch() -> str:
    """Get the current git branch name.

    Returns:
        Current branch name
    """
    return git_ops.get_current_branch()


@mcp.tool()
def create_git_branch(branch_name: str) -> str:
    """Create and checkout a new git branch.

    Args:
        branch_name: Name for the new branch

    Returns:
        Success or error message
    """
    success, error = git_ops.create_branch(branch_name)
    if success:
        return f"Created and checked out branch: {branch_name}"
    return f"Failed to create branch: {error}"


@mcp.tool()
def commit_changes(message: str) -> str:
    """Stage all changes and create a commit.

    Args:
        message: Commit message

    Returns:
        Success or error message
    """
    success, error = git_ops.commit_changes(message)
    if success:
        return f"Changes committed: {message}"
    return f"Failed to commit: {error}"


@mcp.tool()
def push_branch(branch_name: str) -> str:
    """Push a branch to the remote repository.

    Args:
        branch_name: Branch name to push

    Returns:
        Success or error message
    """
    success, error = git_ops.push_branch(branch_name)
    if success:
        return f"Pushed branch: {branch_name}"
    return f"Failed to push: {error}"


@mcp.tool()
def check_pr_exists(branch_name: str) -> str:
    """Check if a pull request exists for a branch.

    Args:
        branch_name: Branch name to check

    Returns:
        PR URL if exists, or message indicating no PR
    """
    pr_url = git_ops.check_pr_exists(branch_name)
    if pr_url:
        return f"PR exists: {pr_url}"
    return "No PR exists for this branch"


@mcp.tool()
def merge_pull_request(pr_number: str, method: Literal["merge", "squash", "rebase"] = "squash") -> str:
    """Merge a pull request.

    Args:
        pr_number: PR number to merge
        method: Merge method - 'merge', 'squash', or 'rebase'

    Returns:
        Success or error message
    """
    success, error = git_ops.merge_pr(pr_number, logger, method)
    if success:
        return f"PR #{pr_number} merged using {method}"
    return f"Failed to merge PR: {error}"


@mcp.tool()
def approve_pull_request(pr_number: str) -> str:
    """Approve a pull request.

    Args:
        pr_number: PR number to approve

    Returns:
        Success or error message
    """
    success, error = git_ops.approve_pr(pr_number, logger)
    if success:
        return f"PR #{pr_number} approved"
    return f"Failed to approve PR: {error}"


# ============================================================================
# WORKFLOW STATE TOOLS
# ============================================================================

@mcp.tool()
def load_cxc_state(cxc_id: str) -> dict:
    """Load CXC workflow state.

    Retrieves the persisted state for a workflow, including issue number,
    branch name, plan file, and other workflow data.

    Args:
        cxc_id: CXC workflow ID

    Returns:
        Dictionary containing workflow state, or error message
    """
    state = CxcState.load(cxc_id, logger)
    if state:
        return state.data
    return {"error": f"No state found for CXC ID: {cxc_id}"}


@mcp.tool()
def get_cxc_state_value(cxc_id: str, key: str) -> str:
    """Get a specific value from CXC workflow state.

    Args:
        cxc_id: CXC workflow ID
        key: State key to retrieve (e.g., 'issue_number', 'branch_name', 'plan_file')

    Returns:
        The value for the key, or error message
    """
    state = CxcState.load(cxc_id, logger)
    if state:
        value = state.get(key)
        if value is not None:
            return str(value)
        return f"Key '{key}' not found in state"
    return f"No state found for CXC ID: {cxc_id}"


@mcp.tool()
def list_available_workflows() -> list:
    """List all available CXC workflows.

    Returns:
        List of workflow names and descriptions
    """
    from cxc.integrations.workflow_ops import AVAILABLE_CXC_WORKFLOWS
    return AVAILABLE_CXC_WORKFLOWS


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Run the CXC MCP server."""
    logger.info("Starting CXC MCP server...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
