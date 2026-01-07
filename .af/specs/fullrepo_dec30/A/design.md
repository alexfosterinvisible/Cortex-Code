# CxC Framework - Architecture and Design Document (Claude)

## Document Information

| Field           | Value                          |
|-----------------|--------------------------------|
| Version         | 1.0                            |
| Date            | 2025-12-30                     |
| Status          | Complete                       |
| Author          | Claude Code Agent              |

---

## 1. System Architecture Overview

### 1.1 High-Level Architecture

CxC Framework is a Python-based orchestration system that automates software development workflows using Claude Code agents. The architecture follows a layered design with clear separation of concerns:

```
+-----------------------------------------------------------------------+
|                          CLI Entry Point                               |
|                            (cxc/cli.py)                                |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                        Workflow Orchestration                          |
|                         (cxc/workflows/wt/)                            |
|  +------------+  +------------+  +------------+  +------------+        |
|  | plan_iso   |  | build_iso  |  | test_iso   |  | review_iso |        |
|  +------------+  +------------+  +------------+  +------------+        |
|  +------------+  +------------+  +------------+  +------------+        |
|  |document_iso|  | ship_iso   |  | sdlc_iso   |  |sdlc_zte_iso|        |
|  +------------+  +------------+  +------------+  +------------+        |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                         Integration Layer                              |
|                      (cxc/integrations/)                               |
|  +------------+  +------------+  +------------+  +------------+        |
|  | github.py  |  | git_ops.py |  |workflow_ops|  |worktree_ops|        |
|  +------------+  +------------+  +------------+  +------------+        |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                           Core Layer                                   |
|                          (cxc/core/)                                   |
|  +------------+  +------------+  +------------+  +------------+        |
|  | config.py  |  | state.py   |  | agent.py   |  | data_types |        |
|  +------------+  +------------+  +------------+  +------------+        |
|                 +------------+  +------------+                         |
|                 | utils.py   |  | health.py  |                         |
|                 +------------+  +------------+                         |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                        External Systems                                |
|  +-------------+  +-------------+  +-------------+  +-------------+    |
|  | Claude Code |  | GitHub API  |  | Git/Worktree|  | Cloudflare  |    |
|  |    CLI      |  | (via gh)    |  |             |  |     R2      |    |
|  +-------------+  +-------------+  +-------------+  +-------------+    |
+-----------------------------------------------------------------------+
```

### 1.2 Package Structure

```
cxc-framework/
|-- cxc/                           # Main package
|   |-- __init__.py
|   |-- cli.py                     # CLI entry point
|   |-- core/                      # Core abstractions
|   |   |-- __init__.py
|   |   |-- config.py              # Configuration management
|   |   |-- state.py               # Workflow state persistence
|   |   |-- agent.py               # Claude Code execution
|   |   |-- data_types.py          # Pydantic models
|   |   |-- utils.py               # Utilities and helpers
|   |   |-- health.py              # Health check logic
|   |-- integrations/              # External system adapters
|   |   |-- __init__.py
|   |   |-- github.py              # GitHub API via gh CLI
|   |   |-- git_ops.py             # Git operations
|   |   |-- workflow_ops.py        # Shared workflow operations
|   |   |-- worktree_ops.py        # Git worktree management
|   |   |-- r2_uploader.py         # Cloudflare R2 uploads
|   |-- workflows/                 # Workflow implementations
|   |   |-- __init__.py
|   |   |-- wt/                    # Worktree-isolated workflows
|   |   |   |-- __init__.py
|   |   |   |-- plan_iso.py
|   |   |   |-- build_iso.py
|   |   |   |-- test_iso.py
|   |   |   |-- review_iso.py
|   |   |   |-- document_iso.py
|   |   |   |-- ship_iso.py
|   |   |   |-- patch_iso.py
|   |   |   |-- sdlc_iso.py
|   |   |   |-- sdlc_zte_iso.py
|   |   |-- reg/                   # Regular workflows (deprecated)
|   |-- triggers/                  # Event triggers
|       |-- __init__.py
|       |-- trigger_webhook.py     # FastAPI webhook server
|       |-- trigger_cron.py        # Polling-based trigger
|-- commands/                      # Slash command templates
|-- templates/                     # Configuration templates
|-- tests/                         # Test suite
```

---

## 2. Component Design

