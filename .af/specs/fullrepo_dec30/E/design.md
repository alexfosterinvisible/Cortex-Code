# CxC Framework - Architecture and Design Document (Claude)

Version: 1.0.0 | Generated: 2025-12-30 | Approach: Feature-Map Driven

---

## 1. System Overview

### 1.1 High-Level Architecture

```
+------------------+     +------------------+     +------------------+
|   CLI / Trigger  |---->|   CxC Framework  |---->|   Claude Code    |
+------------------+     +------------------+     +------------------+
        |                        |                        |
        v                        v                        v
+------------------+     +------------------+     +------------------+
|  GitHub Issues   |     |   Git Worktrees  |     |  Agent Outputs   |
+------------------+     +------------------+     +------------------+
```

### 1.2 Design Principles

1. **Package-as-Dependency**: CxC is consumed by projects via `uv add`, not cloned into projects
2. **Worktree Isolation**: Each workflow runs in dedicated git worktree for parallel execution
3. **State Persistence**: JSON-based state survives process restarts and enables resumption
4. **Composable Phases**: Each SDLC phase is independent and chainable
5. **Typed Throughout**: Pydantic models for all data structures
6. **CLI-First Integration**: Uses `gh` and `claude` CLIs rather than API clients

### 1.3 Component Diagram

```
                            +------------------------+
                            |       CLI Entry        |
                            |      (cxc/cli.py)      |
                            +------------------------+
                                       |
                    +------------------+------------------+
                    |                  |                  |
                    v                  v                  v
           +---------------+  +----------------+  +----------------+
           |   Workflows   |  |    Triggers    |  |  Integrations  |
           |   (wt/*.py)   |  | (triggers/*.py)|  | (integrations/)|
           +---------------+  +----------------+  +----------------+
                    |                  |                  |
                    +------------------+------------------+
                                       |
                            +------------------------+
                            |         Core           |
                            | (config, state, agent) |
                            +------------------------+
                                       |
                    +------------------+------------------+
                    |                  |                  |
                    v                  v                  v
           +---------------+  +----------------+  +----------------+
           |   GitHub      |  |   Git Repos    |  |  Claude Code   |
           |   (gh CLI)    |  |   (git CLI)    |  |  (claude CLI)  |
           +---------------+  +----------------+  +----------------+
```

---

## 2. Component Design

### 2.1 Core Module (`cxc/core/`)

#### 2.1.1 Configuration (`config.py`)

**Purpose**: Centralized configuration loading and path management.

**Design Decisions**:
- Uses dataclasses for simple configuration objects
- Auto-discovers project root by walking up to find `.cxc.yaml`
- Supports `${CxC_FRAMEWORK}` variable expansion for command paths
- Defaults are minimal - explicit configuration preferred

**Key Classes**:

```python
@dataclass
class PortConfig:
    backend_start: int = 9100
    backend_count: int = 15
    frontend_start: int = 9200
    frontend_count: int = 15

@dataclass
class CxCConfig:
    project_root: Path
    project_id: str
    artifacts_dir: Path
    ports: PortConfig
    source_root: Path
    commands: List[Path]
    app_config: Dict[str, Any]

    @classmethod
    def load(cls, project_root: Optional[Path] = None) -> "CxCConfig"

    def get_project_artifacts_dir(self) -> Path
    def get_agents_dir(self, cxc_id: str) -> Path
    def get_trees_dir(self) -> Path
```

**Model Selection Map**:
```python
SLASH_COMMAND_MODEL_MAP: Final[Dict[SlashCommand, Dict[ModelSet, str]]] = {
    "/classify_issue": {"base": "haiku", "heavy": "sonnet"},
    "/implement": {"base": "sonnet", "heavy": "opus"},
    "/feature": {"base": "sonnet", "heavy": "opus"},
    # ... etc
}
```

#### 2.1.2 State Management (`state.py`)

**Purpose**: Persistent workflow state across process boundaries.

**Design Decisions**:
- Single JSON file per CxC instance
- Core fields filtered on update (prevents state pollution)
- Supports stdin/stdout piping for workflow chaining
- Lazy config loading to avoid circular imports

**Key Class**:

```python
class CxCState:
    STATE_FILENAME = "cxc_state.json"

    def __init__(self, cxc_id: str)
    def update(self, **kwargs)
    def get(self, key: str, default=None)
    def get_working_directory(self) -> str
    def save(self, workflow_step: Optional[str] = None)

    @classmethod
    def load(cls, cxc_id: str, logger=None) -> Optional["CxCState"]

    @classmethod
    def from_stdin(cls) -> Optional["CxCState"]

    def to_stdout(self)
```

**State Schema** (CxCStateData Pydantic model):
```python
class CxCStateData(BaseModel):
    cxc_id: str
    issue_number: Optional[str]
    branch_name: Optional[str]
    plan_file: Optional[str]
    issue_class: Optional[IssueClassSlashCommand]
    worktree_path: Optional[str]
    backend_port: Optional[int]
    frontend_port: Optional[int]
    model_set: Optional[ModelSet] = "base"
    all_cxcs: List[str] = Field(default_factory=list)
```

#### 2.1.3 Agent Execution (`agent.py`)

**Purpose**: Execute Claude Code CLI and handle responses.

**Design Decisions**:
- JSONL streaming output for real-time feedback
- Retry logic with exponential backoff
- Safe environment filtering (only required vars passed)
- Automatic model selection based on slash command and model set

**Key Functions**:

```python
def execute_template(request: AgentTemplateRequest) -> AgentPromptResponse:
    """Execute slash command template with automatic model selection."""

def prompt_claude_code(request: AgentPromptRequest) -> AgentPromptResponse:
    """Execute raw prompt against Claude Code CLI."""

def prompt_claude_code_with_retry(
    request: AgentPromptRequest,
    max_retries: int = 3,
    retry_delays: List[int] = None
) -> AgentPromptResponse:
    """Execute with retry logic for transient failures."""

def get_model_for_slash_command(
    request: AgentTemplateRequest,
    default: str = "sonnet"
) -> str:
    """Select model based on command and state's model_set."""
```

**Execution Flow**:
```
execute_template()
    |
    +-> get_model_for_slash_command()  # Load state, get model_set, lookup command
    |
    +-> Build prompt from slash command + args
    |
    +-> Create output directory from config
    |
    +-> prompt_claude_code_with_retry()
            |
            +-> save_prompt()  # Log prompt to file
            |
            +-> subprocess.run(claude CLI)  # Stream to JSONL file
            |
            +-> parse_jsonl_output()  # Extract result message
            |
            +-> convert_jsonl_to_json()  # Create JSON array file
            |
            +-> Return AgentPromptResponse
```

#### 2.1.4 Data Types (`data_types.py`)

**Purpose**: Typed models for all system data.

**Design Decisions**:
- Pydantic v2 with `populate_by_name = True` for JSON alias support
- Literal types for constrained values (SlashCommand, ModelSet, etc.)
- Separate models for GitHub API responses
- Result models for each workflow output

**Key Types**:

```python
# Constrained literals
IssueClassSlashCommand = Literal["/chore", "/bug", "/feature"]
ModelSet = Literal["base", "heavy"]
SlashCommand = Literal["/classify_issue", "/implement", "/feature", ...]
CxCWorkflow = Literal["cxc_plan_iso", "cxc_sdlc_iso", ...]

# GitHub models
class GitHubUser(BaseModel)
class GitHubLabel(BaseModel)
class GitHubComment(BaseModel)
class GitHubIssue(BaseModel)
class GitHubIssueListItem(BaseModel)

# Agent request/response
class AgentPromptRequest(BaseModel)
class AgentPromptResponse(BaseModel)
class AgentTemplateRequest(BaseModel)
class ClaudeCodeResultMessage(BaseModel)

# Workflow results
class TestResult(BaseModel)
class E2ETestResult(BaseModel)
class ReviewIssue(BaseModel)
class ReviewResult(BaseModel)
class DocumentationResult(BaseModel)
class CxCExtractionResult(BaseModel)
```

#### 2.1.5 Utilities (`utils.py`)

**Purpose**: Shared utility functions.

**Key Functions**:

```python
def make_cxc_id() -> str:
    """Generate 8-character UUID."""
    return str(uuid.uuid4())[:8]

def setup_logger(cxc_id: str, trigger_type: str) -> logging.Logger:
    """Create logger writing to file and console."""

def parse_json(text: str, target_type: Type[T] = None) -> Union[T, Any]:
    """Parse JSON from markdown code blocks."""

def get_safe_subprocess_env() -> Dict[str, str]:
    """Filter environment to safe variables for subprocesses."""

def print_markdown(content: str, title: str = None, ...) -> None:
    """Rich terminal output for markdown content."""

def print_artifact(title: str, content: str, ...) -> None:
    """Print artifact with rich formatting."""
```

---

### 2.2 Integrations Module (`cxc/integrations/`)

#### 2.2.1 GitHub Integration (`github.py`)

**Purpose**: All GitHub operations via `gh` CLI.

**Design Decisions**:
- Uses `gh` CLI (not PyGithub) for simpler auth handling
- Environment-based token with fallback to `gh auth`
- Bot identifier prefix on all comments
- Typed return values using Pydantic models

**Key Functions**:

```python
def fetch_issue(issue_number: str, repo_path: str) -> GitHubIssue
def fetch_open_issues(repo_path: str) -> List[GitHubIssueListItem]
def fetch_issue_comments(repo_path: str, issue_number: int) -> List[Dict]
def make_issue_comment(issue_id: str, comment: str) -> None
def mark_issue_in_progress(issue_id: str) -> None
def approve_pr(pr_number: str, repo_path: str) -> tuple[bool, Optional[str]]
def close_issue(issue_number: str, repo_path: str = None) -> tuple[bool, Optional[str]]
def find_keyword_from_comment(keyword: str, issue: GitHubIssue) -> Optional[GitHubComment]
```

**Bot Loop Prevention**:
```python
CxC_BOT_IDENTIFIER = "[CxC-AGENTS]"

def make_issue_comment(issue_id: str, comment: str) -> None:
    # Ensure comment has CxC_BOT_IDENTIFIER
    if not comment.startswith(CxC_BOT_IDENTIFIER):
        comment = f"{CxC_BOT_IDENTIFIER} {comment}"
    # ... execute gh comment
```

#### 2.2.2 Git Operations (`git_ops.py`)

**Purpose**: Low-level git command execution.

**Key Functions**:

```python
def get_current_branch(cwd: Optional[str] = None) -> str
def create_branch(branch_name: str, cwd: Optional[str] = None) -> Tuple[bool, Optional[str]]
def checkout_branch(branch_name: str, cwd: Optional[str] = None) -> Tuple[bool, Optional[str]]
def push_branch(branch_name: str, cwd: Optional[str] = None) -> Tuple[bool, Optional[str]]
def delete_branch(branch_name: str, cwd: Optional[str] = None) -> Tuple[bool, Optional[str]]
```

#### 2.2.3 Workflow Operations (`workflow_ops.py`)

**Purpose**: Shared high-level operations used by multiple workflows.

**Design Decisions**:
- Agent name constants for consistency
- Available workflows list for validation
- Combined operations for efficiency (classify_and_generate_branch)
- Issue message formatting with session tracking

**Key Functions**:

```python
# Classification and planning
def classify_issue(issue, cxc_id, logger) -> Tuple[Optional[IssueClassSlashCommand], Optional[str]]
def generate_branch_name(issue, issue_class, cxc_id, logger) -> Tuple[Optional[str], Optional[str]]
def classify_and_generate_branch(issue, cxc_id, logger) -> Tuple[Optional[str], Optional[str], Optional[str]]
def build_plan(issue, command, cxc_id, logger, working_dir=None) -> AgentPromptResponse

# Implementation
def implement_plan(plan_file, cxc_id, logger, agent_name=None, working_dir=None) -> AgentPromptResponse
def create_and_implement_patch(cxc_id, change_request, logger, ...) -> Tuple[Optional[str], AgentPromptResponse]

# Git/PR operations
def create_commit(agent_name, issue, issue_class, cxc_id, logger, working_dir) -> Tuple[Optional[str], Optional[str]]
def create_pull_request(branch_name, issue, state, logger, working_dir) -> Tuple[Optional[str], Optional[str]]
def create_or_find_branch(issue_number, issue, state, logger, cwd=None) -> Tuple[str, Optional[str]]

# State and discovery
def ensure_cxc_id(issue_number, cxc_id=None, logger=None) -> str
def ensure_plan_exists(state, issue_number) -> str
def find_existing_branch_for_issue(issue_number, cxc_id=None, cwd=None) -> Optional[str]
def find_plan_for_issue(issue_number, cxc_id=None) -> Optional[str]
def find_spec_file(state, logger) -> Optional[str]

# CxC classification
def extract_cxc_info(text, temp_cxc_id) -> CxCExtractionResult
```

