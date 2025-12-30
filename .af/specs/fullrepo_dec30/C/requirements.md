# ADW Framework Requirements Specification (Claude)

**Version:** 1.0.0
**Date:** 2025-12-30
**Status:** Complete

---

## 1. Overview

This document defines all system requirements for the ADW (AI Developer Workflow) Framework, an orchestration system that automates software development using Claude Code agents in isolated git worktrees.

---

## 2. Requirement Categories

| Category                   | ID Prefix | Description                                      |
| :------------------------- | :-------- | :----------------------------------------------- |
| Workflow Requirements      | WF        | SDLC pipeline phases and chaining                |
| Trigger Requirements       | TR        | Invocation mechanisms                            |
| State Management           | ST        | Persistence and artifact tracking                |
| Integration Requirements   | IN        | External system interfaces                       |
| Agent Requirements         | AG        | Claude Code agent execution                      |
| Configuration Requirements | CF        | Project setup and environment                    |
| Command Template           | CT        | Slash command template system                    |
| Testing Requirements       | TS        | Test suite and validation                        |

---

## 3. Workflow Requirements (WF)

### WF-001: Plan Phase

| Attribute             | Value                                                                  |
| :-------------------- | :--------------------------------------------------------------------- |
| **ID**                | WF-001                                                                 |
| **Title**             | Planning Phase Workflow                                                |
| **Priority**          | P0 (Critical)                                                          |
| **Description**       | Transform GitHub issue into implementation plan with isolated worktree |
| **Acceptance Criteria** |                                                                      |

1. Fetch GitHub issue details via `gh` CLI
2. Generate unique 8-character ADW ID
3. Classify issue as `/feature`, `/bug`, `/chore`, or `/patch`
4. Generate standardized branch name: `<type>-issue-<number>-adw-<adw_id>-<slug>`
5. Create isolated git worktree at `trees/<adw_id>/`
6. Allocate deterministic ports (backend: 9100-9114, frontend: 9200-9214)
7. Setup worktree environment with `.ports.env` file
8. Execute appropriate planning template (`/feature`, `/bug`, `/chore`)
9. Create plan file at `specs/issue-<number>-adw-<adw_id>-<name>.md`
10. Commit plan and push to remote
11. Create/update pull request
12. Post progress updates to GitHub issue

**Dependencies:** GitHub issue exists, `gh` CLI authenticated
**Source Files:** `adw/workflows/wt/plan_iso.py`

---

### WF-002: Build Phase

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | WF-002                                                 |
| **Title**             | Implementation Phase Workflow                          |
| **Priority**          | P0 (Critical)                                          |
| **Description**       | Execute implementation plan in isolated worktree       |
| **Acceptance Criteria** |                                                      |

1. Require existing ADW state with valid worktree
2. Load plan file path from state
3. Checkout feature branch in worktree
4. Execute `/implement` template with plan file content
5. Post implementation report to GitHub issue
6. Commit implementation changes
7. Push and update PR

**Dependencies:** WF-001 completed, plan file exists
**Source Files:** `adw/workflows/wt/build_iso.py`

---

### WF-003: Test Phase

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | WF-003                                                 |
| **Title**             | Testing Phase Workflow with Auto-Resolution            |
| **Priority**          | P0 (Critical)                                          |
| **Description**       | Run tests with automatic failure resolution and retry  |
| **Acceptance Criteria** |                                                      |

1. Validate worktree exists via state
2. Run unit test suite via `/test` template
3. Parse JSON test results into `TestResult` objects
4. If failures exist, attempt resolution via `/resolve_failed_test` (max 4 attempts)
5. Re-run tests after resolution attempts
6. Run E2E tests via `/test_e2e` if not skipped (max 2 retry attempts)
7. Resolve E2E failures via `/resolve_failed_e2e_test`
8. Post comprehensive test summary to issue
9. Commit test results
10. Exit with error code if unresolved failures remain

**Dependencies:** WF-002 completed
**Source Files:** `adw/workflows/wt/test_iso.py`
**Constants:**
- `MAX_TEST_RETRY_ATTEMPTS = 4`
- `MAX_E2E_TEST_RETRY_ATTEMPTS = 2`

---

