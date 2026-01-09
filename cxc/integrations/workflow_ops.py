"""Shared Cortex Code (CXC) operations."""

import glob
import json
import logging
import os
import subprocess
import re
from typing import Tuple, Optional
from cxc.core.data_types import (
    AgentTemplateRequest,
    GitHubIssue,
    AgentPromptResponse,
    IssueClassSlashCommand,
    CXCExtractionResult,
)
from cxc.core.agent import execute_template
from cxc.integrations.github import CXC_BOT_IDENTIFIER
from cxc.core.state import CxcState
from cxc.core.utils import parse_json, print_agent_log


# Agent name constants
AGENT_PLANNER = "sdlc_planner"
AGENT_IMPLEMENTOR = "sdlc_implementor"
AGENT_CLASSIFIER = "issue_classifier"
AGENT_BRANCH_GENERATOR = "branch_generator"
AGENT_PR_CREATOR = "pr_creator"
AGENT_CLASSIFY_AND_BRANCH = "classify_and_branch"

# Available CXC workflows for runtime validation
AVAILABLE_CXC_WORKFLOWS = [
    # Isolated workflows (all workflows are now iso-based)
    "cxc_plan_iso",
    "cxc_patch_iso",
    "cxc_build_iso",
    "cxc_test_iso",
    "cxc_review_iso",
    "cxc_document_iso",
    "cxc_ship_iso",
    "cxc_sdlc_zte_iso",  # Zero Touch Execution workflow
    "cxc_plan_build_iso",
    "cxc_plan_build_test_iso",
    "cxc_plan_build_test_review_iso",
    "cxc_plan_build_document_iso",
    "cxc_plan_build_review_iso",
    "cxc_sdlc_iso",
]


def format_issue_message(
    cxc_id: str, agent_name: str, message: str, session_id: Optional[str] = None
) -> str:
    """Format a message for issue comments with CXC tracking and bot identifier."""
    # Always include CXC_BOT_IDENTIFIER to prevent webhook loops
    if session_id:
        return f"{CXC_BOT_IDENTIFIER} {cxc_id}_{agent_name}_{session_id}: {message}"
    return f"{CXC_BOT_IDENTIFIER} {cxc_id}_{agent_name}: {message}"


# ----------- Phase-based comment consolidation -----------
# Instead of ~74 comments per SDLC run, consolidate into ~5 phase comments

PHASE_NAMES = ["plan", "build", "test", "review", "document", "ship"]


def get_phase_comment_pattern(cxc_id: str, phase: str) -> str:
    """Get the pattern used to identify phase-based comments.
    
    Pattern format: [CXC-AGENTS] {cxc_id}_{phase}
    """
    return f"{CXC_BOT_IDENTIFIER} {cxc_id}_{phase}"


