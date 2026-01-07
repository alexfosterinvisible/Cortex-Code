# CxC Framework Design Specification (Claude)

**Version:** 1.0.0
**Date:** 2025-12-30
**Document Type:** Architecture and Design

---

## 1. System Overview

### 1.1 Architecture Philosophy

CxC Framework follows a **contract-driven, workflow-orchestrated architecture** where:

1. **Workflows are the primary unit of execution** - Each workflow (plan, build, test, review, document, ship) is a self-contained module
2. **State is the communication mechanism** - Workflows communicate via persistent JSON state
3. **Agents are the implementation engine** - Claude Code agents execute tasks via slash command templates
4. **Worktrees provide isolation** - Each workflow instance runs in its own git worktree

### 1.2 Component Diagram

```
                                    +------------------+
                                    |   GitHub Issue   |
                                    +--------+---------+
                                             |
                              +--------------v--------------+
                              |         CLI (cxc)           |
                              |     cxc/cli.py              |
                              +--------------+--------------+
                                             |
              +------------------------------v------------------------------+
              |                     Workflow Router                         |
              |  plan -> plan_iso.py  |  build -> build_iso.py  |  etc.    |
              +------------------------------+------------------------------+
                                             |
         +-----------------------------------v-----------------------------------+
         |                         Workflow Execution                           |
         +------+--------+--------+--------+--------+--------+---------+--------+
                |        |        |        |        |        |         |
           +----v----+   |   +----v----+   |   +----v----+   |   +-----v-----+
           |  plan   |   |   |  build  |   |   |  test   |   |   |  review   |
           | _iso.py |   |   | _iso.py |   |   | _iso.py |   |   |  _iso.py  |
           +---------+   |   +---------+   |   +---------+   |   +-----------+
                         |                 |                 |
                    +----v----+       +----v----+       +----v-----+
                    |document |       |  ship   |       |  patch   |
                    | _iso.py |       | _iso.py |       | _iso.py  |
                    +---------+       +---------+       +----------+
                         |
         +---------------v---------------+
         |        Core Services          |
         +------+--------+-------+-------+
                |        |       |
           +----v----+   |  +----v----+
           | Config  |   |  |  State  |
           +----+----+   |  +----+----+
                |        |       |
                +--------v-------+
                |     Agent      |
                +--------+-------+
                         |
         +---------------v---------------+
         |       Integrations            |
         +------+--------+-------+-------+
                |        |       |
           +----v----+ +-v-----+ +----v-------+
           | GitHub  | |  Git  | | Worktree   |
           +---------+ +-------+ +------------+
```

---

## 2. Package Structure

### 2.1 Directory Layout

```
cxc/
├── __init__.py
├── cli.py                          # CLI entry point and router
├── core/
│   ├── __init__.py
│   ├── config.py                   # CxCConfig - configuration loading
│   ├── state.py                    # CxCState - workflow state persistence
│   ├── agent.py                    # Claude Code agent execution
│   ├── data_types.py               # Pydantic models and type definitions
│   └── utils.py                    # Logging, ID generation, parsing
├── integrations/
│   ├── __init__.py
│   ├── github.py                   # GitHub API via gh CLI
│   ├── git_ops.py                  # Git operations (commit, push, PR)
│   ├── workflow_ops.py             # Shared workflow operations
│   ├── worktree_ops.py             # Git worktree management
│   └── r2_uploader.py              # Cloudflare R2 screenshot upload
├── workflows/
│   ├── __init__.py
│   ├── wt/                         # Worktree-isolated workflows (primary)
│   │   ├── __init__.py
│   │   ├── plan_iso.py
│   │   ├── build_iso.py
│   │   ├── test_iso.py
│   │   ├── review_iso.py
│   │   ├── document_iso.py
│   │   ├── ship_iso.py
│   │   ├── patch_iso.py
│   │   ├── sdlc_iso.py
│   │   └── sdlc_zte_iso.py
│   └── reg/                        # Regular workflows (deprecated)
│       └── ...
└── triggers/
    ├── __init__.py
    ├── trigger_webhook.py          # FastAPI GitHub webhook
    └── trigger_cron.py             # Polling-based trigger

commands/                           # Slash command templates
├── feature.md
├── bug.md
├── chore.md
├── patch.md
├── implement.md
├── review.md
├── document.md
├── commit.md
├── classify_issue.md
├── classify_and_branch.md
├── generate_branch_name.md
├── resolve_failed_test.md
├── resolve_failed_e2e_test.md
├── install_worktree.md
└── examples/
    ├── test.md
    ├── test_e2e.md
    └── ...

tests/
├── conftest.py                     # Shared fixtures
├── unit/
│   ├── test_config.py
│   ├── test_state.py
│   ├── test_cli.py
│   ├── test_agent.py
│   └── ...
└── integration/
    └── ...
```