### WF-004: Review Phase

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | WF-004                                                 |
| **Title**             | Code Review Phase Workflow                             |
| **Priority**          | P1 (High)                                              |
| **Description**       | Validate implementation against specification          |
| **Acceptance Criteria** |                                                      |

1. Find spec file matching current branch
2. Run `git diff origin/main` to analyze changes
3. Execute `/review` template with spec file path
4. Capture screenshots of critical functionality (1-5 screenshots)
5. Parse review results into JSON structure
6. Identify blocking vs non-blocking issues
7. If blocking issues, optionally create patch plan
8. Post review report with screenshots to issue

**Dependencies:** WF-003 completed
**Source Files:** `adw/workflows/wt/review_iso.py`, `commands/review.md`
**Output Structure:**
```json
{
  "success": "boolean",
  "review_summary": "string",
  "review_issues": [
    {
      "review_issue_number": "number",
      "screenshot_path": "string",
      "issue_description": "string",
      "issue_resolution": "string",
      "issue_severity": "skippable|tech_debt|blocker"
    }
  ],
  "screenshots": ["string"]
}
```

---

### WF-005: Document Phase

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | WF-005                                                 |
| **Title**             | Documentation Generation Phase                         |
| **Priority**          | P2 (Medium)                                            |
| **Description**       | Generate feature documentation from implementation     |
| **Acceptance Criteria** |                                                      |

1. Analyze git diff against main branch
2. Read specification file if provided
3. Copy review screenshots to `app_docs/assets/`
4. Generate documentation at `app_docs/feature-<adw_id>-<name>.md`
5. Update conditional documentation index
6. Follow standardized documentation format

**Dependencies:** WF-004 completed
**Source Files:** `adw/workflows/wt/document_iso.py`, `commands/document.md`

---

### WF-006: Ship Phase

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | WF-006                                                 |
| **Title**             | Pull Request Approval and Merge                        |
| **Priority**          | P1 (High)                                              |
| **Description**       | Approve and merge PR for zero-touch execution          |
| **Acceptance Criteria** |                                                      |

1. Validate all previous phases completed
2. Approve PR via `gh pr review --approve`
3. Merge PR via `gh pr merge --squash`
4. Post completion message to issue
5. Clean up worktree (optional)

**Dependencies:** WF-005 completed, all tests pass
**Source Files:** `adw/workflows/wt/ship_iso.py`

---

### WF-007: SDLC Pipeline Orchestration

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | WF-007                                                 |
| **Title**             | Complete SDLC Pipeline Execution                       |
| **Priority**          | P0 (Critical)                                          |
| **Description**       | Chain all phases into single automated workflow        |
| **Acceptance Criteria** |                                                      |

1. Execute phases in order: plan -> build -> test -> review -> document
2. Pass ADW ID between phases for state continuity
3. Support `--skip-e2e` flag to bypass E2E tests
4. Support `--skip-resolution` flag to bypass review resolution
5. Continue on test warnings, halt on blocking errors
6. Report final status with worktree location

**Dependencies:** All phase workflows implemented
**Source Files:** `adw/workflows/wt/sdlc_iso.py`
**CLI Invocation:** `uv run adw sdlc <issue-number> [adw-id] [--skip-e2e] [--skip-resolution]`

---

### WF-008: Zero-Touch Execution (ZTE)

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | WF-008                                                 |
| **Title**             | SDLC with Automatic PR Merge                           |
| **Priority**          | P1 (High)                                              |
| **Description**       | Full SDLC pipeline with automated PR approval/merge    |
| **Acceptance Criteria** |                                                      |

1. Execute complete SDLC pipeline (WF-007)
2. If all tests pass and no blocking review issues, execute ship phase
3. Auto-approve and merge PR without human intervention

**Dependencies:** WF-007 completed successfully
**Source Files:** `adw/workflows/wt/sdlc_zte_iso.py`
**CLI Invocation:** `uv run adw zte <issue-number> [adw-id]`

---

### WF-009: Patch Workflow

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | WF-009                                                 |
| **Title**             | Focused Patch for Review Issues                        |
| **Priority**          | P2 (Medium)                                            |
| **Description**       | Create targeted fixes for review-identified issues     |
| **Acceptance Criteria** |                                                      |

1. Read original spec and review issues
2. Generate focused patch plan at `specs/patch/`
3. Implement minimal fixes
4. Re-run validation to confirm resolution