def edit_or_create_phase_comment(
    issue_number: str,
    cxc_id: str,
    phase: str,
    content: str,
    state: Optional["CxcState"] = None,
    append: bool = True,
    timestamp: bool = True,
) -> Optional[int]:
    """Edit an existing phase comment or create a new one if it doesn't exist.
    
    This consolidates multiple comments per phase into a single editable comment.
    New content is appended (with timestamp) to the existing comment body.
    
    Args:
        issue_number: GitHub issue number
        cxc_id: CXC workflow ID
        phase: Phase name (plan, build, test, review, document, ship)
        content: Content to add/append
        state: Optional CxcState to cache comment IDs
        append: If True, append to existing content; if False, replace
        timestamp: If True, add timestamp to new content
        
    Returns:
        Comment ID if successful, None if failed
    """
    from cxc.integrations.github import (
        update_comment,
        find_comment_id_by_pattern,
        make_issue_comment_and_get_id,
        get_repo_url,
        extract_repo_path,
    )
    from datetime import datetime
    import json
    import subprocess
    
    # Validate phase
    if phase not in PHASE_NAMES:
        print(f"Warning: Unknown phase '{phase}', using anyway")
    
    pattern = get_phase_comment_pattern(cxc_id, phase)
    comment_id = None
    
    # Check state cache first
    if state:
        comment_ids = state.get("github_comment_ids", {})
        if phase in comment_ids:
            comment_id = comment_ids[phase]
    
    # If not in cache, search GitHub
    if not comment_id:
        github_repo_url = get_repo_url()
        repo_path = extract_repo_path(github_repo_url)
        comment_id = find_comment_id_by_pattern(issue_number, pattern, repo_path)
    
    # Format the new content
    if timestamp:
        ts = datetime.now().strftime("%H:%M:%S")
        formatted_content = f"\n\n**[{ts}]** {content}"
    else:
        formatted_content = content
    
    if comment_id:
        # Edit existing comment
        if append:
            # Fetch existing body first
            github_repo_url = get_repo_url()
            repo_path = extract_repo_path(github_repo_url)
            try:
                cmd = [
                    "gh", "api",
                    f"/repos/{repo_path}/issues/comments/{comment_id}",
                    "--jq", ".body"
                ]
                from cxc.integrations.github import get_github_env
                env = get_github_env()
                result = subprocess.run(cmd, capture_output=True, text=True, env=env)
                if result.returncode == 0:
                    existing_body = result.stdout.strip()
                    new_body = existing_body + formatted_content
                else:
                    new_body = pattern + formatted_content
            except:
                new_body = pattern + formatted_content
        else:
            new_body = pattern + formatted_content
        
        success, error = update_comment(comment_id, new_body)
        if success:
            # Update state cache
            if state:
                comment_ids = state.get("github_comment_ids", {})
                comment_ids[phase] = comment_id
                state.update(github_comment_ids=comment_ids)
            return comment_id
        else:
            # Fallback: create new comment if edit fails
            print(f"Warning: Failed to edit comment {comment_id}: {error}, creating new")
    
    # Create new comment
    header = f"**{phase.upper()} PHASE** - CXC ID: `{cxc_id}`\n\n---"
    new_body = f"{pattern}\n\n{header}{formatted_content}"
    
    new_comment_id = make_issue_comment_and_get_id(issue_number, new_body)
    
    if new_comment_id and state:
        # Update state cache
        comment_ids = state.get("github_comment_ids", {})
        comment_ids[phase] = new_comment_id
        state.update(github_comment_ids=comment_ids)
    
    return new_comment_id


def extract_cxc_info(text: str, temp_cxc_id: str) -> CXCExtractionResult:
    """Extract CXC workflow, ID, and model_set from text using classify_cxc agent.
    Returns CXCExtractionResult with workflow_command, cxc_id, and model_set."""

    # Use classify_cxc to extract structured info
    request = AgentTemplateRequest(
        agent_name="cxc_classifier",
        slash_command="/classify_cxc",
        args=[text],
        cxc_id=temp_cxc_id,
    )

    try:

        # <CALLING_AGENT> >> cxc/core/agent.py::execute_template
        response = execute_template(request)  # No logger available in this function
        # </CALLING_AGENT>


        if not response.success:
            print(f"Failed to classify CXC: {response.output}")
            return CXCExtractionResult()  # Empty result

        # Check for structured output first (when --json-schema is used)
        data = None
        if response.structured_output:
            data = response.structured_output
        else:
            # Fallback: Parse JSON response using utility that handles markdown
            try:
                data = parse_json(response.output, dict)
            except ValueError as e:
                print(f"Failed to parse classify_cxc response: {e}")
                return CXCExtractionResult()  # Empty result

        if data:
            cxc_command = data.get("cxc_slash_command", "").replace(
                "/", ""
            )  # Remove slash
            cxc_id = data.get("cxc_id")
            model_set = data.get("model_set", "base")  # Default to "base"

            # Validate command
            if cxc_command and cxc_command in AVAILABLE_CXC_WORKFLOWS:
                return CXCExtractionResult(
                    workflow_command=cxc_command,
                    cxc_id=cxc_id,
                    model_set=model_set
                )

        return CXCExtractionResult()  # Empty result

    except Exception as e:
        print(f"Error calling classify_cxc: {e}")
        return CXCExtractionResult()  # Empty result