### 2.1 Core Components

#### 2.1.1 Configuration (CxCConfig)

**Responsibility**: Load and provide access to project configuration.

**Data Model**:
```
CxCConfig
|-- project_root: Path           # Resolved project directory
|-- project_id: str              # GitHub org/repo identifier
|-- artifacts_dir: Path          # State and artifact storage
|-- source_root: Path            # Source code base path
|-- ports: PortConfig            # Port allocation settings
|   |-- backend_start: int       # Starting port for backend (default: 9100)
|   |-- backend_count: int       # Number of backend ports (default: 15)
|   |-- frontend_start: int      # Starting port for frontend (default: 9200)
|   |-- frontend_count: int      # Number of frontend ports (default: 15)
|-- commands: List[Path]         # Slash command directories
|-- app_config: Dict             # Project-specific settings
```

**Behavior**:
- `load()`: Finds and parses `.cxc.yaml` from project root upward
- `get_agents_dir(cxc_id)`: Returns path for workflow artifacts
- `get_trees_dir()`: Returns base path for worktrees
- Expands `${CxC_FRAMEWORK}` variable in command paths

#### 2.1.2 State Management (CxCState)

**Responsibility**: Persist and retrieve workflow state across process restarts.

**Data Model**:
```
CxCStateData (Pydantic)
|-- cxc_id: str                  # Required: Unique workflow ID
|-- issue_number: Optional[str]   # GitHub issue reference
|-- branch_name: Optional[str]    # Feature branch name
|-- plan_file: Optional[str]      # Spec file path
|-- issue_class: Optional[str]    # /feature, /bug, /chore, /patch
|-- worktree_path: Optional[str]  # Isolated worktree directory
|-- backend_port: Optional[int]   # Allocated backend port
|-- frontend_port: Optional[int]  # Allocated frontend port
|-- model_set: Optional[str]      # "base" or "heavy"
|-- all_cxcs: List[str]          # Phases executed in workflow
```

**Behavior**:
- Constructor requires valid `cxc_id`
- `update(**kwargs)`: Filters and updates only core fields
- `save(workflow_step)`: Persists to JSON with logging
- `load(cxc_id)`: Class method to retrieve existing state
- `from_stdin()`: Parse piped JSON input
- `to_stdout()`: Emit JSON for piping
- `get_working_directory()`: Returns worktree_path or project_root
- `get_state_path()`: Returns full path to state JSON file

**State File Location**:
```
{artifacts_dir}/{org}/{repo}/{cxc_id}/cxc_state.json
```

#### 2.1.3 Agent Execution (execute_template)

**Responsibility**: Execute Claude Code with slash command templates.

**Input Model**:
```
AgentTemplateRequest
|-- agent_name: str              # Identifier for logging
|-- slash_command: str           # Command name (e.g., /implement)
|-- args: List[str]              # Arguments for template
|-- cxc_id: str                  # Workflow ID for artifacts
|-- working_dir: Optional[str]   # Directory for execution
|-- model_set: Optional[str]     # Model selection override
```

**Output Model**:
```
AgentPromptResponse
|-- success: bool                # Execution outcome
|-- output: str                  # Result text
|-- session_id: Optional[str]    # Claude session ID
|-- duration_ms: Optional[int]   # Execution time
|-- cost_usd: Optional[float]    # API cost
```

**Behavior**:
1. Load template from command file path
2. Substitute `$ARGUMENTS` and positional placeholders ($1, $2, etc.)
3. Execute Claude Code CLI with:
   - `-p "<prompt>"` for prompt content
   - `--output-format stream-json` for structured output
   - `--dangerously-skip-permissions` for automation
   - `--cwd <working_dir>` for directory context
   - `--model <model>` based on command type
4. Parse JSONL output to find result message
5. Log prompt and response to artifacts directory
6. Return AgentPromptResponse with extracted result

**Model Selection Logic**:
- Heavy (Opus): `/implement`, `/document`, `/feature`, `/bug`, `/chore`, `/patch`
- Base (Sonnet): All other commands

#### 2.1.4 Data Types

**Core Literals**:
```
IssueClassSlashCommand: /feature | /bug | /chore | /patch
SlashCommand: All supported command names
ModelSet: base | heavy | haiku
ModelLiteral: Model identifiers for Claude variants
```

