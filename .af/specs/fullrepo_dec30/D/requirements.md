# CxC Framework Requirements Specification (Claude)

**Version:** 1.0.0
**Date:** 2025-12-30
**Document Type:** Contract-Based Requirements

---

## Executive Summary

CxC (Cortex Code) is an orchestration framework that automates software development using Claude Code agents in isolated git worktrees. It processes GitHub issues through a complete SDLC pipeline: plan, build, test, review, document, and ship.

---

## 1. CLI Contract

### 1.1 Entry Point

| Command           | Module                          | Required Args        | Optional Args                  | Description                              |
|:------------------|:--------------------------------|:---------------------|:-------------------------------|:-----------------------------------------|
| `cxc plan`        | `wt.plan_iso`                   | `<issue-number>`     | `[cxc-id]`                     | Planning phase - creates worktree + plan |
| `cxc build`       | `wt.build_iso`                  | `<issue-number> <cxc-id>` |                           | Implementation phase                     |
| `cxc test`        | `wt.test_iso`                   | `<issue-number> <cxc-id>` | `--skip-e2e`             | Testing phase with retry logic           |
| `cxc review`      | `wt.review_iso`                 | `<issue-number> <cxc-id>` | `--skip-resolution`      | Review against spec with screenshots     |
| `cxc document`    | `wt.document_iso`               | `<issue-number> <cxc-id>` |                           | Documentation generation                 |
| `cxc ship`        | `wt.ship_iso`                   | `<issue-number> <cxc-id>` |                           | Approve and merge PR                     |
| `cxc patch`       | `wt.patch_iso`                  | `<issue-number>`     | `[cxc-id]`                     | Create patch for review issue            |
| `cxc sdlc`        | `wt.sdlc_iso`                   | `<issue-number>`     | `[cxc-id] --skip-e2e --skip-resolution` | Full pipeline (no ship)   |
| `cxc zte`         | `wt.sdlc_zte_iso`               | `<issue-number>`     | `[cxc-id] --skip-e2e --skip-resolution` | Full pipeline + auto-ship |
| `cxc monitor`     | `triggers.trigger_cron`         |                      |                                | Polling-based trigger                    |
| `cxc webhook`     | `triggers.trigger_webhook`      |                      |                                | FastAPI webhook server                   |

### 1.2 CLI Behaviors

| Requirement ID | Description                                                                  |
|:---------------|:-----------------------------------------------------------------------------|
| CLI-01         | `cxc --help` shows usage information and exits with code 0                   |
| CLI-02         | `cxc` with no command shows help and exits with code 1                       |
| CLI-03         | Dynamically imports workflow modules via `importlib.import_module`           |
| CLI-04         | Patches `sys.argv` before calling workflow `main()`                          |
| CLI-05         | Exits with code 1 if workflow module not found                               |
| CLI-06         | Exits with code 1 if workflow module has no `main()` function                |
| CLI-07         | Exits with code 1 on runtime exceptions with error message                   |
| CLI-08         | Passes all remaining args (including flags) to workflow module               |

---

## 2. Configuration Contract

### 2.1 Configuration File: `.cxc.yaml`

| Field             | Type            | Default               | Description                                   |
|:------------------|:----------------|:----------------------|:----------------------------------------------|
| `project_id`      | `string`        | `"unknown-project"`   | GitHub repo identifier (org/repo format)      |
| `artifacts_dir`   | `string`        | `"./artifacts"`       | Base directory for workflow artifacts         |
| `source_root`     | `string`        | `"./src"`             | Where app/feature code is written             |
| `ports.backend_start`   | `int`     | `9100`                | Starting port for backend services            |
| `ports.backend_count`   | `int`     | `15`                  | Number of backend ports available             |
| `ports.frontend_start`  | `int`     | `9200`                | Starting port for frontend services           |
| `ports.frontend_count`  | `int`     | `15`                  | Number of frontend ports available            |
| `commands`        | `list[string]`  | `["${CxC_FRAMEWORK}/commands"]` | Slash command search paths        |
| `app`             | `dict`          | `{}`                  | App-specific config (backend_dir, etc.)       |

### 2.2 CxCConfig Class Behaviors