def classify_issue(
    issue: GitHubIssue, cxc_id: str, logger: logging.Logger
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
        cxc_id=cxc_id,
    )

    logger.debug(f"Classifying issue: {issue.title}")


    # <CALLING_AGENT> >> cxc/core/agent.py::execute_template
    response = execute_template(request)
    # </CALLING_AGENT>


    logger.debug(
        f"Classification response: {response.model_dump_json(indent=2, by_alias=True)}"
    )

    if not response.success:
        logger.error(f"classify_issue agent failed: {response.output}")
        print_agent_log(cxc_id, AGENT_CLASSIFIER)
        return None, f"Agent failed: {response.output}"

    # Check for structured output first (when --json-schema is used)
    if response.structured_output:
        classification = response.structured_output.get("classification")
        logger.debug(f"classify_issue structured_output: {response.structured_output}")
        if classification in ["/chore", "/bug", "/feature"]:
            return classification, None  # type: ignore
        elif classification == "0":
            logger.error(f"No command selected. Structured output: {response.structured_output}")
            print_agent_log(cxc_id, AGENT_CLASSIFIER)
            return None, f"No command selected. Structured output: {response.structured_output}"
        else:
            logger.error(f"Invalid classification '{classification}' in structured output")
            print_agent_log(cxc_id, AGENT_CLASSIFIER)
            return None, f"Invalid classification '{classification}' in structured output"

    # Fallback: Extract the classification from text response
    output = response.output.strip()
    logger.debug(f"classify_issue raw response ({len(output)} chars): {output}")

    # Look for the classification pattern in the output
    # Claude might add explanation, so we need to extract just the command
    classification_match = re.search(r"(/chore|/bug|/feature|0)", output)

    if classification_match:
        issue_command = classification_match.group(1)
    else:
        issue_command = output

    if issue_command == "0":
        logger.error(f"No command selected. Raw response: {output}")
        print_agent_log(cxc_id, AGENT_CLASSIFIER)
        return None, f"No command selected. Raw response: {output}"

    if issue_command not in ["/chore", "/bug", "/feature"]:
        logger.error(f"Invalid command '{issue_command}' selected. Raw response: {output}")
        print_agent_log(cxc_id, AGENT_CLASSIFIER)
        return None, f"Invalid command '{issue_command}' selected. Raw response: {output}"

    return issue_command, None  # type: ignore


def build_plan(
    issue: GitHubIssue,
    command: str,
    cxc_id: str,
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
        args=[str(issue.number), cxc_id, minimal_issue_json],
        cxc_id=cxc_id,
        working_dir=working_dir,
    )

    logger.debug(
        f"issue_plan_template_request: {issue_plan_template_request.model_dump_json(indent=2, by_alias=True)}"
    )


    # <CALLING_AGENT> >> cxc/core/agent.py::execute_template
    issue_plan_response = execute_template(issue_plan_template_request)
    # </CALLING_AGENT>


    logger.debug(
        f"issue_plan_response: {issue_plan_response.model_dump_json(indent=2, by_alias=True)}"
    )

    return issue_plan_response


def implement_plan(
    plan_file: str,
    cxc_id: str,
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
        cxc_id=cxc_id,
        working_dir=working_dir,
    )

    logger.debug(
        f"implement_template_request: {implement_template_request.model_dump_json(indent=2, by_alias=True)}"
    )


    # <CALLING_AGENT> >> cxc/core/agent.py::execute_template
    implement_response = execute_template(implement_template_request)
    # </CALLING_AGENT>


    logger.debug(
        f"implement_response: {implement_response.model_dump_json(indent=2, by_alias=True)}"
    )

    return implement_response


def generate_branch_name(
    issue: GitHubIssue,
    issue_class: IssueClassSlashCommand,
    cxc_id: str,
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
        args=[issue_type, cxc_id, minimal_issue_json],
        cxc_id=cxc_id,
    )


    # <CALLING_AGENT> >> cxc/core/agent.py::execute_template
    response = execute_template(request)
    # </CALLING_AGENT>


    if not response.success:
        logger.error(f"generate_branch_name agent failed: {response.output}")
        print_agent_log(cxc_id, AGENT_BRANCH_GENERATOR)
        return None, f"Agent failed: {response.output}"

    branch_name = response.output.strip()
    logger.debug(f"generate_branch_name raw response ({len(branch_name)} chars): {branch_name}")
    
    # Strip markdown code fences if present (LLM sometimes wraps output)
    # Pattern consumes ```lang\n (e.g., ```python\n or ```\n)
    import re
    branch_name = re.sub(r'^```[^\n]*\n?', '', branch_name)
    branch_name = re.sub(r'\n?```\s*$', '', branch_name)
    branch_name = branch_name.strip()
    
    if not branch_name:
        logger.error("generate_branch_name returned empty response")
        print_agent_log(cxc_id, AGENT_BRANCH_GENERATOR)
        return None, "Agent returned empty branch name"

    logger.info(f"Generated branch name: {branch_name}")
    return branch_name, None