**GitHub Models**:
```
GitHubIssue
|-- number: int
|-- title: str
|-- body: Optional[str]
|-- state: str
|-- author: Dict
|-- labels: List[Dict]
|-- assignees: List[Dict]
|-- milestone: Optional[Dict]
|-- comments: List[Dict]
|-- createdAt: str
|-- updatedAt: str
|-- url: str
```

**Test Result Models**:
```
TestResult
|-- test_name: str
|-- passed: bool
|-- error: Optional[str]
|-- execution_command: Optional[str]
|-- test_path: Optional[str]

E2ETestResult
|-- test_name: str
|-- test_path: str
|-- passed: bool
|-- error: Optional[str]
|-- screenshots: List[str]
```

**Review Models**:
```
ReviewResult
|-- success: bool
|-- review_summary: str
|-- review_issues: List[ReviewIssue]
|-- screenshots: List[str]

ReviewIssue
|-- review_issue_number: int
|-- screenshot_path: Optional[str]
|-- issue_description: str
|-- issue_resolution: str
|-- issue_severity: "skippable" | "tech_debt" | "blocker"
```

### 2.2 Integration Components

#### 2.2.1 GitHub Integration (github.py)

**Functions**:
- `get_repo_url()`: Get remote origin URL from git
- `extract_repo_path(url)`: Parse org/repo from URL
- `fetch_issue(issue_number, repo_path)`: Get issue via `gh issue view`
- `make_issue_comment(issue_number, body)`: Post comment via `gh issue comment`
- `get_issue_comments(issue_number)`: List comments for issue
- `list_open_issues()`: Get unprocessed issues

**Comment Posting Control**:
- Environment variable `CxC_DISABLE_GITHUB_COMMENTS` suppresses posting
- All comments formatted with CxC ID and agent name prefix

#### 2.2.2 Git Operations (git_ops.py)

**Functions**:
- `create_branch(branch_name)`: Create and checkout feature branch
- `commit_changes(message, cwd)`: Stage and commit all changes
- `push_to_remote(branch_name, cwd)`: Push branch to origin
- `finalize_git_operations(state, logger, cwd)`: Complete git workflow
- `get_pr_number(branch_name)`: Find existing PR for branch
- `update_pr_body(pr_number, body)`: Append to PR description

#### 2.2.3 Workflow Operations (workflow_ops.py)

**Functions**:
- `ensure_cxc_id(issue_number, provided_id)`: Generate or validate CxC ID
- `classify_issue(issue, cxc_id, logger)`: Get issue type via agent
- `classify_issue_and_generate_branch(issue, cxc_id, logger)`: Combined operation
- `create_commit(agent, issue, issue_class, cxc_id, logger, cwd)`: Generate commit
- `format_issue_message(cxc_id, agent, message)`: Format comment body
- `post_artifact_to_issue(issue, cxc_id, artifact, label)`: Post with collapsible
- `post_state_to_issue(issue, cxc_id, state_data, label)`: Post state summary

**CxC ID Generation**:
- 8 characters, alphanumeric, lowercase
- Generated via hashlib from timestamp + random
- Unique per workflow instance

#### 2.2.4 Worktree Operations (worktree_ops.py)

**Functions**:
- `create_worktree(cxc_id, branch_name, state, logger)`: Set up isolated env
- `allocate_ports(cxc_id, config)`: Deterministic port assignment
- `validate_worktree(cxc_id, state)`: Check worktree exists
- `cleanup_worktree(cxc_id)`: Remove worktree and directory

**Port Allocation Algorithm**:
```
hash = hashlib.md5(cxc_id.encode()).hexdigest()
index = int(hash[:8], 16) % ports.backend_count
backend_port = ports.backend_start + index
frontend_port = ports.frontend_start + index
```

**Worktree Creation Steps**:
1. Calculate port allocation from CxC ID
2. Create worktree under `{artifacts_dir}/{project_id}/trees/{cxc_id}`
3. Checkout specified branch in worktree
4. Write `.ports.env` file with BACKEND_PORT and FRONTEND_PORT
5. Run install script if configured
6. Update state with worktree_path and ports

### 2.3 Workflow Components

#### 2.3.1 Phase: Plan (plan_iso.py)

**Entry**: `cxc plan <issue-number> [cxc-id]`