#### 2.2.4 Worktree Operations (`worktree_ops.py`)

**Purpose**: Git worktree lifecycle management.

**Design Decisions**:
- Worktrees stored under `artifacts/{project_id}/trees/`
- Deterministic port allocation from CxC ID hash
- Cleanup of existing worktrees before recreation

**Key Functions**:

```python
def create_worktree(
    branch_name: str,
    cxc_id: str,
    state: CxCState,
    logger: logging.Logger,
    base_branch: str = "main"
) -> Tuple[str, Optional[str]]:
    """Create isolated worktree for workflow."""

def remove_worktree(worktree_path: str, logger: logging.Logger) -> bool:
    """Remove worktree when done."""

def allocate_ports(cxc_id: str, config: CxCConfig) -> Tuple[int, int]:
    """Deterministic port allocation from CxC ID hash."""
```

**Port Allocation Algorithm**:
```python
def allocate_ports(cxc_id: str, config: CxCConfig) -> Tuple[int, int]:
    hash_int = int(hashlib.md5(cxc_id.encode()).hexdigest()[:8], 16)
    backend_port = config.ports.backend_start + (hash_int % config.ports.backend_count)
    frontend_port = config.ports.frontend_start + (hash_int % config.ports.frontend_count)
    return backend_port, frontend_port
```

---

### 2.3 Workflows Module (`cxc/workflows/`)

#### 2.3.1 Workflow Design Pattern

All isolated workflows follow this pattern:

```python
# cxc/workflows/wt/{phase}_iso.py

def run(issue_number: str, cxc_id: str, logger: logging.Logger, ...) -> bool:
    """Execute the {phase} workflow phase."""

    # 1. Load state
    state = CxCState.load(cxc_id, logger)
    if not state:
        state = CxCState(cxc_id)
        state.update(issue_number=issue_number)

    # 2. Get working directory (worktree or project root)
    working_dir = state.get_working_directory()

    # 3. Execute phase-specific logic
    # ... phase implementation ...

    # 4. Update and save state
    state.update(key=value)
    state.save(f"{phase}_iso")

    # 5. Return success/failure
    return success

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument("issue_number")
    parser.add_argument("cxc_id")
    # ... other args ...

    args = parser.parse_args()

    # Setup logger
    logger = setup_logger(args.cxc_id, f"wt_{phase}_iso")

    # Run workflow
    success = run(args.issue_number, args.cxc_id, logger, ...)

    sys.exit(0 if success else 1)
```

#### 2.3.2 Planning Workflow (`plan_iso.py`)

**Flow**:
```
main()
    |
    +-> ensure_cxc_id()
    |
    +-> fetch_issue()
    |
    +-> classify_and_generate_branch()
    |       |
    |       +-> Returns (issue_class, branch_name, error)
    |
    +-> create_worktree(branch_name)
    |       |
    |       +-> allocate_ports()
    |       +-> git worktree add
    |
    +-> build_plan(issue, issue_class, working_dir=worktree)
    |       |
    |       +-> execute_template(/feature|/bug|/chore)
    |
    +-> create_commit(plan changes)
    |
    +-> push_branch()
    |
    +-> create_pull_request()
    |
    +-> post_artifact_to_issue(plan content)
    |
    +-> save state
```

#### 2.3.3 Build Workflow (`build_iso.py`)

**Flow**:
```
main()
    |
    +-> load state (must exist)
    |
    +-> ensure_plan_exists()
    |
    +-> implement_plan(plan_file)
    |       |
    |       +-> execute_template(/implement)
    |
    +-> create_commit(implementation)
    |
    +-> push_branch()
    |
    +-> save state
```

#### 2.3.4 Test Workflow (`test_iso.py`)