#! AF: This didn't work (vs keeping classify and generate branch seprarate, so not in unuse atm.) 
def classify_and_generate_branch(
    issue: GitHubIssue,
    cxc_id: str,
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
        args=[cxc_id, minimal_issue_json],
        cxc_id=cxc_id,
    )

    logger.debug(f"Combined classify+branch for issue: {issue.title}")

    # <CALLING_AGENT> >> cxc/core/agent.py::execute_template
    response = execute_template(request)
    # </CALLING_AGENT>

    if not response.success:
        logger.error(f"classify_and_branch agent failed: {response.output}")
        print_agent_log(cxc_id, AGENT_CLASSIFY_AND_BRANCH)
        return None, None, f"Agent failed: {response.output}"

    # Check for structured output first (when --json-schema is used)
    data = None
    if response.structured_output:
        data = response.structured_output
        logger.debug(f"classify_and_branch structured_output: {data}")
    else:
        # Fallback: Parse JSON from text response
        raw_output = response.output
        logger.debug(f"classify_and_branch raw response ({len(raw_output)} chars): {raw_output}")

        # Check for empty response
        if not raw_output or not raw_output.strip():
            logger.error("classify_and_branch returned empty response")
            print_agent_log(cxc_id, AGENT_CLASSIFY_AND_BRANCH)
            return None, None, "Agent returned empty response"

        try:
            data = parse_json(raw_output, dict)
        except ValueError as e:
            logger.error(f"JSON parse failed. Raw response: {raw_output}")
            print_agent_log(cxc_id, AGENT_CLASSIFY_AND_BRANCH)
            return None, None, f"Failed to parse JSON response. Raw output ({len(raw_output)} chars): {raw_output}"

    if not data:
        logger.error("No data from classify_and_branch response")
        return None, None, "No data extracted from response"

    issue_class = data.get("issue_class")
    branch_name = data.get("branch_name")

    if not issue_class or issue_class not in ["/chore", "/bug", "/feature"]:
        logger.error(f"Invalid issue_class '{issue_class}' in response: {data}")
        return None, None, f"Invalid issue_class: '{issue_class}'. Response: {data}"
    
    if not branch_name:
        logger.error(f"No branch_name in response: {data}")
        return None, None, f"No branch_name in response: {data}"

    logger.info(f"Classified as {issue_class}, branch: {branch_name}")
    return issue_class, branch_name, None