**Flow**:
```
START
  |
  v
Load environment (.env)
  |
  v
Generate or load CxC ID
  |
  v
Fetch GitHub issue
  |
  v
Classify issue type
  |
  v
Generate branch name
  |
  v
Create worktree with ports
  |
  v
Execute planning agent (/feature, /bug, /chore)
  |
  v
Commit plan to branch
  |
  v
Push and create PR
  |
  v
Save state
  |
  v
END (exit 0)
```

**Outputs**:
- Spec file at `specs/issue-{number}-cxc-{id}-{slug}.md`
- State file with all workflow metadata
- PR created and linked to issue
- GitHub issue comments with progress

#### 2.3.2 Phase: Build (build_iso.py)

**Entry**: `cxc build <issue-number> <cxc-id>`

**Flow**:
```
START
  |
  v
Load existing state
  |
  v
Validate worktree exists
  |
  v
Read spec file path from state
  |
  v
Execute /implement with spec file
  |
  v
Commit implementation changes
  |
  v
Push and update PR
  |
  v
Save state
  |
  v
END (exit 0)
```

**Constraints**:
- Requires CxC ID (cannot create worktree)
- Fails if worktree missing or spec file not found

#### 2.3.3 Phase: Test (test_iso.py)

**Entry**: `cxc test <issue-number> <cxc-id> [--skip-e2e]`

**Flow**:
```
START
  |
  v
Load existing state
  |
  v
Validate worktree exists
  |
  v
Run unit tests (/test)
  |
  v
Parse test results
  |
  +--> Failed? --> Attempt resolution (/resolve_failed_test)
  |                     |
  |                     v
  |               Retry up to 4 times
  |                     |
  +<--------------------+
  |
  v
Run E2E tests (/test_e2e) if not skipped
  |
  v
Parse E2E results
  |
  +--> Failed? --> Attempt resolution (/resolve_failed_e2e_test)
  |                     |
  |                     v
  |               Retry up to 2 times
  |                     |
  +<--------------------+
  |
  v
Post comprehensive summary
  |
  v
Commit test changes
  |
  v
Push and update PR
  |
  v
Save state
  |
  v
END (exit code based on failures)
```

**Retry Logic**:
- Unit tests: MAX_TEST_RETRY_ATTEMPTS = 4
- E2E tests: MAX_E2E_TEST_RETRY_ATTEMPTS = 2
- Stops retrying if no tests resolved in iteration

#### 2.3.4 Phase: Review (review_iso.py)

**Entry**: `cxc review <issue-number> <cxc-id> [--skip-resolution]`

**Flow**:
```
START
  |
  v
Load existing state
  |
  v
Validate worktree exists
  |
  v
Read spec file path from state
  |
  v
Execute /review with spec file
  |
  v
Parse review JSON result
  |
  v
Upload screenshots to R2 (if configured)
  |
  v
Check for blocker issues
  |
  +--> Blockers found? --> Create patch plan (/patch)
  |                              |
  |                              v
  |                        Implement patch
  |                              |
  |                              v
  |                        Retry review (max 3 times)
  |                              |
  +<-----------------------------+
  |
  v
Update PR body with review results
  |
  v
Post summary to issue
  |
  v
Save state
  |
  v
END (exit 0 if success, 1 if blockers remain)
```

**Issue Severity Handling**:
- `skippable`: Non-blocking, informational
- `tech_debt`: Non-blocking, tracked for future
- `blocker`: Triggers patch flow unless --skip-resolution

#### 2.3.5 Phase: Document (document_iso.py)

**Entry**: `cxc document <issue-number> <cxc-id>`

**Flow**:
```
START
  |
  v
Load existing state
  |
  v
Validate worktree exists
  |
  v
Check for changes against main
  |
  +--> No changes? --> Skip documentation
  |
  v
Read spec file and review screenshots
  |
  v
Execute /document with spec file
  |
  v
Commit documentation changes
  |
  v
Track agentic KPIs (never fails)
  |
  v
Push and update PR
  |
  v
Save state
  |
  v
END (exit 0 always)
```

**Documentation Output**:
- File at `app_docs/feature-{cxc_id}-{name}.md`
- Screenshots copied to `app_docs/assets/`
- Entry added to `conditional_docs.md`

#### 2.3.6 Phase: Ship (ship_iso.py)