| Requirement ID | Description                                                                 |
|:---------------|:----------------------------------------------------------------------------|
| CFG-01         | Loads `.cxc.yaml` from project root or walks up directory tree to find it  |
| CFG-02         | Missing `.cxc.yaml` uses default values (does not raise)                   |
| CFG-03         | Invalid YAML falls back to defaults with warning                           |
| CFG-04         | Relative `artifacts_dir` resolved to absolute path from project root       |
| CFG-05         | Absolute `artifacts_dir` preserved as-is                                   |
| CFG-06         | `${CxC_FRAMEWORK}` expanded in command paths to framework location         |
| CFG-07         | Partial YAML merges with defaults (specified values override)              |
| CFG-08         | `get_project_artifacts_dir()` returns `artifacts/{org}/{repo}`             |
| CFG-09         | `get_agents_dir(cxc_id)` returns `artifacts/{org}/{repo}/{cxc_id}`         |
| CFG-10         | `get_trees_dir()` returns `artifacts/{org}/{repo}/trees`                   |
| CFG-11         | `get_app_source_dir(appname)` returns `source_root/{appname}`              |

### 2.3 Environment Variables Contract

| Variable                     | Required | Default   | Description                           |
|:-----------------------------|:---------|:----------|:--------------------------------------|
| `ANTHROPIC_API_KEY`          | Yes      |           | Claude API key                        |
| `GITHUB_PAT`                 | No       | gh auth   | GitHub Personal Access Token          |
| `CLAUDE_CODE_PATH`           | No       | `claude`  | Path to Claude Code CLI               |
| `GITHUB_REPO_URL`            | No       | git origin| Repository URL                        |
| `CLOUDFLARE_ACCOUNT_ID`      | No       |           | R2 upload account                     |
| `CLOUDFLARE_R2_ACCESS_KEY_ID`| No       |           | R2 access key                         |
| `CLOUDFLARE_R2_SECRET_ACCESS_KEY` | No  |           | R2 secret key                         |
| `CLOUDFLARE_R2_BUCKET_NAME`  | No       |           | R2 bucket name                        |

---

## 3. State Contract

### 3.1 CxCState Data Schema

| Field           | Type                | Required | Description                                 |
|:----------------|:--------------------|:---------|:--------------------------------------------|
| `cxc_id`        | `string`            | Yes      | 8-character unique workflow ID              |
| `issue_number`  | `string` or `null`  | No       | GitHub issue number                         |
| `branch_name`   | `string` or `null`  | No       | Feature branch name                         |
| `plan_file`     | `string` or `null`  | No       | Path to plan/spec file                      |
| `issue_class`   | `SlashCommand` or `null` | No  | Issue type: /feature, /bug, /chore, /patch  |
| `worktree_path` | `string` or `null`  | No       | Absolute path to git worktree               |
| `backend_port`  | `int` or `null`     | No       | Allocated backend port                      |
| `frontend_port` | `int` or `null`     | No       | Allocated frontend port                     |
| `model_set`     | `"base"` or `"heavy"` or `null` | No | Model tier for agent execution        |
| `all_cxcs`      | `list[string]`      | No       | List of workflow steps that have run        |

### 3.2 CxCState Class Behaviors

| Requirement ID | Description                                                                   |
|:---------------|:------------------------------------------------------------------------------|
| STATE-01       | `CxCState("")` raises `ValueError` with message "cxc_id is required"          |
| STATE-02       | `update()` filters out non-core fields (only schema fields persisted)         |
| STATE-03       | `get(key)` returns value or None for missing keys                             |
| STATE-04       | `get(key, default)` returns default for missing keys                          |
| STATE-05       | `append_cxc_id(id)` adds workflow step to `all_cxcs` list                     |
| STATE-06       | `append_cxc_id()` deduplicates (no duplicate entries)                         |
| STATE-07       | `get_working_directory()` returns `worktree_path` if set, else project root   |
| STATE-08       | `get_state_path()` returns `artifacts/{org}/{repo}/{cxc_id}/cxc_state.json`   |
| STATE-09       | `save()` creates parent directories if they don't exist                       |
| STATE-10       | `save()` validates data against Pydantic schema before writing                |
| STATE-11       | `save(workflow_step)` logs the workflow step being saved                      |
| STATE-12       | `load(cxc_id)` returns None if state file doesn't exist                       |
| STATE-13       | `load(cxc_id)` parses valid JSON and returns CxCState instance                |
| STATE-14       | `from_stdin()` returns None if stdin is a TTY                                 |
| STATE-15       | `from_stdin()` parses JSON from piped stdin                                   |
| STATE-16       | `from_stdin()` returns None for empty stdin                                   |
| STATE-17       | `from_stdin()` returns None for invalid JSON                                  |
| STATE-18       | `from_stdin()` returns None if JSON lacks `cxc_id`                            |
| STATE-19       | `to_stdout()` outputs complete JSON including `all_cxcs`                      |