---

## 3. Core Module Design

### 3.1 Configuration (config.py)

```python
@dataclass
class PortConfig:
    """Port allocation configuration."""
    backend_start: int = 9100
    backend_count: int = 15
    frontend_start: int = 9200
    frontend_count: int = 15


@dataclass
class CxCConfig:
    """Immutable configuration loaded from .cxc.yaml."""
    project_root: Path
    project_id: str
    artifacts_dir: Path
    source_root: Path
    ports: PortConfig
    commands: List[Path]
    app_config: Dict[str, Any]

    @classmethod
    def load(cls, start_path: Path = None) -> "CxCConfig":
        """
        Load configuration from .cxc.yaml.

        Resolution order:
        1. If start_path provided, look there
        2. Walk up from cwd to find .cxc.yaml
        3. Use defaults if not found
        """
        ...

    def get_project_artifacts_dir(self) -> Path:
        """Returns: artifacts/{org}/{repo}"""
        ...

    def get_agents_dir(self, cxc_id: str) -> Path:
        """Returns: artifacts/{org}/{repo}/{cxc_id}"""
        ...

    def get_trees_dir(self) -> Path:
        """Returns: artifacts/{org}/{repo}/trees"""
        ...

    def get_app_source_dir(self, appname: str) -> Path:
        """Returns: source_root/{appname}"""
        ...
```

**Design Decisions:**
1. **Immutable dataclass** - Config is loaded once and never modified
2. **Directory walking** - Supports nested project structures
3. **Graceful fallback** - Missing config uses sensible defaults
4. **Variable expansion** - `${CxC_FRAMEWORK}` expanded in command paths

### 3.2 State (state.py)

```python
class CxCState:
    """
    Persistent workflow state manager.

    State is stored as JSON at:
    artifacts/{org}/{repo}/{cxc_id}/cxc_state.json

    Core fields (persisted):
    - cxc_id: str
    - issue_number: Optional[str]
    - branch_name: Optional[str]
    - plan_file: Optional[str]
    - issue_class: Optional[str]
    - worktree_path: Optional[str]
    - backend_port: Optional[int]
    - frontend_port: Optional[int]
    - model_set: Optional[str]
    - all_cxcs: List[str]
    """

    def __init__(self, cxc_id: str):
        """Create new state with cxc_id."""
        if not cxc_id:
            raise ValueError("cxc_id is required")
        ...

    def update(self, **kwargs) -> None:
        """Update state fields. Non-core fields filtered out."""
        ...

    def get(self, key: str, default: Any = None) -> Any:
        """Get field value with optional default."""
        ...

    def append_cxc_id(self, workflow_id: str) -> None:
        """Add workflow step to all_cxcs (deduplicated)."""
        ...

    def save(self, workflow_step: str = None) -> None:
        """Persist state to JSON file. Creates directories."""
        ...

    @classmethod
    def load(cls, cxc_id: str, logger: Logger = None) -> Optional["CxCState"]:
        """Load existing state or return None."""
        ...

    @classmethod
    def from_stdin(cls) -> Optional["CxCState"]:
        """Parse state from piped stdin (for chaining)."""
        ...

    def to_stdout(self) -> None:
        """Output state as JSON to stdout."""
        ...

    def get_working_directory(self) -> str:
        """Returns worktree_path if set, else project root."""
        ...

    def get_state_path(self) -> str:
        """Returns full path to state JSON file."""
        ...
```

**Design Decisions:**
1. **Field filtering** - Only core fields persisted to prevent state bloat
2. **Pydantic validation** - `CxCStateData` schema validated on save
3. **Workflow tracking** - `all_cxcs` tracks which workflows have run
4. **Piping support** - `from_stdin`/`to_stdout` enables workflow chaining

### 3.3 Agent (agent.py)

