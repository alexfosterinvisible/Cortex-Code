"""Shared AI Developer Workflow (ADW) operations."""

import glob
import json
import logging
import os
import subprocess
import re
from typing import Tuple, Optional
from adw.core.data_types import (
    AgentTemplateRequest,
    GitHubIssue,
    AgentPromptResponse,
    IssueClassSlashCommand,
    ADWExtractionResult,
)
from adw.core.agent import execute_template
from adw.integrations.github import ADW_BOT_IDENTIFIER
from adw.core.state import ADWState
from adw.core.utils import parse_json


# Agent name constants
AGENT_PLANNER = "sdlc_planner"
AGENT_IMPLEMENTOR = "sdlc_implementor"
AGENT_CLASSIFIER = "issue_classifier"
AGENT_BRANCH_GENERATOR = "branch_generator"
AGENT_PR_CREATOR = "pr_creator"
AGENT_CLASSIFY_AND_BRANCH = "classify_and_branch"

# Available ADW workflows for runtime validation
AVAILABLE_ADW_WORKFLOWS = [
    # Isolated workflows (all workflows are now iso-based)
    "adw_plan_iso",
    "adw_patch_iso",
    "adw_build_iso",
    "adw_test_iso",
    "adw_review_iso",
    "adw_document_iso",
    "adw_ship_iso",
    "adw_sdlc_zte_iso",  # Zero Touch Execution workflow
    "adw_plan_build_iso",
    "adw_plan_build_test_iso",
    "adw_plan_build_test_review_iso",
    "adw_plan_build_document_iso",
    "adw_plan_build_review_iso",
    "adw_sdlc_iso",
]


def format_issue_message(
    adw_id: str, agent_name: str, message: str, session_id: Optional[str] = None
) -> str:
    """Format a message for issue comments with ADW tracking and bot identifier."""
    # Always include ADW_BOT_IDENTIFIER to prevent webhook loops
    if session_id:
        return f"{ADW_BOT_IDENTIFIER} {adw_id}_{agent_name}_{session_id}: {message}"
    return f"{ADW_BOT_IDENTIFIER} {adw_id}_{agent_name}: {message}"


def extract_adw_info(text: str, temp_adw_id: str) -> ADWExtractionResult:
    """Extract ADW workflow, ID, and model_set from text using classify_adw agent.
    Returns ADWExtractionResult with workflow_command, adw_id, and model_set."""

    # Use classify_adw to extract structured info
    request = AgentTemplateRequest(
        agent_name="adw_classifier",
        slash_command="/classify_adw",
        args=[text],
        adw_id=temp_adw_id,
    )

    try:

        # <CALLING_AGENT> >> adw/core/agent.py::execute_template
        response = execute_template(request)  # No logger available in this function
        # </CALLING_AGENT>


        if not response.success:
            print(f"Failed to classify ADW: {response.output}")
            return ADWExtractionResult()  # Empty result

        # Parse JSON response using utility that handles markdown
        try:
            data = parse_json(response.output, dict)
            adw_command = data.get("adw_slash_command", "").replace(
                "/", ""
            )  # Remove slash
            adw_id = data.get("adw_id")
            model_set = data.get("model_set", "base")  # Default to "base"

            # Validate command
            if adw_command and adw_command in AVAILABLE_ADW_WORKFLOWS:
                return ADWExtractionResult(
                    workflow_command=adw_command,
                    adw_id=adw_id,
                    model_set=model_set
                )

            return ADWExtractionResult()  # Empty result

        except ValueError as e:
            print(f"Failed to parse classify_adw response: {e}")
            return ADWExtractionResult()  # Empty result

    except Exception as e:
        print(f"Error calling classify_adw: {e}")
        return ADWExtractionResult()  # Empty result