**Dependencies:** Review phase identified issues
**Source Files:** `adw/workflows/wt/patch_iso.py`, `commands/patch.md`

---

## 4. Trigger Requirements (TR)

### TR-001: CLI Invocation

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | TR-001                                                 |
| **Title**             | Command Line Interface Triggers                        |
| **Priority**          | P0 (Critical)                                          |
| **Description**       | Invoke workflows via `adw` CLI command                 |
| **Acceptance Criteria** |                                                      |

1. Entry point: `adw.cli:main`
2. Support commands: `plan`, `build`, `test`, `review`, `document`, `ship`, `sdlc`, `zte`
3. Accept `<issue-number>` as required argument
4. Accept optional `[adw-id]` to resume existing workflow
5. Accept flags: `--skip-e2e`, `--skip-resolution`
6. Provide `--help` documentation

**Source Files:** `adw/cli.py`
**Installation:** `uv sync` (via pyproject.toml scripts entry)

---

### TR-002: GitHub Webhook Trigger

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | TR-002                                                 |
| **Title**             | GitHub Issue Comment Webhook                           |
| **Priority**          | P1 (High)                                              |
| **Description**       | Trigger workflows via issue comments                   |
| **Acceptance Criteria** |                                                      |

1. FastAPI webhook endpoint at `/api/github/issue_comment`
2. Parse comment body for magic keywords:
   - `adw_plan_iso` - Plan only
   - `adw_build_iso` - Build only
   - `adw_test_iso` - Test only
   - `adw_review_iso` - Review only
   - `adw_document_iso` - Document only
   - `adw_ship_iso` - Ship only
   - `adw_sdlc_iso` - Full SDLC
   - `adw_sdlc_zte_iso` - Full SDLC with auto-merge
   - `model_set heavy` - Use Opus model
3. Extract `adw_id` from comment if provided
4. Spawn workflow as background subprocess
5. Verify webhook signature from GitHub

**Source Files:** `adw/triggers/trigger_webhook.py`
**Dependencies:** FastAPI, uvicorn

---

### TR-003: Cron Polling Trigger

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | TR-003                                                 |
| **Title**             | Scheduled Issue Polling                                |
| **Priority**          | P3 (Low)                                               |
| **Description**       | Poll GitHub issues on schedule for auto-processing     |
| **Acceptance Criteria** |                                                      |

1. Configurable polling interval
2. Filter issues by label or state
3. Track processed issues to avoid duplicates
4. Trigger appropriate workflow based on issue metadata

**Source Files:** `adw/triggers/trigger_cron.py`
**Dependencies:** schedule library

---

## 5. State Management Requirements (ST)

### ST-001: ADW State Persistence

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | ST-001                                                 |
| **Title**             | Persistent Workflow State                              |
| **Priority**          | P0 (Critical)                                          |
| **Description**       | Track workflow progress across phases                  |
| **Acceptance Criteria** |                                                      |

1. State file at `artifacts/{project_id}/{adw_id}/adw_state.json`
2. Track fields:
   - `adw_id`: 8-char unique identifier
   - `issue_number`: GitHub issue number
   - `branch_name`: Feature branch name
   - `plan_file`: Path to implementation plan
   - `issue_class`: `/feature`, `/bug`, `/chore`, `/patch`
   - `worktree_path`: Absolute path to worktree
   - `backend_port`: Allocated backend port
   - `frontend_port`: Allocated frontend port
   - `model_set`: `base` or `heavy`
   - `adw_workflow_history`: List of executed phases
3. Automatic save after each update
4. Load by ADW ID for phase resumption

**Source Files:** `adw/core/state.py`
**Class:** `ADWState`

---

### ST-002: ADW ID Generation

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | ST-002                                                 |
| **Title**             | Unique Workflow Identifier Generation                  |
| **Priority**          | P0 (Critical)                                          |
| **Description**       | Generate and manage 8-character workflow identifiers   |
| **Acceptance Criteria** |                                                      |

1. Generate via `uuid.uuid4()[:8]`
2. Use for:
   - State file directory name
   - Worktree directory name
   - Branch name component
   - Log file organization
   - Port allocation hash

**Source Files:** `adw/core/utils.py`
**Function:** `make_adw_id()`

---