---

## 4. Workflow Contracts

### 4.1 Plan Workflow (`plan_iso.py`)

**Inputs:**
- `issue-number` (required): GitHub issue to process
- `cxc-id` (optional): Existing CxC ID to resume

**Outputs:**
- Creates worktree at `artifacts/{org}/{repo}/trees/{cxc_id}/`
- Creates plan file at `specs/issue-{N}-cxc-{ID}-sdlc_planner-{name}.md`
- Creates/updates pull request
- Persists state to `cxc_state.json`

**Side Effects:**
- Posts comments to GitHub issue at each phase
- Allocates backend/frontend ports
- Creates feature branch

**State Transitions:**
| Action                     | State Field Updated                                    |
|:---------------------------|:-------------------------------------------------------|
| Generate ID                | `cxc_id`                                               |
| Classify + branch          | `issue_class`, `branch_name`                           |
| Create worktree            | `worktree_path`, `backend_port`, `frontend_port`       |
| Build plan                 | `plan_file`                                            |
| Track run                  | `all_cxcs` += "cxc_plan_iso"                           |

### 4.2 Build Workflow (`build_iso.py`)

**Inputs:**
- `issue-number` (required)
- `cxc-id` (required): Must have existing state

**Preconditions:**
- State file must exist for `cxc_id`
- Worktree must be valid
- `branch_name` must be in state
- `plan_file` must be in state

**Outputs:**
- Implemented code in worktree
- Commit with implementation changes
- Updated PR

**Error Handling:**
- Exits with code 1 if no state found
- Exits with code 1 if worktree validation fails
- Exits with code 1 if missing branch_name or plan_file

### 4.3 Test Workflow (`test_iso.py`)

**Inputs:**
- `issue-number` (required)
- `cxc-id` (required)
- `--skip-e2e` (optional): Skip end-to-end tests

**Retry Logic:**
- Unit tests: MAX_TEST_RETRY_ATTEMPTS = 4
- E2E tests: MAX_E2E_TEST_RETRY_ATTEMPTS = 2

**Behaviors:**
| Requirement ID | Description                                                           |
|:---------------|:----------------------------------------------------------------------|
| TEST-01        | Runs unit tests via `/test` command                                   |
| TEST-02        | Parses JSON test results (`TestResult` schema)                        |
| TEST-03        | Attempts resolution for failed tests via `/resolve_failed_test`       |
| TEST-04        | Re-runs tests after successful resolution                             |
| TEST-05        | Stops retrying if no tests were resolved                              |
| TEST-06        | Runs E2E tests via `/test_e2e` if not skipped                         |
| TEST-07        | Posts comprehensive test summary to issue                             |
| TEST-08        | Commits test results regardless of pass/fail                          |
| TEST-09        | Exits with code 1 if total failures > 0 (after all retries)           |

### 4.4 Review Workflow (`review_iso.py`)

**Inputs:**
- `issue-number` (required)
- `cxc-id` (required)
- `--skip-resolution` (optional): Don't attempt to fix blocker issues

**Retry Logic:**
- MAX_REVIEW_RETRY_ATTEMPTS = 3

**Outputs:**
- Review result JSON (`ReviewResult` schema)
- Screenshots uploaded to R2
- Updated PR body with review summary

**Behaviors:**
| Requirement ID | Description                                                           |
|:---------------|:----------------------------------------------------------------------|
| REVIEW-01      | Finds spec file from state or branch                                  |
| REVIEW-02      | Runs review via `/review` command                                     |
| REVIEW-03      | Parses `ReviewResult` JSON response                                   |
| REVIEW-04      | Uploads screenshots to R2 if configured                               |
| REVIEW-05      | Creates patch plans for blocker issues if not skipped                 |
| REVIEW-06      | Implements patches via `/implement`                                   |
| REVIEW-07      | Retries review after resolving blockers                               |
| REVIEW-08      | Updates PR body with comprehensive summary                            |