```python
def execute_template(request: AgentTemplateRequest) -> AgentPromptResponse:
    """
    Execute a slash command template via Claude Code.

    Process:
    1. Load template from commands directory
    2. Replace placeholders ($ARGUMENTS, $1, $2, etc.)
    3. Execute Claude Code CLI
    4. Parse JSONL response
    5. Return structured response

    Model selection:
    - Heavy: /implement, /document, /feature, /bug, /chore, /patch
    - Base: all others
    """
    ...


def _load_template(command: str, commands_dirs: List[Path]) -> str:
    """
    Find and load command template.

    Searches commands directories in order, returns first match.
    Template filename: {command}.md (without leading slash)
    """
    ...


def _substitute_args(template: str, args: List[str]) -> str:
    """
    Replace template placeholders.

    - $ARGUMENTS -> args joined by space
    - $1, $2, $3... -> positional args
    """
    ...


def _execute_claude_code(prompt: str, working_dir: str, model: str) -> str:
    """
    Execute Claude Code CLI and return JSONL output.

    Command: claude --print -p "{prompt}" --model {model}
    Working directory: working_dir or cwd
    """
    ...


def _parse_jsonl_response(jsonl: str) -> AgentPromptResponse:
    """
    Parse JSONL output to structured response.

    Looks for final 'result' type message.
    Extracts: success, result, duration, cost
    """
    ...
```

**Design Decisions:**
1. **Template-based prompts** - Commands are markdown files, not hardcoded
2. **Model routing** - Complex tasks get heavier model automatically
3. **Prompt logging** - All prompts saved to artifacts for debugging
4. **Structured output** - Always returns `AgentPromptResponse`

---

## 4. Workflow Design

### 4.1 Workflow Lifecycle

```
                  +------------------+
                  |  Load .env       |
                  +--------+---------+
                           |
                  +--------v---------+
                  |  Parse CLI args  |
                  +--------+---------+
                           |
                  +--------v---------+
                  | ensure_cxc_id()  |
                  +--------+---------+
                           |
                  +--------v---------+
                  |  Load state      |
                  +--------+---------+
                           |
                  +--------v---------+
                  | Validate prereqs |
                  +--------+---------+
                           |
                  +--------v---------+
                  | Execute workflow |
                  |    (phases)      |
                  +--------+---------+
                           |
                  +--------v---------+
                  |  Save state      |
                  +--------+---------+
                           |
                  +--------v---------+
                  | Finalize git ops |
                  +------------------+
```

### 4.2 Plan Workflow Design

```python
def main():
    """
    Plan workflow: GitHub issue -> Worktree + Plan file + PR

    Phases:
    1. Initialize: Load env, parse args, ensure CxC ID
    2. Fetch: Get issue details from GitHub
    3. Classify: Determine issue type (/feature, /bug, /chore)
    4. Branch: Generate branch name
    5. Worktree: Create isolated git worktree
    6. Setup: Configure worktree environment (ports, deps)
    7. Plan: Execute planning command template
    8. Commit: Commit plan to branch
    9. Push: Push and create/update PR
    10. Report: Post status to GitHub issue
    """
```

**Worktree Setup Sequence:**
```
1. Calculate deterministic ports from cxc_id hash
2. Check port availability, find alternatives if busy
3. Create worktree at: artifacts/{org}/{repo}/trees/{cxc_id}
4. Create .ports.env with PORT configuration
5. Copy .env files from parent repo
6. Copy and update MCP config (absolute paths)
7. Install dependencies (uv sync, bun install)
8. Reset database if applicable
```

### 4.3 Test Workflow Design

```python
class TestWorkflow:
    """
    Test workflow with resolution retry logic.

    Unit Test Loop (max 4 attempts):
    1. Run /test command
    2. Parse TestResult JSON
    3. If failures:
       a. For each failed test: run /resolve_failed_test
       b. If any resolved: go to step 1
       c. If none resolved: break
    4. If all pass: done

    E2E Test Loop (max 2 attempts):
    Same pattern with /test_e2e and /resolve_failed_e2e_test
    """
```

**Test Result Flow:**
```
    +-------------+
    |  Run Tests  |
    +------+------+
           |
    +------v------+
    | Parse JSON  |
    +------+------+
           |
    +------v------+
    | All Pass?   +--Yes--> Done
    +------+------+
           |No
    +------v------+
    | Max Retries?+--Yes--> Report + Exit
    +------+------+
           |No
    +------v------+
    | Resolve     |
    | Each Failure|
    +------+------+
           |
    +------v------+
    | Any Fixed?  +--No--> Report + Exit
    +------+------+
           |Yes
           +---> Run Tests
```