### ST-003: Artifact Directory Structure

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | ST-003                                                 |
| **Title**             | Organized Artifact Storage                             |
| **Priority**          | P1 (High)                                              |
| **Description**       | Standardized directory structure for outputs           |
| **Acceptance Criteria** |                                                      |

```
artifacts/{org}/{repo}/
  {adw-id}/
    adw_state.json            # Workflow state
    ops/
      prompts/                # Saved agent prompts
    sdlc_planner/
      raw_output.jsonl        # Planning agent output
    sdlc_implementor/
      raw_output.jsonl        # Build agent output
    test_runner/
      raw_output.jsonl        # Test agent output
    reviewer/
      review_img/             # Review screenshots
      raw_output.jsonl        # Review agent output
  trees/
    {adw-id}/                 # Git worktree checkout
```

**Source Files:** `adw/core/config.py`

---

### ST-004: Prompt and Output Logging

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | ST-004                                                 |
| **Title**             | Agent Prompt and Response Archival                     |
| **Priority**          | P2 (Medium)                                            |
| **Description**       | Store all agent interactions for debugging             |
| **Acceptance Criteria** |                                                      |

1. Save each prompt to `artifacts/{id}/{agent}/prompts/{timestamp}.md`
2. Save raw JSONL output to `artifacts/{id}/{agent}/raw_output.jsonl`
3. Parse JSONL for result extraction
4. Track execution duration and cost

**Source Files:** `adw/core/agent.py`

---

## 6. Integration Requirements (IN)

### IN-001: GitHub API Integration

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | IN-001                                                 |
| **Title**             | GitHub Operations via CLI                              |
| **Priority**          | P0 (Critical)                                          |
| **Description**       | Interface with GitHub using `gh` CLI                   |
| **Acceptance Criteria** |                                                      |

1. Fetch issue details: `gh issue view <number> --json`
2. Create/update issue comments: `gh issue comment`
3. Create PR: `gh pr create`
4. List PRs: `gh pr list --head <branch>`
5. Review PR: `gh pr review --approve`
6. Merge PR: `gh pr merge --squash`
7. Support authentication via `GITHUB_PAT` env var or `gh auth`

**Source Files:** `adw/integrations/github.py`
**Functions:** `fetch_issue()`, `make_issue_comment()`, `create_pull_request()`, `list_prs()`, `get_repo_url()`

---

### IN-002: Git Operations

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | IN-002                                                 |
| **Title**             | Git Repository Operations                              |
| **Priority**          | P0 (Critical)                                          |
| **Description**       | Git branch, commit, push operations                    |
| **Acceptance Criteria** |                                                      |

1. Create branches: `git checkout -b <name>`
2. Stage changes: `git add -A`
3. Commit with message: `git commit -m "<msg>"`
4. Push to remote: `git push -u origin <branch>`
5. Get current branch: `git rev-parse --abbrev-ref HEAD`
6. Check for changes: `git status --porcelain`
7. Execute in specific working directory via `cwd` parameter

**Source Files:** `adw/integrations/git_ops.py`
**Functions:** `create_branch()`, `commit_changes()`, `push_branch()`, `get_current_branch()`, `finalize_git_operations()`

---

### IN-003: Git Worktree Management

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | IN-003                                                 |
| **Title**             | Isolated Git Worktree Operations                       |
| **Priority**          | P0 (Critical)                                          |
| **Description**       | Create and manage isolated worktrees for parallel work |
| **Acceptance Criteria** |                                                      |

1. Create worktree: `git worktree add trees/<adw_id>/ -b <branch>`
2. Validate worktree exists and is accessible
3. List worktrees: `git worktree list`
4. Remove worktree: `git worktree remove <path>`
5. Create `.ports.env` file in worktree with port assignments
6. Execute `/install_worktree` to setup dependencies

**Source Files:** `adw/integrations/worktree_ops.py`
**Functions:** `create_worktree()`, `validate_worktree()`, `setup_worktree_environment()`

---

### IN-004: Port Allocation

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | IN-004                                                 |
| **Title**             | Deterministic Port Assignment                          |
| **Priority**          | P1 (High)                                              |
| **Description**       | Allocate unique ports per workflow instance            |
| **Acceptance Criteria** |                                                      |

1. Hash ADW ID to port offset (0-14 range)
2. Backend ports: 9100-9114 (configurable start)
3. Frontend ports: 9200-9214 (configurable start)
4. Check port availability before allocation
5. Fall back to scanning for next available port
6. Store allocated ports in `.ports.env`