### 4.5 Document Workflow (`document_iso.py`)

**Inputs:**
- `issue-number` (required)
- `cxc-id` (required)

**Behaviors:**
| Requirement ID | Description                                                           |
|:---------------|:----------------------------------------------------------------------|
| DOC-01         | Checks for changes vs origin/main before documenting                  |
| DOC-02         | Skips documentation if no changes detected                            |
| DOC-03         | Finds spec file from state                                            |
| DOC-04         | Generates docs via `/document` command                                |
| DOC-05         | Creates doc at `app_docs/feature-{cxc_id}-{name}.md`                  |
| DOC-06         | Tracks agentic KPIs (never fails main workflow)                       |
| DOC-07         | Commits documentation changes                                         |

### 4.6 Ship Workflow (`ship_iso.py`)

**Inputs:**
- `issue-number` (required)
- `cxc-id` (required)

**Preconditions (all must be non-None):**
- `cxc_id`
- `issue_number`
- `branch_name`
- `plan_file`
- `issue_class`
- `worktree_path`
- `backend_port`
- `frontend_port`

**Behaviors:**
| Requirement ID | Description                                                           |
|:---------------|:----------------------------------------------------------------------|
| SHIP-01        | Validates all state fields are populated                              |
| SHIP-02        | Validates worktree exists                                             |
| SHIP-03        | Approves PR via GitHub API                                            |
| SHIP-04        | Performs manual merge to main (fetch, checkout, merge, push)          |
| SHIP-05        | Closes GitHub issue                                                   |
| SHIP-06        | Uses --no-ff merge to preserve commit history                         |
| SHIP-07        | Restores original branch after merge                                  |

### 4.7 SDLC Workflow (`sdlc_iso.py`)

**Pipeline Sequence:**
1. `plan_iso` - Creates worktree and plan
2. `build_iso` - Implements plan
3. `test_iso` - Runs tests (continues on failure)
4. `review_iso` - Reviews implementation
5. `document_iso` - Generates documentation

**Exit Conditions:**
| Phase      | Exit on Failure?                           |
|:-----------|:-------------------------------------------|
| Plan       | Yes                                        |
| Build      | Yes                                        |
| Test       | No (warns but continues to review)         |
| Review     | Yes                                        |
| Document   | Yes                                        |

### 4.8 ZTE Workflow (`sdlc_zte_iso.py`)

**Same as SDLC plus:**
- Runs `ship_iso` at end
- Posts initial ZTE comment to issue
- Exits on test failure (stricter than SDLC)
- Documentation failure does not block shipping

---

## 5. Integration Contracts

### 5.1 GitHub Integration (`github.py`)

| Function                    | Inputs                         | Outputs                      | Side Effects                   |
|:----------------------------|:-------------------------------|:-----------------------------|:-------------------------------|
| `fetch_issue`               | `issue_number, repo_path`      | `GitHubIssue`                | Calls `gh issue view`          |
| `make_issue_comment`        | `issue_number, body`           | `bool`                       | Posts comment via `gh`         |
| `get_repo_url`              | None                           | `str`                        | Gets from env or git remote    |
| `extract_repo_path`         | `url`                          | `str` (org/repo)             | Parses URL                     |
| `approve_pr`                | `pr_number, repo_path`         | `(bool, error)`              | Approves via `gh pr review`    |
| `close_issue`               | `issue_number, repo_path`      | `(bool, error)`              | Closes via `gh issue close`    |

### 5.2 Git Operations (`git_ops.py`)

| Function                    | Inputs                         | Outputs                      | Side Effects                   |
|:----------------------------|:-------------------------------|:-----------------------------|:-------------------------------|
| `commit_changes`            | `message, cwd`                 | `(bool, error)`              | git add -A && git commit       |
| `get_current_branch`        | `cwd`                          | `str`                        | git rev-parse --abbrev-ref     |
| `finalize_git_operations`   | `state, logger, cwd`           | None                         | Pushes and creates/updates PR  |
| `get_pr_number`             | `branch_name`                  | `int or None`                | gh pr list                     |
| `get_pr_number_for_branch`  | `branch_name`                  | `int or None`                | gh pr list                     |
| `update_pr_body`            | `pr_number, body, logger`      | `(bool, error)`              | gh pr edit                     |