### 4.4 Review Workflow Design

```python
class ReviewWorkflow:
    """
    Review workflow: Spec validation with visual proof.

    Phases:
    1. Find spec file from state
    2. Run /review command
    3. Parse ReviewResult JSON
    4. Upload screenshots to R2
    5. If blockers found and not skipped:
       a. Create patch plan for each blocker
       b. Implement patches
       c. Retry review (max 3 attempts)
    6. Post results to issue
    7. Update PR body with summary
    """
```

**Review Severity Levels:**
| Severity     | Blocks Release? | Action                    |
|:-------------|:----------------|:--------------------------|
| `skippable`  | No              | Log and continue          |
| `tech_debt`  | No              | Log for future work       |
| `blocker`    | Yes             | Attempt resolution        |

### 4.5 Ship Workflow Design

```python
class ShipWorkflow:
    """
    Ship workflow: Final validation and merge.

    Preconditions (all must be populated):
    - cxc_id, issue_number, branch_name
    - plan_file, issue_class, worktree_path
    - backend_port, frontend_port

    Merge Sequence:
    1. Validate state completeness
    2. Validate worktree exists
    3. Approve PR (via gh pr review)
    4. Fetch latest from origin
    5. Checkout main
    6. Pull latest main
    7. Merge feature branch (--no-ff)
    8. Push to origin/main
    9. Close issue
    10. Restore original branch
    """
```

**Merge Strategy:**
- Uses `--no-ff` to preserve commit history
- Merge happens in main repo, not worktree
- Original branch restored after merge
- Continues on PR approval failure

---

## 5. Integration Design

### 5.1 GitHub Integration

**Design Principle:** Use `gh` CLI rather than REST API for simpler authentication.

```python
def fetch_issue(issue_number: str, repo_path: str) -> GitHubIssue:
    """
    Fetch issue via: gh issue view {number} -R {repo} --json ...

    Fields fetched:
    - number, title, body, state
    - author, assignees, labels
    - milestone, comments
    - createdAt, updatedAt, closedAt
    - url
    """
    ...


def make_issue_comment(issue_number: str, body: str) -> bool:
    """
    Post comment via: gh issue comment {number} --body {body}

    Returns True on success, False on failure.
    """
    ...


def get_repo_url() -> str:
    """
    Resolution order:
    1. GITHUB_REPO_URL environment variable
    2. git remote get-url origin

    Raises ValueError if neither available.
    """
    ...
```

### 5.2 Git Operations

```python
def commit_changes(message: str, cwd: str = None) -> Tuple[bool, Optional[str]]:
    """
    Commit sequence:
    1. git add -A
    2. git commit -m "{message}"

    Returns (success, error_message)
    """
    ...


def finalize_git_operations(state: CxCState, logger: Logger, cwd: str = None):
    """
    Finalization sequence:
    1. Get current branch
    2. Push to origin with upstream tracking
    3. Check if PR exists
    4. Create PR if not exists, update if exists
    5. Post PR link to issue
    """
    ...
```

### 5.3 Worktree Operations

**Port Allocation Algorithm:**
```python
def get_ports_for_cxc(cxc_id: str) -> Tuple[int, int]:
    """
    Deterministic port allocation from CxC ID.

    Algorithm:
    1. Hash cxc_id with MD5
    2. Take first 8 hex chars as integer
    3. backend_offset = hash_int % backend_count
    4. frontend_offset = hash_int % frontend_count
    5. Return (backend_start + offset, frontend_start + offset)

    This ensures same cxc_id always gets same ports.
    """
```

**Worktree Creation:**
```python
def create_worktree(cxc_id: str, branch_name: str, logger: Logger) -> Tuple[str, Optional[str]]:
    """
    Create isolated worktree.

    Steps:
    1. Calculate worktree path: trees/{cxc_id}
    2. Create branch if not exists
    3. git worktree add {path} {branch}
    4. Return (path, error)

    Branch handling:
    - If branch exists remotely: checkout
    - If new branch: create from current HEAD
    """
```

---

## 6. Command Template Design

### 6.1 Template Structure

```markdown
# Command Title

Short description of what this command does.

## VARIABLES

var1: $1
var2: $2
complex_var: $ARGUMENTS

## INSTRUCTIONS

- Step-by-step instructions for the agent
- Reference relevant files with [path/to/file]
- Include constraints and requirements

## RELEVANT_FILES

Focus on:
- [file1.py] - Description
- [file2.py] - Description

## FORMAT or REPORT

Expected output format or reporting instructions.
```