**Source Files:** `adw/integrations/worktree_ops.py`
**Functions:** `get_ports_for_adw()`, `is_port_available()`, `find_next_available_ports()`

---

### IN-005: Claude Code Agent Execution

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | IN-005                                                 |
| **Title**             | Claude Code CLI Wrapper                                |
| **Priority**          | P0 (Critical)                                          |
| **Description**       | Execute Claude Code with slash commands                |
| **Acceptance Criteria** |                                                      |

1. Build prompt from template file and arguments
2. Execute: `claude -p "<prompt>" --print --output-format jsonl`
3. Model selection:
   - Base (Sonnet): Default for most commands
   - Heavy (Opus): `/implement`, `/document`, `/feature`, `/bug`, `/chore`, `/patch`
4. Parse JSONL output for result extraction
5. Track session ID, duration, cost
6. Save prompts and outputs to artifact directories

**Source Files:** `adw/core/agent.py`
**Class:** `AgentTemplateRequest`, `AgentPromptResponse`
**Function:** `execute_template()`

---

## 7. Configuration Requirements (CF)

### CF-001: Project Configuration

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | CF-001                                                 |
| **Title**             | ADW YAML Configuration File                            |
| **Priority**          | P0 (Critical)                                          |
| **Description**       | Project-level ADW settings                             |
| **Acceptance Criteria** |                                                      |

1. File: `.adw.yaml` in project root
2. Required fields:
   - `project_id`: `"org/repo"` format
   - `artifacts_dir`: Path to artifacts (default: `./artifacts`)
3. Optional fields:
   - `source_root`: Source code root (default: `./src`)
   - `ports.backend_start`: Backend port range start (default: 9100)
   - `ports.backend_count`: Number of backend ports (default: 15)
   - `ports.frontend_start`: Frontend port range start (default: 9200)
   - `ports.frontend_count`: Number of frontend ports (default: 15)
   - `commands`: List of command template directories
   - `app.backend_dir`: Backend source directory
   - `app.frontend_dir`: Frontend source directory
   - `app.test_command`: Test execution command
   - `app.reset_db_script`: Database reset script path

**Source Files:** `adw/core/config.py`
**Class:** `ADWConfig`, `PortConfig`

---

### CF-002: Environment Variables

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | CF-002                                                 |
| **Title**             | Required Environment Configuration                     |
| **Priority**          | P0 (Critical)                                          |
| **Description**       | Environment variables for secrets and paths            |
| **Acceptance Criteria** |                                                      |

1. Required:
   - `ANTHROPIC_API_KEY`: Claude API key
   - `CLAUDE_CODE_PATH`: Path to `claude` executable (default: `claude`)
2. Optional:
   - `GITHUB_PAT`: GitHub personal access token (falls back to `gh auth`)
   - `E2B_API_KEY`: E2B sandbox API key
   - `CLOUDFLARED_TUNNEL_TOKEN`: Cloudflare tunnel token
3. Loaded via `python-dotenv` from `.env` file
4. Safe subprocess environment filtering

**Source Files:** `adw/core/utils.py`
**Functions:** `check_env_vars()`, `get_safe_subprocess_env()`

---

### CF-003: Worktree Port Configuration

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | CF-003                                                 |
| **Title**             | Per-Worktree Port Assignment File                      |
| **Priority**          | P1 (High)                                              |
| **Description**       | Port configuration for isolated environments           |
| **Acceptance Criteria** |                                                      |

1. File: `.ports.env` in worktree root
2. Contents:
   ```
   BACKEND_PORT=9100
   FRONTEND_PORT=9200
   ```
3. Sourced by scripts for environment-aware execution
4. Used by `/test_e2e`, `/prepare_app`, `/start` commands

**Source Files:** `adw/integrations/worktree_ops.py`

---

## 8. Command Template Requirements (CT)

### CT-001: Template Loading

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | CT-001                                                 |
| **Title**             | Slash Command Template System                          |
| **Priority**          | P0 (Critical)                                          |
| **Description**       | Load and process markdown command templates            |
| **Acceptance Criteria** |                                                      |