### 5.3 Worktree Operations (`worktree_ops.py`)

| Function                    | Inputs                         | Outputs                      | Description                    |
|:----------------------------|:-------------------------------|:-----------------------------|:-------------------------------|
| `create_worktree`           | `cxc_id, branch_name, logger`  | `(path, error)`              | Creates isolated worktree      |
| `validate_worktree`         | `cxc_id, state`                | `(bool, error)`              | Checks worktree exists + valid |
| `get_ports_for_cxc`         | `cxc_id`                       | `(backend, frontend)`        | Deterministic port allocation  |
| `is_port_available`         | `port`                         | `bool`                       | Checks if port is free         |
| `find_next_available_ports` | `cxc_id`                       | `(backend, frontend)`        | Finds free ports               |
| `setup_worktree_environment`| `path, backend, frontend, log` | None                         | Creates .ports.env             |

**Port Allocation Formula:**
```python
def get_ports_for_cxc(cxc_id: str) -> tuple[int, int]:
    hash_val = int(hashlib.md5(cxc_id.encode()).hexdigest()[:8], 16)
    backend_offset = hash_val % config.ports.backend_count
    frontend_offset = hash_val % config.ports.frontend_count
    return (
        config.ports.backend_start + backend_offset,
        config.ports.frontend_start + frontend_offset
    )
```

### 5.4 Workflow Operations (`workflow_ops.py`)

| Function                      | Inputs                              | Outputs                   | Description                          |
|:------------------------------|:------------------------------------|:--------------------------|:-------------------------------------|
| `ensure_cxc_id`               | `issue_number, cxc_id?, logger?`    | `str`                     | Creates or validates CxC ID          |
| `classify_issue`              | `issue, cxc_id, logger`             | `(command, error)`        | Determines /feature, /bug, /chore    |
| `generate_branch_name`        | `issue, cxc_id, logger`             | `(name, error)`           | Creates branch name                  |
| `classify_and_generate_branch`| `issue, cxc_id, logger`             | `(cmd, branch, error)`    | Combined LLM call (2x faster)        |
| `build_plan`                  | `issue, cmd, cxc_id, log, dir`      | `AgentPromptResponse`     | Runs /feature, /bug, or /chore       |
| `implement_plan`              | `plan_file, cxc_id, log, dir`       | `AgentPromptResponse`     | Runs /implement                      |
| `create_commit`               | `agent, issue, cmd, cxc_id, log, cwd` | `(msg, error)`          | Runs /commit                         |
| `find_spec_file`              | `state, logger`                     | `str or None`             | Locates plan/spec file               |
| `format_issue_message`        | `cxc_id, agent, msg`                | `str`                     | Formats `{cxc_id}_{agent}: {msg}`    |
| `post_artifact_to_issue`      | `issue, cxc_id, agent, title, content, path, collapsible` | None | Posts formatted artifact |
| `post_state_to_issue`         | `issue, cxc_id, state, title`       | None                      | Posts state JSON to issue            |

---

## 6. Agent Contract

### 6.1 AgentTemplateRequest Schema

| Field           | Type            | Required | Description                           |
|:----------------|:----------------|:---------|:--------------------------------------|
| `agent_name`    | `string`        | Yes      | Identifier for logging/artifacts      |
| `slash_command` | `SlashCommand`  | Yes      | Command template to execute           |
| `args`          | `list[string]`  | No       | Arguments for template                |
| `cxc_id`        | `string`        | Yes      | Workflow ID for context               |
| `working_dir`   | `string`        | No       | Directory to execute in               |

### 6.2 AgentPromptResponse Schema

| Field           | Type            | Description                           |
|:----------------|:----------------|:--------------------------------------|
| `success`       | `bool`          | True if agent completed successfully  |
| `output`        | `string`        | Agent's response/result               |
| `error`         | `string` or None| Error message if failed               |
| `duration_ms`   | `int`           | Execution time                        |
| `cost_usd`      | `float`         | API cost                              |

### 6.3 execute_template Behaviors