**Flow**:
```
main()
    |
    +-> load state
    |
    +-> run_tests()
    |       |
    |       +-> execute_template(/test)
    |       +-> parse_json(results)
    |       |
    |       +-> if failures and retries_left:
    |       |       +-> execute_template(/resolve_failed_test)
    |       |       +-> retry tests
    |       |
    |       +-> if not skip_e2e:
    |               +-> execute_template(/test_e2e)
    |               +-> if failures:
    |                       +-> execute_template(/resolve_failed_e2e_test)
    |
    +-> commit test fixes if any
    |
    +-> push_branch()
    |
    +-> save state
```

#### 2.3.5 Review Workflow (`review_iso.py`)

**Flow**:
```
main()
    |
    +-> load state
    |
    +-> find_spec_file()
    |
    +-> run_review()
    |       |
    |       +-> execute_template(/review)
    |       +-> parse ReviewResult
    |       +-> capture screenshots
    |       +-> upload screenshots to R2 (optional)
    |
    +-> if blockers and not skip_resolution:
    |       +-> for each blocker:
    |               +-> create_and_implement_patch()
    |               +-> re-run review
    |
    +-> post_review_to_issue()
    |
    +-> save state
```

#### 2.3.6 Document Workflow (`document_iso.py`)

**Flow**:
```
main()
    |
    +-> load state
    |
    +-> run_documentation()
    |       |
    |       +-> execute_template(/document)
    |       +-> parse DocumentationResult
    |
    +-> create_commit(docs)
    |
    +-> push_branch()
    |
    +-> post_docs_to_issue()
    |
    +-> save state
```

#### 2.3.7 Ship Workflow (`ship_iso.py`)

**Flow**:
```
main()
    |
    +-> load state
    |
    +-> get PR number from branch
    |
    +-> approve_pr()
    |
    +-> merge PR (gh pr merge)
    |
    +-> close_issue()
    |
    +-> post_ship_comment()
    |
    +-> save state
```

#### 2.3.8 SDLC Orchestration (`sdlc_iso.py`)

**Flow**:
```
main()
    |
    +-> plan_iso.run()
    |       |
    |       +-> Returns: branch_name, plan_file in state
    |
    +-> build_iso.run()
    |       |
    |       +-> Uses plan_file from state
    |
    +-> test_iso.run()
    |       |
    |       +-> Uses worktree_path from state
    |
    +-> review_iso.run()
    |       |
    |       +-> Uses spec from state
    |
    +-> document_iso.run()
    |
    +-> (ZTE only) ship_iso.run()
```

---

### 2.4 Triggers Module (`cxc/triggers/`)

#### 2.4.1 Webhook Trigger (`trigger_webhook.py`)

**Purpose**: FastAPI server for GitHub webhook events.

**Design**:
```python
app = FastAPI()

@app.post("/webhook")
async def handle_webhook(request: Request):
    payload = await request.json()

    # Parse event type
    event_type = request.headers.get("X-GitHub-Event")

    if event_type == "issue_comment":
        # Extract comment body
        comment = payload["comment"]["body"]
        issue_number = str(payload["issue"]["number"])

        # Skip bot comments
        if CxC_BOT_IDENTIFIER in comment:
            return {"status": "skipped", "reason": "bot_comment"}

        # Extract CxC command
        result = extract_cxc_info(comment, make_cxc_id())

        if result.has_workflow:
            # Launch workflow async
            background_tasks.add_task(
                run_workflow,
                result.workflow_command,
                issue_number,
                result.cxc_id,
                result.model_set
            )

    return {"status": "ok"}
```

#### 2.4.2 Cron Trigger (`trigger_cron.py`)

**Purpose**: Polling-based workflow triggering.

**Design**:
```python
def poll_for_issues():
    """Check for new/updated issues and trigger workflows."""
    config = CxCConfig.load()
    issues = fetch_open_issues(config.project_id)

    for issue in issues:
        # Check for trigger labels/keywords
        if should_trigger(issue):
            run_workflow("cxc_sdlc_iso", str(issue.number))

def main():
    schedule.every(5).minutes.do(poll_for_issues)

    while True:
        schedule.run_pending()
        time.sleep(1)
```

---

### 2.5 Command Templates (`commands/`)

**Purpose**: Markdown templates for Claude Code slash commands.