def create_commit(
    agent_name: str,
    issue: GitHubIssue,
    issue_class: IssueClassSlashCommand,
    cxc_id: str,
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
        cxc_id=cxc_id,
        working_dir=working_dir,
    )


    # <CALLING_AGENT> >> cxc/core/agent.py::execute_template
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
    state: CxcState,
    logger: logging.Logger,
    working_dir: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Create a pull request for the implemented changes.
    Returns (pr_url, error_message) tuple."""

    # Get plan file from state (may be None for test runs)
    plan_file = state.get("plan_file") or "No plan file (test run)"
    cxc_id = state.get("cxc_id")

    # If we don't have issue data, try to construct minimal data
    if not issue:
        issue_data = state.get("issue", {})
        issue_json = json.dumps(issue_data) if issue_data else "{}"
    elif isinstance(issue, dict):
        # Try to reconstruct as GitHubIssue model which handles datetime serialization
        from cxc.core.data_types import GitHubIssue

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
        args=[branch_name, issue_json, plan_file, cxc_id],
        cxc_id=cxc_id,
        working_dir=working_dir,
    )


    # <CALLING_AGENT> >> cxc/core/agent.py::execute_template
    response = execute_template(request)
    # </CALLING_AGENT>


    if not response.success:
        return None, response.output

    pr_url = response.output.strip()
    logger.info(f"Created pull request: {pr_url}")
    return pr_url, None


def ensure_plan_exists(state: CxcState, issue_number: str) -> str:
    """Find or error if no plan exists for issue.
    Used by isolated build workflows in standalone mode."""
    # Check if plan file is in state
    if state.get("plan_file"):
        return state.get("plan_file")

    # Check current branch
    from cxc.integrations.git_ops import get_current_branch

    branch = get_current_branch()

    # Look for plan in branch name
    if f"-{issue_number}-" in branch:
        # Look for plan file
        plans = glob.glob(f"specs/*{issue_number}*.md")
        if plans:
            return plans[0]

    # No plan found
    raise ValueError(
        f"No plan found for issue {issue_number}. Run cxc plan first."
    )


def ensure_cxc_id(
    issue_number: str,
    cxc_id: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> str:
    """Get CXC ID or create a new one and initialize state.

    Args:
        issue_number: The issue number to find/create CXC ID for
        cxc_id: Optional existing CXC ID to use
        logger: Optional logger instance

    Returns:
        The CXC ID (existing or newly created)
    """
    # If CXC ID provided, check if state exists
    if cxc_id:
        state = CxcState.load(cxc_id, logger)
        if state:
            if logger:
                logger.info(f"Found existing CXC state for ID: {cxc_id}")
            else:
                print(f"Found existing CXC state for ID: {cxc_id}")
            return cxc_id
        # CXC ID provided but no state exists, create state
        state = CxcState(cxc_id)
        state.update(cxc_id=cxc_id, issue_number=issue_number)
        state.save("ensure_cxc_id")
        if logger:
            logger.info(f"Created new CXC state for provided ID: {cxc_id}")
        else:
            print(f"Created new CXC state for provided ID: {cxc_id}")
        return cxc_id

    # No CXC ID provided, create new one with state
    from cxc.core.utils import make_cxc_id

    new_cxc_id = make_cxc_id()
    state = CxcState(new_cxc_id)
    state.update(cxc_id=new_cxc_id, issue_number=issue_number)
    state.save("ensure_cxc_id")
    if logger:
        logger.info(f"Created new CXC ID and state: {new_cxc_id}")
    else:
        print(f"Created new CXC ID and state: {new_cxc_id}")
    return new_cxc_id


def find_existing_branch_for_issue(
    issue_number: str, cxc_id: Optional[str] = None, cwd: Optional[str] = None
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

    # Look for branch with standardized pattern: *-issue-{issue_number}-cxc-{cxc_id}-*
    for branch in branches:
        branch = branch.strip().replace("* ", "").replace("remotes/origin/", "")
        # Check for the standardized pattern
        if f"-issue-{issue_number}-" in branch:
            if cxc_id and f"-cxc-{cxc_id}-" in branch:
                return branch
            elif not cxc_id:
                # Return first match if no cxc_id specified
                return branch

    return None


def find_plan_for_issue(
    issue_number: str, cxc_id: Optional[str] = None
) -> Optional[str]:
    """Find plan file for the given issue number and optional cxc_id.
    Returns path to plan file if found, None otherwise."""
    from cxc.core.config import CxcConfig
    
    config = CxcConfig.load()
    agents_base = config.get_project_artifacts_dir()

    if not agents_base.exists():
        return None

    # If cxc_id is provided, check specific directory first
    if cxc_id:
        plan_path = agents_base / cxc_id / AGENT_PLANNER / "plan.md"
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
    state: CxcState,
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
        from cxc.integrations.git_ops import get_current_branch

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
    cxc_id = state.get("cxc_id")
    existing_branch = find_existing_branch_for_issue(issue_number, cxc_id, cwd=cwd)
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
    issue_command, error = classify_issue(issue, cxc_id, logger)
    if error:
        return "", f"Failed to classify issue: {error}"

    state.update(issue_class=issue_command)

    # Generate branch name
    branch_name, error = generate_branch_name(issue, issue_command, cxc_id, logger)
    if error:
        return "", f"Failed to generate branch name: {error}"

    # Create the branch
    from cxc.integrations.git_ops import create_branch

    success, error = create_branch(branch_name, cwd=cwd)
    if not success:
        return "", f"Failed to create branch: {error}"

    state.update(branch_name=branch_name)
    logger.info(f"Created and checked out new branch: {branch_name}")

    return branch_name, None


def find_spec_file(state: CxcState, logger: logging.Logger) -> Optional[str]:
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
            cxc_id = state.get("cxc_id")

            # Look for spec files matching the pattern
            import glob

            # Use worktree_path if provided, otherwise current directory
            search_dir = worktree_path if worktree_path else os.getcwd()
            pattern = os.path.join(
                search_dir, f"specs/issue-{issue_num}-cxc-{cxc_id}*.md"
            )
            spec_files = glob.glob(pattern)

            if spec_files:
                spec_file = spec_files[0]
                logger.info(f"Found spec file by pattern: {spec_file}")
                return spec_file

    logger.warning("No spec file found")
    return None


def create_and_implement_patch(
    cxc_id: str,
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
    args = [cxc_id, review_change_request]

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
        cxc_id=cxc_id,
        working_dir=working_dir,
    )

    logger.debug(
        f"Patch plan request: {request.model_dump_json(indent=2, by_alias=True)}"
    )


    # <CALLING_AGENT> >> cxc/core/agent.py::execute_template
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


    # <CALLING_AGENT> >> workflow_ops.py::implement_plan >> cxc/core/agent.py::execute_template
    implement_response = implement_plan(
        patch_file_path, cxc_id, logger, agent_name_implementor, working_dir=working_dir
    )
    # </CALLING_AGENT>


    return patch_file_path, implement_response


def build_comprehensive_pr_body(
    state: CxcState,
    issue: Optional[GitHubIssue],
    review_summary: Optional[str] = None,
    test_summary: Optional[str] = None,
    remediation_loops: int = 0,
    logger: Optional[logging.Logger] = None,
) -> str:
    """Build a comprehensive PR body with all phase artifacts.
    
    Args:
        state: CXC state containing workflow data
        issue: GitHub issue data
        review_summary: Optional review summary markdown
        test_summary: Optional test results summary
        remediation_loops: Number of remediation loops executed
        logger: Optional logger
        
    Returns:
        Comprehensive markdown PR body
    """
    cxc_id = state.get("cxc_id", "unknown")
    issue_number = state.get("issue_number", "?")
    plan_file = state.get("plan_file", "")
    issue_class = state.get("issue_class", "/feature")
    all_cxcs = state.get("all_cxcs", [])
    
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
        "cxc_plan_iso": ("📝 Plan", "Created implementation spec"),
        "cxc_build_iso": ("🔨 Build", "Implemented changes"),
        "cxc_test_iso": ("🧪 Test", "Ran test suite"),
        "cxc_review_iso": ("🔍 Review", "Validated implementation"),
        "cxc_document_iso": ("📖 Document", "Updated documentation"),
    }
    
    for phase_id, (phase_name, phase_desc) in phase_map.items():
        if phase_id in all_cxcs:
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
    
    # CXC Tracking
    sections.append("---\n")
    sections.append(f"**CXC ID:** `{cxc_id}`\n")
    sections.append(f"**Phases Completed:** {len([p for p in all_cxcs if p in phase_map])}/5\n")
    
    # Close issue reference
    sections.append(f"\nCloses #{issue_number}")
    
    return "\n".join(sections)


def post_artifact_to_issue(
    issue_number: str,
    cxc_id: str,
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
        cxc_id: CXC workflow ID
        agent_name: Name of the agent posting (e.g., "sdlc_planner")
        title: Title/heading for the artifact (e.g., "📋 Implementation Plan")
        content: The artifact content to post
        file_path: Optional path to the artifact file (shown in summary)
        max_length: Maximum content length before truncation (default 8000)
        collapsible: Whether to wrap in <details> block (default True)
        print_to_terminal: Whether to print full content to terminal (default True)
    """
    from cxc.integrations.github import make_issue_comment
    from cxc.core.utils import print_artifact
    
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
        format_issue_message(cxc_id, agent_name, full_comment)
    )


def post_state_to_issue(
    issue_number: str,
    cxc_id: str,
    state_data: dict,
    title: str = "📋 State",
    print_to_terminal: bool = False,
) -> None:
    """Post workflow state to a GitHub issue as a collapsible comment.
    
    Args:
        issue_number: GitHub issue number
        cxc_id: CXC workflow ID
        state_data: The state dictionary to post
        title: Title for the state comment (e.g., "📋 Final planning state")
        print_to_terminal: Whether to print to terminal (default False - state is verbose)
    """
    from cxc.integrations.github import make_issue_comment
    from cxc.core.utils import print_state_json
    
    # Print to terminal with rich formatting (disabled by default for state)
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
        format_issue_message(cxc_id, "ops", comment)
    )