1. Template directories configurable in `.adw.yaml`
2. Search order: project `commands/`, framework `commands/`, `.claude/commands/`
3. Template naming: `<command>.md` maps to `/<command>`
4. Variable substitution: `$1`, `$2`, `$3` for positional args
5. `$ARGUMENTS` placeholder for raw argument passing

**Source Files:** `adw/core/agent.py`

---

### CT-002: Issue Classification Templates

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | CT-002                                                 |
| **Title**             | Issue Type Classification Commands                     |
| **Priority**          | P0 (Critical)                                          |
| **Description**       | Templates for classifying GitHub issues                |
| **Acceptance Criteria** |                                                      |

1. `/classify_issue`: Determine issue type
   - Outputs: `/feature`, `/bug`, `/chore`, `/patch`, `0`
2. `/classify_and_branch`: Combined classification + branch name
   - Outputs: JSON with `issue_class` and `branch_name`
3. Use fast model (Haiku) for classification tasks

**Source Files:** `commands/classify_issue.md`, `commands/classify_and_branch.md`

---

### CT-003: Planning Templates

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | CT-003                                                 |
| **Title**             | Implementation Planning Commands                       |
| **Priority**          | P0 (Critical)                                          |
| **Description**       | Templates for generating implementation plans          |
| **Acceptance Criteria** |                                                      |

1. `/feature`: Feature implementation plan
2. `/bug`: Bug fix plan
3. `/chore`: Maintenance task plan
4. `/patch`: Focused patch for review issues
5. Plan format includes:
   - Metadata (issue_number, adw_id)
   - Feature/bug description
   - User story
   - Problem/solution statements
   - Relevant files
   - Implementation phases
   - Step-by-step tasks
   - Testing strategy
   - Acceptance criteria
   - Validation commands

**Source Files:** `commands/feature.md`, `commands/bug.md`, `commands/chore.md`, `commands/patch.md`

---

### CT-004: Implementation Template

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | CT-004                                                 |
| **Title**             | Plan Execution Command                                 |
| **Priority**          | P0 (Critical)                                          |
| **Description**       | Template for implementing a plan                       |
| **Acceptance Criteria** |                                                      |

1. `/implement`: Execute plan from `$ARGUMENTS`
2. Read plan content
3. Implement step-by-step tasks
4. Report files changed and summary

**Source Files:** `commands/implement.md`

---

### CT-005: Review Template

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | CT-005                                                 |
| **Title**             | Code Review Command                                    |
| **Priority**          | P1 (High)                                              |
| **Description**       | Template for validating implementation                 |
| **Acceptance Criteria** |                                                      |

1. `/review`: Validate against spec file
2. Inputs: `adw_id`, `spec_file`, `agent_name`
3. Run `git diff origin/main` to see changes
4. Execute `/prepare_app` to start application
5. Capture 1-5 screenshots of critical functionality
6. Identify issues with severity levels:
   - `skippable`: Non-blocking
   - `tech_debt`: Future improvement needed
   - `blocker`: Must fix before release
7. Output JSON with success status and issues

**Source Files:** `commands/review.md`

---

### CT-006: Test Resolution Templates

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | CT-006                                                 |
| **Title**             | Failed Test Resolution Commands                        |
| **Priority**          | P1 (High)                                              |
| **Description**       | Templates for fixing failing tests                     |
| **Acceptance Criteria** |                                                      |

1. `/resolve_failed_test`: Fix unit/integration test
   - Input: TestResult JSON with name, error, execution_command
   - Reproduce failure, identify root cause, apply fix
2. `/resolve_failed_e2e_test`: Fix E2E test
   - Similar process with UI-specific considerations

**Source Files:** `commands/resolve_failed_test.md`, `commands/resolve_failed_e2e_test.md`

---

### CT-007: Documentation Template

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | CT-007                                                 |
| **Title**             | Feature Documentation Generation                       |
| **Priority**          | P2 (Medium)                                            |
| **Description**       | Template for generating feature documentation          |
| **Acceptance Criteria** |                                                      |

1. `/document`: Generate docs from implementation
2. Analyze git diff for changes
3. Copy review screenshots to `app_docs/assets/`
4. Generate markdown doc at `app_docs/feature-<adw_id>-<name>.md`
5. Update conditional docs index

**Source Files:** `commands/document.md`

---