| Requirement ID | Description                                                             |
|:---------------|:------------------------------------------------------------------------|
| AGENT-01       | Loads template from commands directory based on `slash_command`         |
| AGENT-02       | Replaces `$ARGUMENTS` placeholder with args                             |
| AGENT-03       | Replaces `$1`, `$2`, etc. with positional args                          |
| AGENT-04       | Executes Claude Code CLI with `--print` flag                            |
| AGENT-05       | Saves prompt to `artifacts/{cxc_id}/ops/prompts/{agent}_{timestamp}.md` |
| AGENT-06       | Parses JSONL output for result                                          |
| AGENT-07       | Uses `heavy` model for: /implement, /document, /feature, /bug, /chore, /patch |
| AGENT-08       | Uses `base` model for all other commands                                |
| AGENT-09       | Returns structured `AgentPromptResponse`                                |

### 6.4 SlashCommand Literals

```python
SlashCommand = Literal[
    "/feature",
    "/bug",
    "/chore",
    "/patch",
    "/implement",
    "/review",
    "/document",
    "/commit",
    "/test",
    "/test_e2e",
    "/resolve_failed_test",
    "/resolve_failed_e2e_test",
    "/classify_issue",
    "/generate_branch_name",
    "/classify_and_branch",
    "/install_worktree",
    "/track_agentic_kpis",
]
```

---

## 7. Command Template Contract

### 7.1 Planning Commands

| Command       | Variables                        | Output                           | Creates File                                |
|:--------------|:---------------------------------|:---------------------------------|:--------------------------------------------|
| `/feature`    | `$1=issue_num, $2=cxc_id, $3=json` | Plan file path                 | `specs/issue-{N}-cxc-{ID}-sdlc_planner-{name}.md` |
| `/bug`        | `$1=issue_num, $2=cxc_id, $3=json` | Plan file path                 | Same pattern                                |
| `/chore`      | `$1=issue_num, $2=cxc_id, $3=json` | Plan file path                 | Same pattern                                |
| `/patch`      | `$1=cxc_id, $2=request, $3=spec`   | Patch file path                | `specs/patch/patch-cxc-{ID}-{name}.md`      |

### 7.2 Classification Commands

| Command                | Input              | Output Format                                    |
|:-----------------------|:-------------------|:-------------------------------------------------|
| `/classify_issue`      | Issue JSON         | Literal: `/chore`, `/bug`, `/feature`, `/patch`  |
| `/generate_branch_name`| Issue JSON + cxc_id| Branch name string                               |
| `/classify_and_branch` | `$1=cxc_id, $2=json` | JSON: `{"issue_class": "/feature", "branch_name": "..."}` |

### 7.3 Execution Commands

| Command                   | Input                    | Output                              |
|:--------------------------|:-------------------------|:------------------------------------|
| `/implement`              | Plan file path           | Summary + git diff --stat           |
| `/commit`                 | agent, issue_class, json | Commit message used                 |
| `/review`                 | cxc_id, spec_file, agent | JSON: ReviewResult                  |
| `/document`               | cxc_id, spec_path        | Doc file path                       |
| `/install_worktree`       | path, backend, frontend  | Report of files created             |

### 7.4 Test Commands

| Command                    | Input           | Output Format                          |
|:---------------------------|:----------------|:---------------------------------------|
| `/test`                    | None            | JSON: `List[TestResult]`               |
| `/test_e2e`                | None            | JSON: `List[E2ETestResult]`            |
| `/resolve_failed_test`     | TestResult JSON | Success/failure message                |
| `/resolve_failed_e2e_test` | E2ETestResult   | Success/failure message                |

---

## 8. Data Type Schemas

### 8.1 GitHubIssue

```python
class GitHubIssue(BaseModel):
    number: int
    title: str
    body: str
    state: str  # "open" | "closed"
    author: GitHubUser
    assignees: List[GitHubUser] = []
    labels: List[GitHubLabel] = []
    milestone: Optional[GitHubMilestone] = None
    comments: List[GitHubComment] = []
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    url: str
```

### 8.2 TestResult

```python
class TestResult(BaseModel):
    test_name: str
    passed: bool
    error_message: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    duration_ms: Optional[int] = None
```

### 8.3 E2ETestResult