### 6.2 Variable Substitution

| Placeholder    | Replaced With                      |
|:---------------|:-----------------------------------|
| `$ARGUMENTS`   | All args joined by space           |
| `$1`           | First positional argument          |
| `$2`           | Second positional argument         |
| `$3`, `$4`...  | Subsequent positional arguments    |

### 6.3 Planning Command Templates

**Common Structure:**
```markdown
## PLAN_FORMAT

# {Type}: <name>

## Metadata
issue_number: `{issue_number}`
cxc_id: `{cxc_id}`
issue_json: `{issue_json}`

## Description
<detailed description>

## Relevant Files
<files to modify>

## Step by Step Tasks
### Step 1: <action>
- <details>

## Validation Commands
- `<command>` - Description

## Notes
<additional context>
```

---

## 7. State Machine

### 7.1 Workflow State Transitions

```
State Field      | Workflow that sets it
-----------------|----------------------
cxc_id           | ensure_cxc_id (first run)
issue_number     | ensure_cxc_id
issue_class      | plan_iso (classify_and_branch)
branch_name      | plan_iso (classify_and_branch)
worktree_path    | plan_iso (create_worktree)
backend_port     | plan_iso (port allocation)
frontend_port    | plan_iso (port allocation)
plan_file        | plan_iso (build_plan)
model_set        | webhook trigger (optional)
all_cxcs         | each workflow (append)
```

### 7.2 SDLC Pipeline State Flow

```
plan_iso
  |
  +-> issue_class = "/feature"
  +-> branch_name = "feat-issue-42-cxc-abc123-..."
  +-> worktree_path = ".../trees/abc123"
  +-> backend_port = 9105
  +-> frontend_port = 9205
  +-> plan_file = "specs/issue-42-cxc-abc123-..."
  +-> all_cxcs = ["cxc_plan_iso"]
  |
build_iso
  |
  +-> all_cxcs = ["cxc_plan_iso", "cxc_build_iso"]
  |
test_iso
  |
  +-> all_cxcs += "cxc_test_iso"
  |
review_iso
  |
  +-> all_cxcs += "cxc_review_iso"
  |
document_iso
  |
  +-> all_cxcs += "cxc_document_iso"
  |
ship_iso (ZTE only)
  |
  +-> all_cxcs += "cxc_ship_iso"
```

---

## 8. Error Handling Design

### 8.1 Error Categories

| Category          | Handling                          | Exit Code |
|:------------------|:----------------------------------|:----------|
| Missing state     | Error message + exit              | 1         |
| Invalid config    | Warning + use defaults            | Continue  |
| Worktree invalid  | Error message + exit              | 1         |
| Agent failure     | Error message + may retry         | 1         |
| Test failure      | Retry with resolution             | 1 (final) |
| PR approval fail  | Warning, continue                 | Continue  |
| Issue close fail  | Warning, continue                 | Continue  |

### 8.2 Recovery Patterns

**Idempotent Operations:**
- State loading checks existence first
- Worktree creation handles existing worktrees
- Branch creation handles existing branches
- PR creation checks for existing PR

**Retry with Backoff:**
- Test resolution (4 attempts unit, 2 attempts E2E)
- Review resolution (3 attempts)

---

## 9. Testing Design

### 9.1 Fixture Hierarchy

```python
# Project structure fixture
tmp_project_dir -> Creates:
  .cxc.yaml
  .env
  artifacts/{org}/{repo}/trees/
  specs/
  commands/

# Mock fixtures
mock_cxc_config -> Mocked CxCConfig.load()
mock_cxc_state -> Pre-populated CxCState
mock_subprocess -> Mock subprocess.run
mock_git_commands -> Configured git responses
mock_claude_execution -> Configured Claude responses

# Data fixtures
sample_github_issue -> Feature issue JSON
sample_github_issue_bug -> Bug issue JSON
```

### 9.2 Test Categories

| Category      | Marker            | Description                    |
|:--------------|:------------------|:-------------------------------|
| Unit          | `@pytest.mark.unit` | Fast, isolated tests         |
| Integration   | `@pytest.mark.integration` | Multi-component tests |
| API           | `@pytest.mark.requires_api` | Needs live API       |

### 9.3 Test Naming Convention

```
test_{method_or_feature}_{scenario}
```