**Entry**: `cxc ship <issue-number> <cxc-id>`

**Flow**:
```
START
  |
  v
Load existing state
  |
  v
Validate all required fields present
  |
  v
Validate worktree exists
  |
  v
Approve PR (gh pr review --approve)
  |
  v
Merge to main (no-ff)
  |
  v
Push main to origin
  |
  v
Close GitHub issue
  |
  v
Post success message
  |
  v
Save final state
  |
  v
END (exit 0)
```

#### 2.3.7 Orchestration: SDLC (sdlc_iso.py)

**Entry**: `cxc sdlc <issue-number> [cxc-id] [--skip-e2e] [--skip-resolution]`

**Flow**:
```
START
  |
  v
Generate or load CxC ID (ensure_cxc_id)
  |
  v
Print "== PHASE 1: PLANNING =="
  |
  v
Run plan_iso
  |
  +--> Failed? --> EXIT 1
  |
  v
Print "== PHASE 2: BUILDING =="
  |
  v
Run build_iso
  |
  +--> Failed? --> EXIT 1
  |
  v
Print "== PHASE 3: TESTING =="
  |
  v
Run test_iso (with --skip-e2e if set)
  |
  +--> Failed? --> Print WARNING, continue
  |
  v
Print "== PHASE 4: REVIEWING =="
  |
  v
Run review_iso (with --skip-resolution if set)
  |
  +--> Failed? --> EXIT 1
  |
  v
Print "== PHASE 5: DOCUMENTING =="
  |
  v
Run document_iso
  |
  +--> Failed? --> Print WARNING, continue
  |
  v
Print "SDLC COMPLETED"
  |
  v
END (exit 0)
```

**Phase Dependencies**:
- plan: No dependencies
- build: Requires plan success
- test: Requires build success, continues on failure
- review: Requires test completion (not success)
- document: Requires review success, continues on failure

#### 2.3.8 Orchestration: ZTE (sdlc_zte_iso.py)

**Entry**: `cxc zte <issue-number> [cxc-id] [--skip-e2e] [--skip-resolution]`

**Extends SDLC with**:
- Stricter test failure handling (stops on test failure)
- Automatic ship phase on success
- Full automation from issue to merged code

### 2.4 Trigger Components

#### 2.4.1 Webhook Trigger (trigger_webhook.py)

**Architecture**:
```
FastAPI App
  |
  +-- POST /gh-webhook
  |     |
  |     +-- Parse GitHub event
  |     +-- Extract CxC commands from body/comment
  |     +-- Launch workflow subprocess
  |     +-- Return 200 immediately
  |
  +-- GET /health
        |
        +-- Return service status
```

**Command Detection**:
- Searches for `cxc_plan_iso`, `cxc_sdlc_iso`, `cxc_sdlc_zte_iso` in text
- Extracts CxC ID if pattern `cxc-<id>` found
- Detects `model_set heavy` for Opus selection
- Ignores comments from CxC bot to prevent loops

**Subprocess Launch**:
```
subprocess.Popen(
    ["uv", "run", "python", "-m", f"cxc.workflows.wt.{workflow}", issue_number, cxc_id],
    start_new_session=True,
    ...
)
```

#### 2.4.2 Cron Trigger (trigger_cron.py)

**Architecture**:
```
Polling Loop (20s interval)
  |
  +-- Fetch open issues
  |
  +-- For each issue:
  |     |
  |     +-- Check if already processed
  |     +-- Check for CxC command in comments
  |     +-- Launch plan workflow if qualifying
  |
  +-- Sleep and repeat
```

---

## 3. Data Flow Diagrams

### 3.1 Full SDLC Data Flow