**Template Structure**:
```markdown
# /command_name

[Instructions for Claude Code agent]

## Arguments

$ARGUMENTS

## Expected Output

[What the agent should produce]
```

**Argument Substitution**:
```python
def build_prompt(template: str, args: List[str]) -> str:
    return template.replace("$ARGUMENTS", " ".join(args))
```

**Command Categories**:

1. **Classification**: `/classify_issue`, `/classify_cxc`, `/classify_and_branch`
2. **Planning**: `/feature`, `/bug`, `/chore`, `/patch`
3. **Execution**: `/implement`, `/test`, `/test_e2e`
4. **Remediation**: `/resolve_failed_test`, `/resolve_failed_e2e_test`
5. **Output**: `/commit`, `/pull_request`, `/document`, `/review`
6. **Setup**: `/install_worktree`, `/cleanup_worktrees`

---

## 3. Data Flow

### 3.1 State Flow Through SDLC

```
[Initial State]
    cxc_id: "abc12345"
    issue_number: "42"

        |
        v (plan_iso)

[After Planning]
    + branch_name: "feature-issue-42-cxc-abc12345-add-auth"
    + plan_file: "specs/issue-42-cxc-abc12345-add-auth.md"
    + issue_class: "/feature"
    + worktree_path: "/path/to/artifacts/org/repo/trees/abc12345"
    + backend_port: 9105
    + frontend_port: 9205

        |
        v (build_iso)

[After Build]
    + all_cxcs: ["cxc_plan_iso", "cxc_build_iso"]

        |
        v (test_iso)

[After Test]
    + all_cxcs: [..., "cxc_test_iso"]

        |
        v (review_iso)

[After Review]
    + all_cxcs: [..., "cxc_review_iso"]

        |
        v (document_iso)

[After Document]
    + all_cxcs: [..., "cxc_document_iso"]
```

### 3.2 Agent Execution Flow

```
[AgentTemplateRequest]
    agent_name: "sdlc_planner"
    slash_command: "/feature"
    args: ["42", "abc12345", "{...issue_json...}"]
    cxc_id: "abc12345"

        |
        v (execute_template)

[Model Selection]
    Load state -> model_set = "base"
    Lookup /feature in SLASH_COMMAND_MODEL_MAP
    Return "sonnet"

        |
        v (prompt_claude_code)

[CLI Execution]
    claude -p "/feature 42 abc12345 {...}" \
           --model sonnet \
           --output-format stream-json \
           --verbose \
           --dangerously-skip-permissions

        |
        v (parse_jsonl_output)

[AgentPromptResponse]
    output: "Plan created at specs/issue-42-cxc-abc12345-add-auth.md"
    success: true
    session_id: "session_xyz"
    retry_code: RetryCode.NONE
```

---

## 4. Error Handling

### 4.1 Retry Codes

```python
class RetryCode(str, Enum):
    CLAUDE_CODE_ERROR = "claude_code_error"      # CLI execution failed
    TIMEOUT_ERROR = "timeout_error"               # Command timed out
    EXECUTION_ERROR = "execution_error"           # Exception during run
    ERROR_DURING_EXECUTION = "error_during_execution"  # Agent hit error
    NONE = "none"                                 # No retry needed
```

### 4.2 Retry Strategy

```python
# Default delays: [1, 3, 5] seconds
for attempt in range(max_retries + 1):
    response = prompt_claude_code(request)

    if response.success or response.retry_code == RetryCode.NONE:
        return response

    if response.retry_code in RETRYABLE_CODES:
        if attempt < max_retries:
            time.sleep(retry_delays[attempt])
            continue

    return response  # Give up
```

### 4.3 Error Propagation

- Workflow functions return `Tuple[result, Optional[str]]` for errors
- Non-zero exit codes from CLI indicate failure
- State is always saved, even on failure (for debugging)
- GitHub comments posted for major failures

---

## 5. Security Design

### 5.1 Environment Variable Filtering

```python
def get_safe_subprocess_env() -> Dict[str, str]:
    """Only pass required env vars to subprocesses."""
    return {
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "GITHUB_PAT": os.getenv("GITHUB_PAT"),
        "CLAUDE_CODE_PATH": os.getenv("CLAUDE_CODE_PATH", "claude"),
        "HOME": os.getenv("HOME"),
        "PATH": os.getenv("PATH"),
        # ... minimal set
    }
```