### CT-008: Worktree Setup Template

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | CT-008                                                 |
| **Title**             | Isolated Environment Setup                             |
| **Priority**          | P1 (High)                                              |
| **Description**       | Template for configuring worktree environment          |
| **Acceptance Criteria** |                                                      |

1. `/install_worktree`: Setup isolated environment
2. Inputs: `worktree_path`, `backend_port`, `frontend_port`
3. Copy `.env.sample` files
4. Update ports in configuration
5. Install dependencies via `uv sync` / `npm install`
6. Reset database if script exists

**Source Files:** `commands/install_worktree.md`

---

## 9. Testing Requirements (TS)

### TS-001: Unit Test Framework

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | TS-001                                                 |
| **Title**             | Pytest-based Unit Testing                              |
| **Priority**          | P0 (Critical)                                          |
| **Description**       | Unit tests for all core modules                        |
| **Acceptance Criteria** |                                                      |

1. Test directory: `tests/unit/`
2. Fixtures in `tests/conftest.py`:
   - `tmp_project_dir`: Full ADW project structure
   - `mock_adw_config`: Mocked configuration
   - `mock_subprocess`: Git/gh command mocking
   - `mock_claude_execution`: Agent response mocking
   - `sample_github_issue`: Test issue data
3. Test coverage targets:
   - `test_config.py`: ADWConfig loading
   - `test_state.py`: ADWState persistence
   - `test_agent.py`: Template execution
   - `test_github.py`: GitHub operations
   - `test_git_ops.py`: Git operations
   - `test_worktree_ops.py`: Worktree management
   - `test_workflow_ops.py`: Workflow operations
   - `test_cli.py`: CLI interface
   - `test_data_types.py`: Pydantic models

**Source Files:** `tests/unit/*.py`, `tests/conftest.py`
**Markers:** `@pytest.mark.unit`

---

### TS-002: Integration Tests

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | TS-002                                                 |
| **Title**             | Integration Testing Suite                              |
| **Priority**          | P1 (High)                                              |
| **Description**       | Tests for multi-component interactions                 |
| **Acceptance Criteria** |                                                      |

1. Test directory: `tests/integration/`
2. Test files:
   - `test_workflow_sdlc.py`: SDLC pipeline flow
   - `test_workflow_plan.py`: Planning workflow
   - `test_state_persistence.py`: State load/save across phases
3. May require real filesystem operations
4. May use mocked external services

**Source Files:** `tests/integration/*.py`
**Markers:** `@pytest.mark.integration`

---

### TS-003: Test Result Data Types

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | TS-003                                                 |
| **Title**             | Structured Test Result Models                          |
| **Priority**          | P1 (High)                                              |
| **Description**       | Pydantic models for test result parsing                |
| **Acceptance Criteria** |                                                      |

1. `TestResult` model:
   - `test_name`: Test identifier
   - `test_purpose`: What test validates
   - `passed`: Boolean result
   - `error_message`: Failure details
   - `execution_command`: Command to reproduce
2. `E2ETestResult` model:
   - Above fields plus:
   - `test_steps`: List of steps
   - `screenshots`: Captured image paths

**Source Files:** `adw/core/data_types.py`

---

## 10. Data Type Requirements (DT)

### DT-001: GitHub Issue Model

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | DT-001                                                 |
| **Title**             | GitHub Issue Data Model                                |
| **Priority**          | P0 (Critical)                                          |
| **Description**       | Pydantic model for GitHub issue data                   |
| **Acceptance Criteria** |                                                      |

```python
class GitHubIssue(BaseModel):
    number: int
    title: str
    body: Optional[str]
    state: str
    author: dict
    labels: List[dict]
    url: str
    createdAt: str
    updatedAt: str
```

**Source Files:** `adw/core/data_types.py`

---

### DT-002: Agent Request/Response Models

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | DT-002                                                 |
| **Title**             | Agent Execution Models                                 |
| **Priority**          | P0 (Critical)                                          |
| **Description**       | Models for agent template requests and responses       |
| **Acceptance Criteria** |                                                      |

```python
class AgentTemplateRequest(BaseModel):
    agent_name: str
    slash_command: SlashCommand  # Literal type
    args: List[str]
    adw_id: str
    working_dir: Optional[str]

class AgentPromptResponse(BaseModel):
    success: bool
    output: str
    error: Optional[str]
    session_id: Optional[str]
    duration_ms: Optional[int]
    cost_usd: Optional[float]
```