```
GitHub Issue (#42)
       |
       v
+------+------+
|   PLAN      |
|   PHASE     |
+------+------+
       |
       | Creates:
       | - Worktree at artifacts/org/repo/trees/abc12345/
       | - Spec file at specs/issue-42-cxc-abc12345-add-auth.md
       | - State file at artifacts/org/repo/abc12345/cxc_state.json
       | - Branch: feat-issue-42-cxc-abc12345-add-user-auth
       | - PR #100
       v
+------+------+
|   BUILD     |
|   PHASE     |
+------+------+
       |
       | Uses:
       | - Spec file from state
       | - Worktree as working directory
       |
       | Creates:
       | - Implementation code
       | - Commits to branch
       v
+------+------+
|   TEST      |
|   PHASE     |
+------+------+
       |
       | Runs in worktree:
       | - Unit tests
       | - E2E tests (if not skipped)
       |
       | Creates:
       | - Test result commits
       v
+------+------+
|   REVIEW    |
|   PHASE     |
+------+------+
       |
       | Uses:
       | - Spec file for requirements
       | - Git diff for changes
       |
       | Creates:
       | - Screenshots in agents/{cxc_id}/review_img/
       | - Review summary in PR
       v
+------+------+
|  DOCUMENT   |
|   PHASE     |
+------+------+
       |
       | Creates:
       | - Feature doc at app_docs/feature-abc12345-add-auth.md
       | - Entry in conditional_docs.md
       v
+------+------+
|    SHIP     |
|   PHASE     |
+------+------+
       |
       | Actions:
       | - Approve PR
       | - Merge to main
       | - Close issue #42
       v
    COMPLETE
```

### 3.2 State Flow

```
Initial State (plan creates):
{
  "cxc_id": "abc12345",
  "issue_number": "42",
  "branch_name": "feat-issue-42-cxc-abc12345-add-user-auth",
  "plan_file": "specs/issue-42-cxc-abc12345-add-user-auth.md",
  "issue_class": "/feature",
  "worktree_path": "/path/to/artifacts/org/repo/trees/abc12345",
  "backend_port": 9103,
  "frontend_port": 9203,
  "model_set": "base",
  "all_cxcs": ["cxc_plan_iso"]
}

After build:
{
  ...,
  "all_cxcs": ["cxc_plan_iso", "cxc_build_iso"]
}

After test:
{
  ...,
  "all_cxcs": ["cxc_plan_iso", "cxc_build_iso", "cxc_test_iso"]
}

... continues through phases
```

### 3.3 Agent Execution Flow

```
Workflow Phase
       |
       v
AgentTemplateRequest {
  agent_name: "sdlc_planner",
  slash_command: "/feature",
  args: [issue_json],
  cxc_id: "abc12345",
  working_dir: "/path/to/worktree"
}
       |
       v
execute_template()
       |
       +-- Load template from commands/feature.md
       |
       +-- Substitute $ARGUMENTS with issue_json
       |
       +-- Build Claude Code command:
       |   claude -p "..." --model sonnet --output-format stream-json
       |   --dangerously-skip-permissions --cwd /path/to/worktree
       |
       +-- Execute subprocess
       |
       +-- Parse JSONL output
       |
       +-- Extract result message
       |
       v
AgentPromptResponse {
  success: true,
  output: "specs/issue-42-cxc-abc12345-add-user-auth.md",
  session_id: "session-xyz",
  duration_ms: 45000,
  cost_usd: 0.15
}
       |
       v
Workflow continues with output
```

---

## 4. State Management Approach

### 4.1 Persistence Strategy

**File-based JSON persistence** was chosen for:
- Human readability for debugging
- No external dependencies (no database)
- Git-friendly for potential versioning
- Simple recovery (just edit the JSON)

**State File Schema**:
```json
{
  "cxc_id": "string (required)",
  "issue_number": "string (optional)",
  "branch_name": "string (optional)",
  "plan_file": "string (optional)",
  "issue_class": "string (optional)",
  "worktree_path": "string (optional)",
  "backend_port": "integer (optional)",
  "frontend_port": "integer (optional)",
  "model_set": "string (optional)",
  "all_cxcs": ["list of strings"]
}
```

### 4.2 State Transitions

```
NULL --> INITIALIZED (cxc_id only)
     --> PLANNED (+ issue_number, branch_name, plan_file, issue_class, worktree_path, ports)
     --> BUILT (no new fields, all_cxcs updated)
     --> TESTED (no new fields, all_cxcs updated)
     --> REVIEWED (no new fields, all_cxcs updated)
     --> DOCUMENTED (no new fields, all_cxcs updated)
     --> SHIPPED (final state)
```

### 4.3 State Location Convention