```python
class E2ETestResult(BaseModel):
    test_name: str
    passed: bool
    error_message: Optional[str] = None
    screenshots: List[str] = []
    duration_ms: Optional[int] = None
```

### 8.4 ReviewResult

```python
class ReviewResult(BaseModel):
    success: bool
    review_summary: str
    review_issues: List[ReviewIssue] = []
    screenshots: List[str] = []
    screenshot_urls: List[str] = []
```

### 8.5 ReviewIssue

```python
class ReviewIssue(BaseModel):
    review_issue_number: int
    screenshot_path: Optional[str] = None
    screenshot_url: Optional[str] = None
    issue_description: str
    issue_resolution: str
    issue_severity: Literal["skippable", "tech_debt", "blocker"]
```

### 8.6 DocumentationResult

```python
class DocumentationResult(BaseModel):
    success: bool
    documentation_created: bool
    documentation_path: Optional[str] = None
    error_message: Optional[str] = None
```

---

## 9. File System Contract

### 9.1 Artifact Directory Structure

```
artifacts/{org}/{repo}/
├── {cxc-id}/
│   ├── cxc_state.json           # Persistent workflow state
│   └── ops/prompts/             # Saved agent prompts
│       └── {agent}_{timestamp}.md
└── trees/
    └── {cxc-id}/                # Isolated git worktree
        ├── .ports.env           # Port configuration
        ├── .env                 # Environment (copied from parent)
        ├── .mcp.json            # MCP configuration (updated paths)
        └── playwright-mcp-config.json
```

### 9.2 Spec File Structure

```
specs/
├── issue-{N}-cxc-{ID}-sdlc_planner-{name}.md    # Feature/bug/chore plans
└── patch/
    └── patch-cxc-{ID}-{name}.md                  # Patch plans
```

### 9.3 Documentation Structure

```
app_docs/
├── assets/                    # Screenshots
│   └── *.png
└── feature-{cxc_id}-{name}.md # Feature documentation
```

---

## 10. Webhook Trigger Contract

### 10.1 Comment Triggers

| Comment Pattern       | Workflow Triggered        | Model Set |
|:----------------------|:--------------------------|:----------|
| `cxc_plan_iso`        | `plan_iso`                | base      |
| `cxc_sdlc_iso`        | `sdlc_iso`                | base      |
| `cxc_sdlc_zte_iso`    | `sdlc_zte_iso`            | base      |
| `model_set heavy`     | Uses heavy models         | heavy     |

### 10.2 Webhook Endpoint

| Endpoint    | Method | Payload              | Action                      |
|:------------|:-------|:---------------------|:----------------------------|
| `/webhook`  | POST   | GitHub issue comment | Parses trigger, runs workflow |

---

## 11. Model Selection Contract

| Slash Command     | Model Tier |
|:------------------|:-----------|
| `/implement`      | heavy      |
| `/document`       | heavy      |
| `/feature`        | heavy      |
| `/bug`            | heavy      |
| `/chore`          | heavy      |
| `/patch`          | heavy      |
| All others        | base       |

---

## 12. Error Handling Contract

### 12.1 Workflow Exit Codes

| Exit Code | Meaning                                      |
|:----------|:---------------------------------------------|
| 0         | Success                                      |
| 1         | Failure (missing state, validation, etc.)    |

### 12.2 Non-Failing Operations

| Operation              | Failure Behavior                            |
|:-----------------------|:--------------------------------------------|
| PR approval            | Logs warning, continues                     |
| Issue closing          | Logs warning, continues                     |
| KPI tracking           | Logs warning, continues                     |
| Screenshot upload      | Falls back to local path                    |

---

## Appendix A: CxC ID Generation

```python
def make_cxc_id() -> str:
    """Generate 8-character unique workflow ID."""
    return uuid.uuid4().hex[:8]
```

**Format:** 8 lowercase hexadecimal characters (e.g., `abc12345`)

## Appendix B: Branch Name Format

```
{type}-issue-{number}-cxc-{cxc_id}-{slug}
```

Where:
- `type`: `feat`, `bug`, or `chore`
- `number`: GitHub issue number
- `cxc_id`: 8-character workflow ID
- `slug`: 3-6 lowercase words from issue title, hyphen-separated

**Example:** `feat-issue-42-cxc-abc12345-add-user-authentication`