### 5.2 Bot Loop Prevention

```python
CxC_BOT_IDENTIFIER = "[CxC-AGENTS]"

def make_issue_comment(issue_id: str, comment: str) -> None:
    if not comment.startswith(CxC_BOT_IDENTIFIER):
        comment = f"{CxC_BOT_IDENTIFIER} {comment}"
    # ... post comment

def handle_webhook(payload):
    comment = payload["comment"]["body"]
    if CxC_BOT_IDENTIFIER in comment:
        return {"status": "skipped"}  # Don't process our own comments
```

### 5.3 Credential Handling

- API keys in `.env` file (gitignored)
- GitHub token optional (uses `gh auth` fallback)
- No secrets in state files
- No secrets in agent prompts

---

## 6. Extension Points

### 6.1 Custom Commands

Projects can add custom slash commands:

```yaml
# .cxc.yaml
commands:
  - "${CxC_FRAMEWORK}/commands"  # Framework commands
  - ".claude/commands"            # Project commands
```

### 6.2 Model Configuration

Override model selection:

```python
# Custom model map in consuming project
from cxc.core.config import SLASH_COMMAND_MODEL_MAP

SLASH_COMMAND_MODEL_MAP["/my_custom_command"] = {
    "base": "sonnet",
    "heavy": "opus"
}
```

### 6.3 Workflow Hooks

Inject custom logic via state:

```python
# In consuming project
state = CxCState.load(cxc_id)
state.update(custom_config={"my_setting": True})
state.save()

# In custom workflow
custom_config = state.get("custom_config", {})
if custom_config.get("my_setting"):
    # Custom behavior
```

---

## 7. Performance Considerations

### 7.1 Optimizations

1. **Combined LLM Calls**: `classify_and_generate_branch()` is 2x faster than separate calls
2. **Haiku for Classification**: Fast model for simple classification tasks
3. **JSONL Streaming**: Output written directly to file (no memory accumulation)
4. **Lazy State Loading**: Config loaded once per workflow run

### 7.2 Bottlenecks

1. **LLM Latency**: Most time spent in Claude Code execution
2. **Git Operations**: Clone/checkout can be slow for large repos
3. **Screenshot Upload**: R2 upload adds latency to review phase

### 7.3 Parallelization

- Multiple workflows can run in parallel (worktree isolation)
- Each gets unique ports
- State files are per-CxC-ID (no conflicts)

---

## 8. Testing Strategy

### 8.1 Test Categories

| Category     | Location                          | Purpose                    |
|--------------|-----------------------------------|----------------------------|
| Unit         | tests/unit/                       | Individual functions       |
| Integration  | tests/integration/                | Workflow combinations      |
| Regression   | tests/regression/                 | Prevent regressions        |

### 8.2 Key Fixtures

```python
# tests/conftest.py

@pytest.fixture
def tmp_project_dir(tmp_path):
    """Create temporary project with .cxc.yaml and .env"""

@pytest.fixture
def mock_cxc_config(tmp_project_dir):
    """Pre-configured CxCConfig for tests"""

@pytest.fixture
def mock_subprocess_run(mocker):
    """Mock git/gh/claude CLI calls"""

@pytest.fixture
def mock_claude_success(mocker):
    """Mock successful agent responses"""
```

### 8.3 Test Markers

```python
@pytest.mark.unit          # Fast, no external deps
@pytest.mark.integration   # May use filesystem
@pytest.mark.requires_api  # Needs real API keys
```

---

## 9. Deployment

### 9.1 Package Installation

```bash
# From consuming project
uv add ../cxc-framework      # Local development
uv add git+https://...       # Production
```

### 9.2 Configuration

```yaml
# .cxc.yaml in consuming project
project_id: "org/repo"
artifacts_dir: "./artifacts"
source_root: "./src"
ports:
  backend_start: 9100
  frontend_start: 9200
commands:
  - "${CxC_FRAMEWORK}/commands"
  - ".claude/commands"
```

### 9.3 Required Setup

1. `.cxc.yaml` configuration
2. `.env` with API keys
3. Git repository with remote
4. GitHub CLI authenticated (`gh auth login`)
5. Claude Code CLI installed