```
{artifacts_dir}/
|-- {org}/
    |-- {repo}/
        |-- {cxc_id}/
        |   |-- cxc_state.json        # Workflow state
        |   |-- ops/
        |   |   |-- prompts/          # Saved agent prompts
        |   |-- sdlc_planner/         # Planning artifacts
        |   |-- sdlc_implementor/     # Build artifacts
        |   |-- tester/               # Test artifacts
        |   |-- reviewer/             # Review artifacts
        |   |   |-- review_img/       # Screenshots
        |-- trees/
            |-- {cxc_id}/             # Git worktree
                |-- .ports.env        # Port configuration
                |-- ...               # Full repo checkout
```

---

## 5. Integration Patterns

### 5.1 Claude Code Integration

**Execution Pattern**:
1. Prepare prompt from template
2. Write prompt to file for logging
3. Execute via subprocess with JSONL output
4. Stream output to file
5. Parse JSONL to find result message
6. Return structured response

**Error Handling**:
- Non-zero exit code: Return success=False with stderr
- Parse error: Return success=False with raw output
- Timeout: Return success=False with timeout message

### 5.2 GitHub Integration

**Pattern**: All GitHub operations via `gh` CLI (no direct API calls)

**Benefits**:
- Automatic authentication via `gh auth`
- Consistent behavior with user's GitHub setup
- No token management in application

**Operations**:
```
gh issue view --json ...        # Fetch issue
gh issue comment -b "..."       # Post comment
gh pr create --title --body     # Create PR
gh pr merge --no-ff            # Merge PR
gh pr review --approve         # Approve PR
```

### 5.3 Git Integration

**Worktree Pattern**:
```
git worktree add <path> -b <branch>   # Create worktree
git worktree remove <path>            # Clean up worktree
```

**Operations in Worktree**:
All git commands include `--git-dir` and `--work-tree` or run with `cwd=worktree_path`

---

## 6. Extension Points

### 6.1 Adding New Commands

1. Create markdown template in `commands/` directory
2. Use `$ARGUMENTS` placeholder for dynamic content
3. Use `$1`, `$2`, etc. for positional arguments
4. Return structured output for parsing

### 6.2 Adding New Workflows

1. Create module in `cxc/workflows/wt/`
2. Implement `main()` function accepting CLI args
3. Use shared operations from `workflow_ops.py`
4. Add CLI routing in `cli.py`

### 6.3 Adding New Integrations

1. Create module in `cxc/integrations/`
2. Follow existing patterns (no exceptions, return tuples)
3. Use `subprocess.run` for external commands
4. Log operations via passed logger

### 6.4 Overriding Commands

1. Create `commands/` directory in project
2. Add command file with same name as framework command
3. Project commands take precedence

---

## 7. Error Handling Strategy

### 7.1 Philosophy

**Explicit Failure**: Rather than catch-all exception handling, the framework:
- Lets errors propagate to identify root causes
- Returns explicit (success, error) tuples from operations
- Fails fast on invalid state

### 7.2 Error Response Patterns

**Integration Layer**:
```
def operation(...) -> Tuple[result, Optional[str]]:
    # Returns (result, None) on success
    # Returns (None, error_message) on failure
```

**Workflow Layer**:
```
result, error = some_operation(...)
if error:
    logger.error(f"Operation failed: {error}")
    make_issue_comment(issue, f"Error: {error}")
    sys.exit(1)
```

### 7.3 Recovery Mechanisms

- **State persistence**: Resume interrupted workflows
- **Worktree isolation**: Failures don't affect other workflows
- **Test retry**: Automatic resolution and retry
- **Review retry**: Patch and retry on blockers

---

## 8. Security Considerations

### 8.1 Credential Management

- All secrets in `.env` file (not in code or config)
- `GITHUB_PAT` optional (falls back to `gh auth`)
- Safe subprocess environment filtering

### 8.2 Subprocess Security

```python
def get_safe_subprocess_env():
    """Return filtered environment for subprocess calls."""
    safe_vars = [
        "PATH", "HOME", "USER", "SHELL", "TERM",
        "ANTHROPIC_API_KEY", "GITHUB_PAT", "GH_TOKEN",
        "CLOUDFLARE_*"  # R2 credentials
    ]
    return {k: v for k, v in os.environ.items() if any(k.startswith(p.rstrip('*')) for p in safe_vars)}
```

### 8.3 Code Execution Safety

- Claude Code runs with `--dangerously-skip-permissions` (required for automation)
- Worktrees provide isolation between workflows
- All code changes go through PR review process