**Source Files:** `adw/core/data_types.py`

---

### DT-003: Command Literal Types

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | DT-003                                                 |
| **Title**             | Type-Safe Slash Command Literals                       |
| **Priority**          | P1 (High)                                              |
| **Description**       | Literal types for all supported slash commands         |
| **Acceptance Criteria** |                                                      |

```python
SlashCommand = Literal[
    "/feature", "/bug", "/chore", "/patch",
    "/implement", "/review", "/document",
    "/test", "/test_e2e",
    "/resolve_failed_test", "/resolve_failed_e2e_test",
    "/classify_issue", "/classify_and_branch",
    "/generate_branch_name", "/install_worktree",
    "/commit", "/pull_request", "/cleanup_worktrees",
    "/prime", "/prepare_app", "/start", "/health_check"
]

IssueClassSlashCommand = Literal["/feature", "/bug", "/chore", "/patch"]

ModelSet = Literal["base", "heavy"]
```

**Source Files:** `adw/core/data_types.py`

---

## 11. Non-Functional Requirements (NF)

### NF-001: Performance

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | NF-001                                                 |
| **Title**             | Performance Requirements                               |
| **Priority**          | P2 (Medium)                                            |
| **Acceptance Criteria** |                                                      |

1. Combined classify+branch in single LLM call (50% faster)
2. Deterministic port allocation (O(1) vs scanning)
3. Parallel worktree execution (no main repo blocking)
4. State persistence overhead < 100ms

---

### NF-002: Reliability

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | NF-002                                                 |
| **Title**             | Reliability Requirements                               |
| **Priority**          | P1 (High)                                              |
| **Acceptance Criteria** |                                                      |

1. Automatic test retry with resolution (up to 4 attempts)
2. State persistence for workflow resumption
3. Graceful handling of missing worktrees
4. Validate prerequisites before each phase

---

### NF-003: Observability

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | NF-003                                                 |
| **Title**             | Logging and Monitoring                                 |
| **Priority**          | P2 (Medium)                                            |
| **Acceptance Criteria** |                                                      |

1. Structured logging via Python `logging` module
2. Log files at `artifacts/{id}/{agent}/execution.log`
3. Progress updates posted to GitHub issue comments
4. Agent cost tracking via JSONL parsing
5. Rich terminal output with markdown formatting

---

### NF-004: Extensibility

| Attribute             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| **ID**                | NF-004                                                 |
| **Title**             | Extensibility Requirements                             |
| **Priority**          | P2 (Medium)                                            |
| **Acceptance Criteria** |                                                      |

1. Project-specific command templates in `.claude/commands/`
2. Configurable command search paths
3. App-specific configuration via `.adw.yaml` `app` section
4. Example templates in `commands/examples/` for customization

---

## 12. Traceability Matrix

| Requirement ID | Source Files                                              | Test Files                  |
| :------------- | :-------------------------------------------------------- | :-------------------------- |
| WF-001         | `adw/workflows/wt/plan_iso.py`                            | `tests/integration/test_workflow_plan.py` |
| WF-002         | `adw/workflows/wt/build_iso.py`                           | `tests/integration/test_workflow_sdlc.py` |
| WF-003         | `adw/workflows/wt/test_iso.py`                            | `tests/integration/test_workflow_sdlc.py` |
| WF-007         | `adw/workflows/wt/sdlc_iso.py`                            | `tests/integration/test_workflow_sdlc.py` |
| ST-001         | `adw/core/state.py`                                       | `tests/unit/test_state.py`  |
| CF-001         | `adw/core/config.py`                                      | `tests/unit/test_config.py` |
| IN-001         | `adw/integrations/github.py`                              | `tests/unit/test_github.py` |
| IN-002         | `adw/integrations/git_ops.py`                             | `tests/unit/test_git_ops.py`|
| IN-003         | `adw/integrations/worktree_ops.py`                        | `tests/unit/test_worktree_ops.py` |
| IN-005         | `adw/core/agent.py`                                       | `tests/unit/test_agent.py`  |
| TR-001         | `adw/cli.py`                                              | `tests/unit/test_cli.py`    |
| DT-001-003     | `adw/core/data_types.py`                                  | `tests/unit/test_data_types.py` |

---

*End of Requirements Specification*