Examples:
- `test_load_from_yaml` - Config loads from file
- `test_load_missing_yaml_uses_defaults` - Missing file uses defaults
- `test_get_returns_default` - Get with missing key

---

## 10. Deployment Design

### 10.1 Package Installation

```bash
# As framework dependency (recommended)
uv add ../cxc-framework

# Direct execution
uv run cxc --help
```

### 10.2 Configuration for Consuming Projects

```yaml
# .cxc.yaml
project_id: "org/repo"
artifacts_dir: "./artifacts"
source_root: "./src"
commands:
  - "${CxC_FRAMEWORK}/commands"
  - ".claude/commands"
app:
  backend_dir: "backend"
  frontend_dir: "frontend"
  test_command: "pytest"
```

### 10.3 Trigger Deployment

**Webhook (FastAPI):**
```bash
# Start webhook server
uv run cxc webhook
# Listens on port 8000 by default
```

**Cron (Polling):**
```bash
# Start polling monitor
uv run cxc monitor
# Polls for new issues periodically
```

---

## 11. Security Considerations

### 11.1 Secret Management

| Secret                | Storage          | Access Method            |
|:----------------------|:-----------------|:-------------------------|
| `ANTHROPIC_API_KEY`   | `.env` file      | `os.getenv()`            |
| `GITHUB_PAT`          | `.env` or gh auth| `os.getenv()` or gh CLI  |
| R2 credentials        | `.env` file      | `os.getenv()`            |

### 11.2 Git Safety

- Never force push
- Never modify git config
- Always use `--no-ff` for merges
- Restore original branch after operations
- Validate worktree before destructive operations

---

## 12. Performance Considerations

### 12.1 Optimization Strategies

| Strategy                    | Implementation                        |
|:----------------------------|:--------------------------------------|
| Combined LLM calls          | `classify_and_generate_branch` (2x faster) |
| Deterministic ports         | Hash-based allocation (no scanning)   |
| Worktree isolation          | Parallel execution possible           |
| Template caching            | Commands loaded once per execution    |

### 12.2 Resource Management

- Worktrees are lightweight (shared git objects)
- State files are small JSON (~1KB)
- Prompts logged for debugging but rotated
- Ports deterministic to avoid conflicts

---

## Appendix A: Data Flow Diagrams

### A.1 Plan Workflow Data Flow

```
GitHub Issue
    |
    v
fetch_issue() --> GitHubIssue
    |
    v
classify_and_generate_branch() --> (issue_class, branch_name)
    |
    v
create_worktree() --> worktree_path
    |
    v
get_ports_for_cxc() --> (backend_port, frontend_port)
    |
    v
execute_template(/install_worktree) --> Environment setup
    |
    v
build_plan() --> plan_file
    |
    v
commit_changes() --> Commit
    |
    v
finalize_git_operations() --> PR
    |
    v
CxCState.save() --> cxc_state.json
```

### A.2 Agent Execution Data Flow

```
AgentTemplateRequest
    |
    v
_load_template(command) --> Template content
    |
    v
_substitute_args(template, args) --> Final prompt
    |
    v
_save_prompt(prompt, cxc_id, agent) --> Saved for debugging
    |
    v
_execute_claude_code(prompt, dir, model) --> JSONL output
    |
    v
_parse_jsonl_response(jsonl) --> AgentPromptResponse
```

---

## Appendix B: Configuration Examples

### B.1 Minimal .cxc.yaml

```yaml
project_id: "myorg/myrepo"
```

### B.2 Full .cxc.yaml

```yaml
project_id: "myorg/myrepo"
artifacts_dir: "./artifacts"
source_root: "./src"
ports:
  backend_start: 9100
  backend_count: 15
  frontend_start: 9200
  frontend_count: 15
commands:
  - "${CxC_FRAMEWORK}/commands"
  - ".claude/commands"
app:
  backend_dir: "backend"
  frontend_dir: "frontend"
  test_command: "pytest"
  start_backend: "scripts/start_backend.sh"
  start_frontend: "scripts/start_frontend.sh"
  reset_db_script: "scripts/reset_db.sh"
```

### B.3 .env Example

```bash
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_PAT=ghp_...
CLAUDE_CODE_PATH=claude
CLOUDFLARE_ACCOUNT_ID=...
CLOUDFLARE_R2_ACCESS_KEY_ID=...
CLOUDFLARE_R2_SECRET_ACCESS_KEY=...
CLOUDFLARE_R2_BUCKET_NAME=...
```