def classify_issue(
    issue: GitHubIssue, adw_id: str, logger: logging.Logger
) -> Tuple[Optional[IssueClassSlashCommand], Optional[str]]:
    """Classify GitHub issue and return appropriate slash command.
    Returns (command, error_message) tuple."""

    # Use the classify_issue slash command template with minimal payload
    # Only include the essential fields: number, title, body
    minimal_issue_json = issue.model_dump_json(
        by_alias=True, include={"number", "title", "body"}
    )

    request = AgentTemplateRequest(
        agent_name=AGENT_CLASSIFIER,
        slash_command="/classify_issue",
        args=[minimal_issue_json],
        adw_id=adw_id,
    )

    logger.debug(f"Classifying issue: {issue.title}")


    # <CALLING_AGENT> >> adw/core/agent.py::execute_template
    response = execute_template(request)
    # </CALLING_AGENT>


    logger.debug(
        f"Classification response: {response.model_dump_json(indent=2, by_alias=True)}"
    )

    if not response.success:
        return None, response.output

    # Extract the classification from the response
    output = response.output.strip()

    # Look for the classification pattern in the output
    # Claude might add explanation, so we need to extract just the command
    classification_match = re.search(r"(/chore|/bug|/feature|0)", output)

    if classification_match:
        issue_command = classification_match.group(1)
    else:
        issue_command = output

    if issue_command == "0":
        return None, f"No command selected: {response.output}"

    if issue_command not in ["/chore", "/bug", "/feature"]:
        return None, f"Invalid command selected: {response.output}"

    return issue_command, None  # type: ignore


def build_plan(
    issue: GitHubIssue,
    command: str,
    adw_id: str,
    logger: logging.Logger,
    working_dir: Optional[str] = None,
) -> AgentPromptResponse:
    """Build implementation plan for the issue using the specified command."""
    # Use minimal payload like classify_issue does
    minimal_issue_json = issue.model_dump_json(
        by_alias=True, include={"number", "title", "body"}
    )

    issue_plan_template_request = AgentTemplateRequest(
        agent_name=AGENT_PLANNER,
        slash_command=command,
        args=[str(issue.number), adw_id, minimal_issue_json],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    logger.debug(
        f"issue_plan_template_request: {issue_plan_template_request.model_dump_json(indent=2, by_alias=True)}"
    )


    # <CALLING_AGENT> >> adw/core/agent.py::execute_template
    issue_plan_response = execute_template(issue_plan_template_request)
    # </CALLING_AGENT>


    logger.debug(
        f"issue_plan_response: {issue_plan_response.model_dump_json(indent=2, by_alias=True)}"
    )

    return issue_plan_response


def implement_plan(
    plan_file: str,
    adw_id: str,
    logger: logging.Logger,
    agent_name: Optional[str] = None,
    working_dir: Optional[str] = None,
) -> AgentPromptResponse:
    """Implement the plan using the /implement command."""
    # Use provided agent_name or default to AGENT_IMPLEMENTOR
    implementor_name = agent_name or AGENT_IMPLEMENTOR

    implement_template_request = AgentTemplateRequest(
        agent_name=implementor_name,
        slash_command="/implement",
        args=[plan_file],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    logger.debug(
        f"implement_template_request: {implement_template_request.model_dump_json(indent=2, by_alias=True)}"
    )


    # <CALLING_AGENT> >> adw/core/agent.py::execute_template
    implement_response = execute_template(implement_template_request)
    # </CALLING_AGENT>


    logger.debug(
        f"implement_response: {implement_response.model_dump_json(indent=2, by_alias=True)}"
    )

    return implement_response


def generate_branch_name(
    issue: GitHubIssue,
    issue_class: IssueClassSlashCommand,
    adw_id: str,
    logger: logging.Logger,
) -> Tuple[Optional[str], Optional[str]]:
    """Generate a git branch name for the issue.
    Returns (branch_name, error_message) tuple."""
    # Remove the leading slash from issue_class for the branch name
    issue_type = issue_class.replace("/", "")

    # Use minimal payload like classify_issue does
    minimal_issue_json = issue.model_dump_json(
        by_alias=True, include={"number", "title", "body"}
    )

    request = AgentTemplateRequest(
        agent_name=AGENT_BRANCH_GENERATOR,
        slash_command="/generate_branch_name",
        args=[issue_type, adw_id, minimal_issue_json],
        adw_id=adw_id,
    )


    # <CALLING_AGENT> >> adw/core/agent.py::execute_template
    response = execute_template(request)
    # </CALLING_AGENT>


    if not response.success:
        return None, response.output

    branch_name = response.output.strip()
    logger.info(f"Generated branch name: {branch_name}")
    return branch_name, None


def classify_and_generate_branch(
    issue: GitHubIssue,
    adw_id: str,
    logger: logging.Logger,
) -> Tuple[Optional[IssueClassSlashCommand], Optional[str], Optional[str]]:
    """Classify issue AND generate branch name in ONE LLM call.
    
    This is ~2x faster than calling classify_issue + generate_branch_name sequentially.
    Returns (issue_class, branch_name, error_message) tuple.
    """
    # Use minimal payload
    minimal_issue_json = issue.model_dump_json(
        by_alias=True, include={"number", "title", "body"}
    )

    request = AgentTemplateRequest(
        agent_name=AGENT_CLASSIFY_AND_BRANCH,
        slash_command="/classify_and_branch",
        args=[adw_id, minimal_issue_json],
        adw_id=adw_id,
    )

    logger.debug(f"Combined classify+branch for issue: {issue.title}")

    # <CALLING_AGENT> >> adw/core/agent.py::execute_template
    response = execute_template(request)
    # </CALLING_AGENT>

    if not response.success:
        return None, None, response.output

    # Parse JSON response
    try:
        data = parse_json(response.output, dict)
        issue_class = data.get("issue_class")
        branch_name = data.get("branch_name")

        if not issue_class or issue_class not in ["/chore", "/bug", "/feature"]:
            return None, None, f"Invalid issue_class: {issue_class}"
        
        if not branch_name:
            return None, None, "No branch_name in response"

        logger.info(f"Classified as {issue_class}, branch: {branch_name}")
        return issue_class, branch_name, None

    except ValueError as e:
        return None, None, f"Failed to parse response: {e}"


def create_commit(
    agent_name: str,
    issue: GitHubIssue,
    issue_class: IssueClassSlashCommand,
    adw_id: str,
    logger: logging.Logger,
    working_dir: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Create a git commit with a properly formatted message.
    Returns (commit_message, error_message) tuple."""
    # Remove the leading slash from issue_class
    issue_type = issue_class.replace("/", "")

    # Create unique committer agent name by suffixing '_committer'
    unique_agent_name = f"{agent_name}_committer"

    # Use minimal payload like classify_issue does
    minimal_issue_json = issue.model_dump_json(
        by_alias=True, include={"number", "title", "body"}
    )

    request = AgentTemplateRequest(
        agent_name=unique_agent_name,
        slash_command="/commit",
        args=[agent_name, issue_type, minimal_issue_json],
        adw_id=adw_id,
        working_dir=working_dir,
    )


    # <CALLING_AGENT> >> adw/core/agent.py::execute_template
    response = execute_template(request)
    # </CALLING_AGENT>


    if not response.success:
        return None, response.output

    commit_message = response.output.strip()
    logger.info(f"Created commit message: {commit_message}")
    return commit_message, None


def create_pull_request(
    branch_name: str,
    issue: Optional[GitHubIssue],
    state: ADWState,
    logger: logging.Logger,
    working_dir: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Create a pull request for the implemented changes.
    Returns (pr_url, error_message) tuple."""

    # Get plan file from state (may be None for test runs)
    plan_file = state.get("plan_file") or "No plan file (test run)"
    adw_id = state.get("adw_id")

    # If we don't have issue data, try to construct minimal data
    if not issue:
        issue_data = state.get("issue", {})
        issue_json = json.dumps(issue_data) if issue_data else "{}"
    elif isinstance(issue, dict):
        # Try to reconstruct as GitHubIssue model which handles datetime serialization
        from adw.core.data_types import GitHubIssue

        try:
            issue_model = GitHubIssue(**issue)
            # Use minimal payload like classify_issue does
            issue_json = issue_model.model_dump_json(
                by_alias=True, include={"number", "title", "body"}
            )
        except Exception:
            # Fallback: use json.dumps with default str converter for datetime
            issue_json = json.dumps(issue, default=str)
    else:
        # Use minimal payload like classify_issue does
        issue_json = issue.model_dump_json(
            by_alias=True, include={"number", "title", "body"}
        )

    request = AgentTemplateRequest(
        agent_name=AGENT_PR_CREATOR,
        slash_command="/pull_request",
        args=[branch_name, issue_json, plan_file, adw_id],
        adw_id=adw_id,
        working_dir=working_dir,
    )


    # <CALLING_AGENT> >> adw/core/agent.py::execute_template
    response = execute_template(request)
    # </CALLING_AGENT>


    if not response.success:
        return None, response.output

    pr_url = response.output.strip()
    logger.info(f"Created pull request: {pr_url}")
    return pr_url, None


def ensure_plan_exists(state: ADWState, issue_number: str) -> str:
    """Find or error if no plan exists for issue.
    Used by isolated build workflows in standalone mode."""
    # Check if plan file is in state
    if state.get("plan_file"):
        return state.get("plan_file")

    # Check current branch
    from adw.integrations.git_ops import get_current_branch

    branch = get_current_branch()

    # Look for plan in branch name
    if f"-{issue_number}-" in branch:
        # Look for plan file
        plans = glob.glob(f"specs/*{issue_number}*.md")
        if plans:
            return plans[0]

    # No plan found
    raise ValueError(
        f"No plan found for issue {issue_number}. Run adw plan first."
    )


def ensure_adw_id(
    issue_number: str,
    adw_id: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> str:
    """Get ADW ID or create a new one and initialize state.

    Args:
        issue_number: The issue number to find/create ADW ID for
        adw_id: Optional existing ADW ID to use
        logger: Optional logger instance

    Returns:
        The ADW ID (existing or newly created)
    """
    # If ADW ID provided, check if state exists
    if adw_id:
        state = ADWState.load(adw_id, logger)
        if state:
            if logger:
                logger.info(f"Found existing ADW state for ID: {adw_id}")
            else:
                print(f"Found existing ADW state for ID: {adw_id}")
            return adw_id
        # ADW ID provided but no state exists, create state
        state = ADWState(adw_id)
        state.update(adw_id=adw_id, issue_number=issue_number)
        state.save("ensure_adw_id")
        if logger:
            logger.info(f"Created new ADW state for provided ID: {adw_id}")
        else:
            print(f"Created new ADW state for provided ID: {adw_id}")
        return adw_id

    # No ADW ID provided, create new one with state
    from adw.core.utils import make_adw_id

    new_adw_id = make_adw_id()
    state = ADWState(new_adw_id)
    state.update(adw_id=new_adw_id, issue_number=issue_number)
    state.save("ensure_adw_id")
    if logger:
        logger.info(f"Created new ADW ID and state: {new_adw_id}")
    else:
        print(f"Created new ADW ID and state: {new_adw_id}")
    return new_adw_id


def find_existing_branch_for_issue(
    issue_number: str, adw_id: Optional[str] = None, cwd: Optional[str] = None
) -> Optional[str]:
    """Find an existing branch for the given issue number.
    Returns branch name if found, None otherwise."""
    # List all branches
    result = subprocess.run(
        ["git", "branch", "-a"], capture_output=True, text=True, cwd=cwd
    )

    if result.returncode != 0:
        return None

    branches = result.stdout.strip().split("\n")

    # Look for branch with standardized pattern: *-issue-{issue_number}-adw-{adw_id}-*
    for branch in branches:
        branch = branch.strip().replace("* ", "").replace("remotes/origin/", "")
        # Check for the standardized pattern
        if f"-issue-{issue_number}-" in branch:
            if adw_id and f"-adw-{adw_id}-" in branch:
                return branch
            elif not adw_id:
                # Return first match if no adw_id specified
                return branch

    return None


def find_plan_for_issue(
    issue_number: str, adw_id: Optional[str] = None
) -> Optional[str]:
    """Find plan file for the given issue number and optional adw_id.
    Returns path to plan file if found, None otherwise."""
    from adw.core.config import ADWConfig
    
    config = ADWConfig.load()
    agents_base = config.get_project_artifacts_dir()

    if not agents_base.exists():
        return None

    # If adw_id is provided, check specific directory first
    if adw_id:
        plan_path = agents_base / adw_id / AGENT_PLANNER / "plan.md"
        if plan_path.exists():
            return str(plan_path)

    # Otherwise, search all agent directories
    for agent_dir in agents_base.iterdir():
        if agent_dir.is_dir() and agent_dir.name != "trees":
            plan_path = agent_dir / AGENT_PLANNER / "plan.md"
            if plan_path.exists():
                # Check if this plan is for our issue by reading branch info or checking commits
                # For now, return the first plan found (can be improved)
                return str(plan_path)

    return None


def create_or_find_branch(
    issue_number: str,
    issue: GitHubIssue,
    state: ADWState,
    logger: logging.Logger,
    cwd: Optional[str] = None,
) -> Tuple[str, Optional[str]]:
    """Create or find a branch for the given issue.

    1. First checks state for existing branch name
    2. Then looks for existing branches matching the issue
    3. If none found, classifies the issue and creates a new branch

    Returns (branch_name, error_message) tuple.
    """
    # 1. Check state for branch name
    branch_name = state.get("branch_name") or state.get("branch", {}).get("name")
    if branch_name:
        logger.info(f"Found branch in state: {branch_name}")
        # Check if we need to checkout
        from adw.integrations.git_ops import get_current_branch

        current = get_current_branch(cwd=cwd)
        if current != branch_name:
            result = subprocess.run(
                ["git", "checkout", branch_name],
                capture_output=True,
                text=True,
                cwd=cwd,
            )
            if result.returncode != 0:
                # Branch might not exist locally, try to create from remote
                result = subprocess.run(
                    ["git", "checkout", "-b", branch_name, f"origin/{branch_name}"],
                    capture_output=True,
                    text=True,
                    cwd=cwd,
                )
                if result.returncode != 0:
                    return "", f"Failed to checkout branch: {result.stderr}"
        return branch_name, None

    # 2. Look for existing branch
    adw_id = state.get("adw_id")
    existing_branch = find_existing_branch_for_issue(issue_number, adw_id, cwd=cwd)
    if existing_branch:
        logger.info(f"Found existing branch: {existing_branch}")
        # Checkout the branch
        result = subprocess.run(
            ["git", "checkout", existing_branch],
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        if result.returncode != 0:
            return "", f"Failed to checkout branch: {result.stderr}"
        state.update(branch_name=existing_branch)
        return existing_branch, None

    # 3. Create new branch - classify issue first
    logger.info("No existing branch found, creating new one")

    # Classify the issue
    issue_command, error = classify_issue(issue, adw_id, logger)
    if error:
        return "", f"Failed to classify issue: {error}"

    state.update(issue_class=issue_command)

    # Generate branch name
    branch_name, error = generate_branch_name(issue, issue_command, adw_id, logger)
    if error:
        return "", f"Failed to generate branch name: {error}"

    # Create the branch
    from adw.integrations.git_ops import create_branch

    success, error = create_branch(branch_name, cwd=cwd)
    if not success:
        return "", f"Failed to create branch: {error}"

    state.update(branch_name=branch_name)
    logger.info(f"Created and checked out new branch: {branch_name}")

    return branch_name, None


def find_spec_file(state: ADWState, logger: logging.Logger) -> Optional[str]:
    """Find the spec file from state or by examining git diff.

    For isolated workflows, automatically uses worktree_path from state.
    """
    # Get worktree path if in isolated workflow
    worktree_path = state.get("worktree_path")

    # Check if spec file is already in state (from plan phase)
    spec_file = state.get("plan_file")
    if spec_file:
        # If worktree_path exists and spec_file is relative, make it absolute
        if worktree_path and not os.path.isabs(spec_file):
            spec_file = os.path.join(worktree_path, spec_file)

        if os.path.exists(spec_file):
            logger.info(f"Using spec file from state: {spec_file}")
            return spec_file

    # Otherwise, try to find it from git diff
    logger.info("Looking for spec file in git diff")
    result = subprocess.run(
        ["git", "diff", "origin/main", "--name-only"],
        capture_output=True,
        text=True,
        cwd=worktree_path,
    )

    if result.returncode == 0:
        files = result.stdout.strip().split("\n")
        spec_files = [f for f in files if f.startswith("specs/") and f.endswith(".md")]

        if spec_files:
            # Use the first spec file found
            spec_file = spec_files[0]
            if worktree_path:
                spec_file = os.path.join(worktree_path, spec_file)
            logger.info(f"Found spec file: {spec_file}")
            return spec_file

    # If still not found, try to derive from branch name
    branch_name = state.get("branch_name")
    if branch_name:
        # Extract issue number from branch name
        import re

        match = re.search(r"issue-(\d+)", branch_name)
        if match:
            issue_num = match.group(1)
            adw_id = state.get("adw_id")

            # Look for spec files matching the pattern
            import glob

            # Use worktree_path if provided, otherwise current directory
            search_dir = worktree_path if worktree_path else os.getcwd()
            pattern = os.path.join(
                search_dir, f"specs/issue-{issue_num}-adw-{adw_id}*.md"
            )
            spec_files = glob.glob(pattern)

            if spec_files:
                spec_file = spec_files[0]
                logger.info(f"Found spec file by pattern: {spec_file}")
                return spec_file

    logger.warning("No spec file found")
    return None


def create_and_implement_patch(
    adw_id: str,
    review_change_request: str,
    logger: logging.Logger,
    agent_name_planner: str,
    agent_name_implementor: str,
    spec_path: Optional[str] = None,
    issue_screenshots: Optional[str] = None,
    working_dir: Optional[str] = None,
) -> Tuple[Optional[str], AgentPromptResponse]:
    """Create a patch plan and implement it.
    Returns (patch_file_path, implement_response) tuple."""

    # Create patch plan using /patch command
    args = [adw_id, review_change_request]

    # Add optional arguments in the correct order
    if spec_path:
        args.append(spec_path)
    else:
        args.append("")  # Empty string for optional spec_path

    args.append(agent_name_planner)

    if issue_screenshots:
        args.append(issue_screenshots)

    request = AgentTemplateRequest(
        agent_name=agent_name_planner,
        slash_command="/patch",
        args=args,
        adw_id=adw_id,
        working_dir=working_dir,
    )

    logger.debug(
        f"Patch plan request: {request.model_dump_json(indent=2, by_alias=True)}"
    )


    # <CALLING_AGENT> >> adw/core/agent.py::execute_template
    response = execute_template(request)
    # </CALLING_AGENT>


    logger.debug(
        f"Patch plan response: {response.model_dump_json(indent=2, by_alias=True)}"
    )

    if not response.success:
        logger.error(f"Error creating patch plan: {response.output}")
        # Return None and a failed response
        return None, AgentPromptResponse(
            output=f"Failed to create patch plan: {response.output}", success=False
        )

    # Extract the patch plan file path from the response
    patch_file_path = response.output.strip()

    # Validate that it looks like a file path
    if "specs/patch/" not in patch_file_path or not patch_file_path.endswith(".md"):
        logger.error(f"Invalid patch plan path returned: {patch_file_path}")
        return None, AgentPromptResponse(
            output=f"Invalid patch plan path: {patch_file_path}", success=False
        )

    logger.info(f"Created patch plan: {patch_file_path}")


    # <CALLING_AGENT> >> workflow_ops.py::implement_plan >> adw/core/agent.py::execute_template
    implement_response = implement_plan(
        patch_file_path, adw_id, logger, agent_name_implementor, working_dir=working_dir
    )
    # </CALLING_AGENT>


    return patch_file_path, implement_response


def build_comprehensive_pr_body(
    state: ADWState,
    issue: Optional[GitHubIssue],
    review_summary: Optional[str] = None,
    test_summary: Optional[str] = None,
    remediation_loops: int = 0,
    logger: Optional[logging.Logger] = None,
) -> str:
    """Build a comprehensive PR body with all phase artifacts.
    
    Args:
        state: ADW state containing workflow data
        issue: GitHub issue data
        review_summary: Optional review summary markdown
        test_summary: Optional test results summary
        remediation_loops: Number of remediation loops executed
        logger: Optional logger
        
    Returns:
        Comprehensive markdown PR body
    """
    adw_id = state.get("adw_id", "unknown")
    issue_number = state.get("issue_number", "?")
    plan_file = state.get("plan_file", "")
    issue_class = state.get("issue_class", "/feature")
    all_adws = state.get("all_adws", [])
    
    # Extract issue type from classification
    issue_type = issue_class.lstrip("/") if issue_class else "feature"
    
    # Build issue title
    issue_title = issue.title if issue else f"Issue #{issue_number}"
    
    sections = []
    
    # Header
    sections.append("## Summary\n")
    sections.append(f"This PR implements {issue_type} #{issue_number}: {issue_title}\n")
    
    # Implementation Plan
    if plan_file:
        sections.append("## 📋 Implementation Plan\n")
        sections.append(f"See [{plan_file}]({plan_file}) for detailed design.\n")
    
    # Phase Execution Summary
    sections.append("## 🔄 Workflow Execution\n")
    
    phase_status = []
    phase_map = {
        "adw_plan_iso": ("📝 Plan", "Created implementation spec"),
        "adw_build_iso": ("🔨 Build", "Implemented changes"),
        "adw_test_iso": ("🧪 Test", "Ran test suite"),
        "adw_review_iso": ("🔍 Review", "Validated implementation"),
        "adw_document_iso": ("📖 Document", "Updated documentation"),
    }
    
    for phase_id, (phase_name, phase_desc) in phase_map.items():
        if phase_id in all_adws:
            phase_status.append(f"- [x] **{phase_name}**: {phase_desc}")
        else:
            phase_status.append(f"- [ ] **{phase_name}**: _{phase_desc}_")
    
    sections.append("\n".join(phase_status) + "\n")
    
    # Remediation Loops
    if remediation_loops > 0:
        sections.append("### 🔧 Remediation\n")
        sections.append(f"- **{remediation_loops}** remediation loop(s) executed to resolve issues\n")
    
    # Test Results
    if test_summary:
        sections.append("## 🧪 Test Results\n")
        sections.append(f"{test_summary}\n")
    
    # Review Summary
    if review_summary:
        sections.append("## 🔍 Review Summary\n")
        sections.append(f"{review_summary}\n")
    
    # Files Changed (will be populated by git diff in PR template)
    sections.append("## 📁 Changes\n")
    sections.append("_See Files Changed tab for detailed diff_\n")
    
    # ADW Tracking
    sections.append("---\n")
    sections.append(f"**ADW ID:** `{adw_id}`\n")
    sections.append(f"**Phases Completed:** {len([p for p in all_adws if p in phase_map])}/5\n")
    
    # Close issue reference
    sections.append(f"\nCloses #{issue_number}")
    
    return "\n".join(sections)


def post_artifact_to_issue(
    issue_number: str,
    adw_id: str,
    agent_name: str,
    title: str,
    content: str,
    file_path: Optional[str] = None,
    max_length: int = 8000,
    collapsible: bool = True,
    print_to_terminal: bool = True,
) -> None:
    """Post an artifact (plan, report, etc.) to a GitHub issue as a comment.
    
    Also prints the full artifact to terminal with rich markdown formatting.
    
    Args:
        issue_number: GitHub issue number
        adw_id: ADW workflow ID
        agent_name: Name of the agent posting (e.g., "sdlc_planner")
        title: Title/heading for the artifact (e.g., "📋 Implementation Plan")
        content: The artifact content to post
        file_path: Optional path to the artifact file (shown in summary)
        max_length: Maximum content length before truncation (default 8000)
        collapsible: Whether to wrap in <details> block (default True)
        print_to_terminal: Whether to print full content to terminal (default True)
    """
    from adw.integrations.github import make_issue_comment
    from adw.core.utils import print_artifact
    
    if not content or not content.strip():
        return
    
    # Print full artifact to terminal with rich markdown formatting
    if print_to_terminal:
        print_artifact(title=title, content=content, file_path=file_path)
    
    # Build the comment for GitHub
    comment_parts = [f"{title}\n"]
    
    # Truncate if needed for GitHub (terminal gets full content)
    truncated = False
    display_content = content.strip()
    if len(display_content) > max_length:
        display_content = display_content[:max_length]
        truncated = True
    
    if collapsible:
        # Use collapsible details block
        summary_text = "Click to expand"
        if file_path:
            summary_text = f"Click to expand ({file_path})"
        
        comment_parts.append(f"<details>\n<summary>{summary_text}</summary>\n")
        comment_parts.append(f"\n{display_content}\n")
        
        if truncated:
            comment_parts.append(f"\n\n... _(truncated, see full file in PR)_\n")
        
        comment_parts.append("\n</details>")
    else:
        # Post content directly (for shorter content)
        comment_parts.append(f"\n{display_content}")
        
        if truncated:
            comment_parts.append(f"\n\n... _(truncated, see full file in PR)_")
    
    full_comment = "".join(comment_parts)
    
    # Post to issue using format_issue_message for consistent formatting
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, agent_name, full_comment)
    )


def post_state_to_issue(
    issue_number: str,
    adw_id: str,
    state_data: dict,
    title: str = "📋 State",
    print_to_terminal: bool = True,
) -> None:
    """Post workflow state to a GitHub issue as a collapsible comment.
    
    Also prints the state to terminal with rich formatting.
    
    Args:
        issue_number: GitHub issue number
        adw_id: ADW workflow ID
        state_data: The state dictionary to post
        title: Title for the state comment (e.g., "📋 Final planning state")
        print_to_terminal: Whether to print to terminal (default True)
    """
    from adw.integrations.github import make_issue_comment
    from adw.core.utils import print_state_json
    
    # Print to terminal with rich formatting
    if print_to_terminal:
        print_state_json(state_data, title=title)
    
    state_json = json.dumps(state_data, indent=2)
    
    comment = (
        f"{title}\n"
        f"<details>\n"
        f"<summary>Click to expand state</summary>\n\n"
        f"```json\n{state_json}\n```\n"
        f"</details>"
    )
    
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", comment)
    )
