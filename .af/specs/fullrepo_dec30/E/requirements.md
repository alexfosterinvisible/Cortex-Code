# ADW Framework - System Requirements Specification (Claude)

Version: 1.0.0 | Generated: 2025-12-30 | Approach: Feature-Map Driven

---

## 1. Introduction

### 1.1 Purpose

This document specifies the complete system requirements for the AI Developer Workflow (ADW) Framework - an orchestration system that automates software development using Claude Code agents in isolated git worktrees. ADW processes GitHub issues through a complete SDLC pipeline: plan, build, test, review, document, ship.

### 1.2 Scope

ADW Framework is a **consumable package** - projects add it as a dependency and configure it via `.adw.yaml`. The framework provides:

- CLI interface for workflow execution
- Claude Code agent orchestration
- GitHub integration for issue tracking and PRs
- Git worktree isolation for parallel execution
- State persistence across workflow phases
- Webhook and cron triggers for automation

### 1.3 Definitions

| Term               | Definition                                                           |
|--------------------|----------------------------------------------------------------------|
| ADW ID             | 8-character UUID identifying a workflow instance (e.g., `abc12345`) |
| Isolated Workflow  | Workflow running in dedicated git worktree (`*_iso` suffix)         |
| Model Set          | Configuration selecting model tier: `base` (Sonnet) or `heavy` (Opus)|
| Slash Command      | Template command executed via Claude Code (e.g., `/implement`)      |
| ZTE                | Zero Touch Execution - full SDLC with auto-merge                    |
| Worktree           | Isolated git working directory for parallel development             |

---

## 2. Feature Map - Issue Processing

### 2.1 Issue Fetching from GitHub

**What it does:**
- Retrieves GitHub issue data via `gh` CLI with JSON output
- Parses into typed Pydantic models (`GitHubIssue`, `GitHubIssueListItem`)
- Extracts number, title, body, state, author, assignees, labels, comments, timestamps, URL

**When it's used:**
- Start of any workflow requiring issue context (plan, patch, SDLC)
- Webhook trigger processing to parse incoming issue events

**What it needs:**
- Issue number (string)
- Repository path in `org/repo` format
- Optional: `GITHUB_PAT` environment variable (falls back to `gh auth` if not set)

**What it produces:**
- `GitHubIssue` Pydantic model with all issue fields
- Comments sorted by creation time

**Success criteria:**
- Valid JSON response from `gh issue view` with status 0
- All required fields populated in returned model

**Edge cases:**
- Issue does not exist -> Exit with error from `gh` CLI
- Bot comments filtered via `ADW_BOT_IDENTIFIER = "[ADW-AGENTS]"`
- Rate limiting handled by underlying `gh` CLI

### 2.2 Issue Classification

**What it does:**
- Determines issue type using Claude Code agent with `/classify_issue` command
- Maps to one of: `/feature`, `/bug`, `/chore`
- Uses haiku model for fast classification (base) or sonnet (heavy)

**When it's used:**
- Planning phase to determine appropriate planning template
- Before branch name generation

**What it needs:**
- `GitHubIssue` model (minimal: number, title, body)
- ADW ID for state tracking
- Logger instance

**What it produces:**
- `IssueClassSlashCommand` literal: `/feature`, `/bug`, or `/chore`
- Error message string if classification fails

**Success criteria:**
- Agent returns one of the three valid classification commands
- Response contains recognizable pattern (regex: `/chore|/bug|/feature|0`)

**Edge cases:**
- Agent returns `0` -> No classification possible, error returned
- Invalid classification -> Returns error message
- Agent execution failure -> Returns agent error output

### 2.3 Branch Name Generation

**What it does:**
- Generates standardized git branch name using Claude Code agent
- Format: `{type}-issue-{number}-adw-{adw_id}-{description}`
- Uses `/generate_branch_name` slash command

**When it's used:**
- After issue classification in planning phase
- When creating new branches for issues

**What it needs:**
- Issue type (without leading slash)
- ADW ID
- Minimal issue JSON (number, title, body)

**What it produces:**
- Branch name string following pattern
- Error message if generation fails

**Success criteria:**
- Valid git branch name (no spaces, special chars)
- Contains issue number and ADW ID for traceability

**Edge cases:**
- Very long issue titles -> Agent should truncate description
- Special characters in title -> Agent should sanitize

### 2.4 Combined Classify and Branch (Optimized)

**What it does:**
- Performs classification AND branch name generation in single LLM call
- ~2x faster than sequential calls
- Uses `/classify_and_branch` slash command

**When it's used:**
- Default path in `plan_iso.py` workflow
- When performance matters and both values needed

**What it needs:**
- ADW ID
- Minimal issue JSON

**What it produces:**
- JSON with `issue_class` and `branch_name` fields
- Error message if parsing fails

**Success criteria:**
- Valid JSON response with both fields populated
- `issue_class` is valid IssueClassSlashCommand
- `branch_name` is valid git branch name

### 2.5 Plan File Creation

**What it does:**
- Creates implementation plan using classified slash command
- Calls `/feature`, `/bug`, or `/chore` template
- Saves plan to `specs/issue-{number}-adw-{id}-{desc}.md`

**When it's used:**
- Planning phase after classification
- Executed in worktree if isolated workflow

**What it needs:**
- GitHub issue data
- Classified command
- ADW ID
- Working directory (worktree path for isolated)

**What it produces:**
- Markdown plan file in `specs/` directory
- Agent response with execution status

**Success criteria:**
- Plan file created with valid markdown
- Contains implementation steps, acceptance criteria
- File path stored in state

---

## 3. Feature Map - Execution Environment

### 3.1 Git Worktree Isolation

**What it does:**
- Creates isolated git worktree for workflow execution
- Path: `artifacts/{project_id}/trees/{adw_id}/`
- Enables parallel workflow execution without interference

**When it's used:**
- All `*_iso` workflows (plan_iso, build_iso, etc.)
- When `create_worktree()` is called in workflow

**What it needs:**
- Branch name (must exist or be created)
- ADW ID for unique directory naming
- ADWConfig for paths

**What it produces:**
- Isolated directory with full repo copy
- Worktree path stored in state

**Success criteria:**
- `git worktree add` succeeds
- Directory contains all tracked files
- Branch checked out correctly

**Edge cases:**
- Worktree already exists -> Remove and recreate
- Branch doesn't exist -> Create from base branch first
- Disk space issues -> Git error propagated

### 3.2 Port Allocation

**What it does:**
- Allocates deterministic ports from ADW ID hash
- Backend ports: 9100-9114 (configurable start)
- Frontend ports: 9200-9214 (configurable start)
- 15 port range for each tier

**When it's used:**
- During worktree creation for projects needing dev servers
- Stored in state for consistent port usage

**What it needs:**
- ADW ID (8-character string)
- Port configuration from ADWConfig

**What it produces:**
- `backend_port` integer
- `frontend_port` integer
- Ports stored in ADWState

**Success criteria:**
- Same ADW ID always produces same ports (deterministic)
- Ports within configured range

**Edge cases:**
- Port already in use -> Not checked, application must handle
- All ports exhausted -> Wraps within range via modulo

**Implementation:**
```python
hash_int = int(hashlib.md5(adw_id.encode()).hexdigest()[:8], 16)
backend_port = config.ports.backend_start + (hash_int % config.ports.backend_count)
frontend_port = config.ports.frontend_start + (hash_int % config.ports.frontend_count)
```

### 3.3 Model Selection

**What it does:**
- Selects Claude model based on slash command and model set
- Model set from state: `base` or `heavy`
- Maps commands to appropriate model tier

**When it's used:**
- Every `execute_template()` call
- Reads `model_set` from ADWState

**What it needs:**
- `AgentTemplateRequest` with slash_command and adw_id
- `SLASH_COMMAND_MODEL_MAP` configuration

**What it produces:**
- Model name: `haiku`, `sonnet`, or `opus`

**Model Mapping:**

| Slash Command           | Base Model | Heavy Model |
|-------------------------|------------|-------------|
| /classify_issue         | haiku      | sonnet      |
| /classify_adw           | haiku      | sonnet      |
| /generate_branch_name   | haiku      | sonnet      |
| /implement              | sonnet     | opus        |
| /test                   | sonnet     | sonnet      |
| /resolve_failed_test    | sonnet     | opus        |
| /review                 | sonnet     | sonnet      |
| /document               | sonnet     | opus        |
| /commit                 | sonnet     | sonnet      |
| /pull_request           | sonnet     | sonnet      |
| /feature                | sonnet     | opus        |
| /bug                    | sonnet     | opus        |
| /chore                  | sonnet     | opus        |
| /patch                  | sonnet     | opus        |

### 3.4 Prompt Templating

**What it does:**
- Loads slash command markdown templates from configured directories
- Substitutes `$ARGUMENTS` placeholder with runtime args
- Supports multiple command directories with priority

**When it's used:**
- Every agent execution via `execute_template()`

**What it needs:**
- Slash command name (e.g., `/implement`)
- Arguments list
- Command paths from ADWConfig

**What it produces:**
- Complete prompt string for Claude Code execution

**Command Directory Resolution:**
1. First checks `${ADW_FRAMEWORK}/commands/`
2. Then checks project's `.claude/commands/`
3. Can be customized via `.adw.yaml` `commands` list

**Success criteria:**
- Template file found and loaded
- Arguments properly interpolated

---

## 4. Feature Map - SDLC Automation

### 4.1 Planning Workflow (`plan_iso`)

**What it does:**
- Fetches GitHub issue
- Creates worktree and branch
- Classifies issue type
- Generates implementation plan
- Commits plan to branch
- Creates PR for review

**Phases:**
1. Fetch issue from GitHub
2. Ensure ADW ID exists (create or load)
3. Classify issue + generate branch name (combined call)
4. Create worktree on new branch
5. Execute planning template (/feature, /bug, /chore)
6. Commit plan file
7. Push branch to origin
8. Create PR linking to issue

**What it needs:**
- Issue number (required)
- ADW ID (optional, generates if not provided)

**What it produces:**
- Branch with plan file
- Pull request URL
- State file with all metadata

**Success criteria:**
- Plan file exists in `specs/` directory
- Branch pushed to remote
- PR created and linked to issue

### 4.2 Build/Implementation Workflow (`build_iso`)

**What it does:**
- Executes `/implement` command with plan file
- Implements all changes specified in plan
- Commits implementation

**When it's used:**
- After planning phase in SDLC
- Standalone with existing ADW ID and plan

**What it needs:**
- Issue number
- ADW ID (required - must have existing state)
- Plan file path from state

**What it produces:**
- Implemented code changes
- Commit with implementation

**Success criteria:**
- `/implement` agent succeeds
- Changes committed to branch

### 4.3 Testing Workflow (`test_iso`)

**What it does:**
- Runs `/test` command for unit tests
- Optionally runs `/test_e2e` for E2E tests
- Auto-fixes failures with `/resolve_failed_test` (up to 3 retries)
- Parses JSON test results

**When it's used:**
- After build phase in SDLC
- Standalone for test-only runs

**What it needs:**
- Issue number
- ADW ID
- Working implementation in worktree
- Optional: `--skip-e2e` flag

**What it produces:**
- Test results (pass/fail with details)
- Fixed code if failures resolved
- State update with test status

**Retry Logic:**
- Maximum 3 retry attempts per test type
- Calls `/resolve_failed_test` or `/resolve_failed_e2e_test`
- Delays between retries: [1, 3, 5] seconds

**Success criteria:**
- All tests pass OR max retries exhausted
- Test results parseable as JSON

### 4.4 Review Workflow (`review_iso`)

**What it does:**
- Validates implementation against spec
- Captures screenshots for UI verification
- Identifies issues with severity ratings
- Optionally auto-resolves issues via patches

**When it's used:**
- After testing phase in SDLC
- Standalone for review-only runs

**What it needs:**
- Issue number
- ADW ID
- Spec file (from state or discovered)
- Optional: `--skip-resolution` flag

**What it produces:**
- `ReviewResult` with:
  - `success`: boolean
  - `review_summary`: 2-4 sentence summary
  - `review_issues`: List of `ReviewIssue`
  - `screenshots`: Local file paths
  - `screenshot_urls`: Public URLs after upload

**Issue Severity Levels:**
- `skippable`: Minor issues, won't block
- `tech_debt`: Should be addressed later
- `blocker`: Must be fixed before merge

**Success criteria:**
- Review completes without agent errors
- Issues properly categorized by severity
- Blockers resolved if resolution enabled

### 4.5 Documentation Workflow (`document_iso`)

**What it does:**
- Generates feature documentation from implementation
- Uses `/document` command
- Commits docs to branch

**When it's used:**
- After review phase in SDLC
- Standalone for documentation updates

**What it needs:**
- Issue number
- ADW ID
- Existing implementation in worktree

**What it produces:**
- Documentation markdown file(s)
- Commit with documentation changes

**Success criteria:**
- Documentation file created
- Changes committed to branch

### 4.6 Ship Workflow (`ship_iso`)

**What it does:**
- Approves pull request
- Merges PR to main branch
- Closes associated issue

**When it's used:**
- Final phase of SDLC
- After all validation passes
- ZTE mode for auto-merge

**What it needs:**
- Issue number
- ADW ID
- Valid PR on branch

**What it produces:**
- Merged PR
- Closed issue
- Status comments on issue

**Success criteria:**
- PR approved via `gh pr review --approve`
- PR merged via `gh pr merge`
- Issue closed via `gh issue close`

### 4.7 Full SDLC Orchestration (`sdlc_iso`)

**What it does:**
- Chains all phases: plan -> build -> test -> review -> document
- Manages state transitions between phases
- Handles failures and cleanup

**Execution Order:**
1. `plan_iso.run()` - Create plan and branch
2. `build_iso.run()` - Implement changes
3. `test_iso.run()` - Run tests with retries
4. `review_iso.run()` - Validate implementation
5. `document_iso.run()` - Generate docs

**What it needs:**
- Issue number
- Optional: ADW ID, --skip-e2e, --skip-resolution

**What it produces:**
- Complete implementation with tests, docs
- PR ready for review/merge

### 4.8 Zero Touch Execution (`sdlc_zte_iso`)

**What it does:**
- Full SDLC plus automatic ship
- True end-to-end automation
- No human intervention required

**When it's used:**
- Triggered via webhook with `adw_sdlc_zte_iso` command
- CLI with `adw zte <issue>`

**Execution:**
1. Full SDLC workflow
2. Automatic `ship_iso.run()`

---

## 5. Feature Map - Persistence

### 5.1 State Management (ADWState)

**What it does:**
- Persists workflow state across phases
- JSON file storage per ADW instance
- Path: `artifacts/{project_id}/{adw_id}/adw_state.json`

**State Fields:**

| Field          | Type                    | Description                          |
|----------------|-------------------------|--------------------------------------|
| adw_id         | str                     | 8-character workflow identifier      |
| issue_number   | Optional[str]           | GitHub issue number                  |
| branch_name    | Optional[str]           | Git branch name                      |
| plan_file      | Optional[str]           | Path to plan markdown file           |
| issue_class    | Optional[str]           | Classification: /feature, /bug, /chore |
| worktree_path  | Optional[str]           | Absolute path to worktree            |
| backend_port   | Optional[int]           | Allocated backend port               |
| frontend_port  | Optional[int]           | Allocated frontend port              |
| model_set      | Optional[str]           | Model tier: base or heavy            |
| all_adws       | List[str]               | All ADW IDs in workflow chain        |

**Operations:**
- `ADWState(adw_id)` - Create new state
- `ADWState.load(adw_id)` - Load existing state
- `state.update(**kwargs)` - Update fields
- `state.save(workflow_step)` - Persist to file
- `state.get(key)` - Retrieve value

**Validation:**
- Uses `ADWStateData` Pydantic model for serialization
- Core fields filtered on update

### 5.2 Artifact Organization

**What it does:**
- Organizes all workflow outputs in structured directories
- Separates agent outputs, prompts, logs by phase

**Directory Structure:**
```
artifacts/{org}/{repo}/
    {adw-id}/
        adw_state.json                    # Workflow state
        sdlc_planner/
            raw_output.jsonl              # Agent JSONL output
            raw_output.json               # Converted JSON array
            prompts/
                feature.txt               # Saved prompt
            plan.md                       # Plan artifact
        sdlc_implementor/
            raw_output.jsonl
        tester/
            raw_output.jsonl
        reviewer/
            raw_output.jsonl
            review_img/                   # Screenshots
    trees/
        {adw-id}/                         # Git worktree
```

### 5.3 Prompt/Output Logging

**What it does:**
- Saves every prompt sent to Claude Code
- Captures JSONL stream output
- Converts to JSON array for easier parsing

**Output Format:**
- JSONL: One JSON object per line (Claude Code stream-json)
- Contains: messages, tool calls, results
- Result message has: type, is_error, duration_ms, session_id, total_cost_usd

### 5.4 Configuration Management

**What it does:**
- Loads project config from `.adw.yaml`
- Provides path resolution and defaults
- Supports variable expansion (`${ADW_FRAMEWORK}`)

**ADWConfig Fields:**

| Field         | Type       | Default            | Description                     |
|---------------|------------|--------------------|---------------------------------|
| project_root  | Path       | (auto-detected)    | Root of consuming project       |
| project_id    | str        | "unknown-project"  | Unique identifier (org/repo)    |
| artifacts_dir | Path       | "./artifacts"      | Base artifacts directory        |
| source_root   | Path       | "./src"            | Source code root                |
| ports         | PortConfig | (see below)        | Port allocation config          |
| commands      | List[Path] | (framework + .claude) | Command template directories |
| app_config    | Dict       | {}                 | Project-specific settings       |

**PortConfig:**

| Field          | Type | Default | Description                |
|----------------|------|---------|----------------------------|
| backend_start  | int  | 9100    | First backend port         |
| backend_count  | int  | 15      | Number of backend ports    |
| frontend_start | int  | 9200    | First frontend port        |
| frontend_count | int  | 15      | Number of frontend ports   |

---

## 6. Feature Map - Triggers

### 6.1 CLI Triggers

**What it does:**
- Entry point via `adw` command
- Routes to workflow modules
- Parses arguments and flags

**Commands:**

| Command    | Module                     | Description                    |
|------------|----------------------------|--------------------------------|
| plan       | wt.plan_iso                | Planning phase only            |
| build      | wt.build_iso               | Build from existing plan       |
| test       | wt.test_iso                | Run tests with retry           |
| review     | wt.review_iso              | Validate implementation        |
| document   | wt.document_iso            | Generate documentation         |
| ship       | wt.ship_iso                | Approve and merge PR           |
| patch      | wt.patch_iso               | Quick fix workflow             |
| sdlc       | wt.sdlc_iso                | Full SDLC pipeline             |
| zte        | wt.sdlc_zte_iso            | SDLC + auto-merge              |
| monitor    | triggers.trigger_cron      | Cron-based monitoring          |
| webhook    | triggers.trigger_webhook   | Webhook server                 |

### 6.2 Webhook Triggers

**What it does:**
- FastAPI server listening for GitHub webhooks
- Processes issue comments with ADW commands
- Triggers workflows asynchronously

**Endpoint:** `POST /webhook`

**Payload Processing:**
1. Validate webhook signature (if configured)
2. Parse issue comment event
3. Extract ADW command from comment
4. Filter bot comments (ADW_BOT_IDENTIFIER)
5. Launch workflow in background

**Trigger Commands:**
- `adw_plan_iso` - Plan only
- `adw_sdlc_iso` - Full SDLC
- `adw_sdlc_zte_iso` - SDLC + auto-merge
- `model_set heavy` - Use Opus for complex tasks

**What it needs:**
- `WEBHOOK_SECRET` for signature validation
- GitHub webhook configured on repo
- Port binding for server (default: 8000)

### 6.3 Cron Triggers

**What it does:**
- Polls repository for new/updated issues
- Auto-triggers workflows based on labels/keywords
- Scheduled execution at intervals

**When it's used:**
- Monitoring repos without webhooks
- Batch processing of issues

**Configuration:**
- Poll interval (default: 5 minutes)
- Label filters for auto-trigger
- Repository path

---

## 7. Feature Map - Integrations

### 7.1 GitHub API Integration

**What it does:**
- All GitHub operations via `gh` CLI
- Issue fetching, commenting, labeling
- PR creation, approval, merging
- Issue closing

**Functions:**

| Function               | Description                              |
|------------------------|------------------------------------------|
| fetch_issue            | Get issue details as GitHubIssue         |
| fetch_open_issues      | List all open issues                     |
| fetch_issue_comments   | Get comments for issue                   |
| make_issue_comment     | Post comment with ADW identifier         |
| mark_issue_in_progress | Add label and assign                     |
| approve_pr             | Approve PR with comment                  |
| close_issue            | Close issue with comment                 |
| find_keyword_from_comment | Search comments for trigger           |

**Bot Identification:**
- All comments prefixed with `[ADW-AGENTS]`
- Prevents webhook loops
- Enables filtering of ADW comments

**Environment:**
- `GITHUB_PAT` - Personal access token (optional)
- Falls back to `gh auth` if not set

### 7.2 Git Operations

**What it does:**
- Branch management (create, checkout, delete)
- Commit operations
- Push to remote
- Current branch detection

**Functions:**

| Function           | Description                          |
|--------------------|--------------------------------------|
| get_current_branch | Return current branch name           |
| create_branch      | Create and checkout new branch       |
| checkout_branch    | Switch to existing branch            |
| delete_branch      | Remove local branch                  |
| push_branch        | Push to origin                       |

### 7.3 Claude Code Agent Integration

**What it does:**
- Executes Claude Code CLI with prompts
- Handles JSONL output streaming
- Parses results and errors
- Retry logic for transient failures

**Functions:**

| Function                    | Description                           |
|-----------------------------|---------------------------------------|
| execute_template            | Run slash command with args           |
| prompt_claude_code          | Execute raw prompt                    |
| prompt_claude_code_with_retry | Execute with retry logic            |
| parse_jsonl_output          | Parse JSONL to messages + result      |
| convert_jsonl_to_json       | Convert JSONL file to JSON array      |

**Execution:**
```bash
claude -p "<prompt>" --model <model> --output-format stream-json --verbose [--dangerously-skip-permissions]
```

**Environment:**
- `ANTHROPIC_API_KEY` - Required for API access
- `CLAUDE_CODE_PATH` - Path to CLI (default: `claude`)
- `CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR` - Preserve CWD

**Retry Logic:**
- RetryCode enum: CLAUDE_CODE_ERROR, TIMEOUT_ERROR, EXECUTION_ERROR, ERROR_DURING_EXECUTION, NONE
- Delays: [1, 3, 5] seconds between retries
- Max 3 retries per execution

### 7.4 File System Operations

**What it does:**
- Directory creation for artifacts
- File reading/writing for plans, specs
- Glob pattern matching for file discovery

**Used For:**
- Creating artifact directories
- Saving prompts and outputs
- Finding existing plans by pattern

---

## 8. Non-Functional Requirements

### 8.1 Performance

- Classification should complete in <30 seconds
- Full SDLC pipeline should complete in <30 minutes for typical issue
- Port allocation is deterministic (O(1) hash lookup)

### 8.2 Reliability

- Retry logic for transient Claude Code failures
- State persistence survives process restarts
- Worktree isolation prevents workflow interference

### 8.3 Security

- API keys stored in `.env`, never committed
- GitHub PAT optional (uses `gh auth` fallback)
- Subprocess environment filtered to safe variables
- Bot identifier prevents infinite webhook loops

### 8.4 Maintainability

- Typed with Pydantic models throughout
- Modular workflow design (composable phases)
- Comprehensive logging to file and console

---

## 9. Dependencies

### 9.1 Python Dependencies

| Package       | Version   | Purpose                        |
|---------------|-----------|--------------------------------|
| python-dotenv | >=1.0.0   | Environment variable loading   |
| pydantic      | >=2.0.0   | Data validation and models     |
| pyyaml        | >=6.0.0   | YAML config parsing            |
| GitPython     | >=3.0.0   | Git operations (optional)      |
| schedule      | >=1.2.0   | Cron scheduling                |
| fastapi       | >=0.100.0 | Webhook server                 |
| uvicorn       | >=0.23.0  | ASGI server                    |
| aiosqlite     | >=0.19.0  | Async SQLite (future use)      |
| boto3         | >=1.26.0  | R2/S3 upload for screenshots   |
| rich          | >=13.0.0  | Terminal formatting            |

### 9.2 External Tools

| Tool   | Purpose                              |
|--------|--------------------------------------|
| git    | Version control operations           |
| gh     | GitHub CLI for API operations        |
| claude | Claude Code CLI for agent execution  |

---

## 10. Environment Variables

| Variable                              | Required | Default | Description                   |
|---------------------------------------|----------|---------|-------------------------------|
| ANTHROPIC_API_KEY                     | Yes      | -       | Claude API authentication     |
| GITHUB_PAT                            | No       | -       | GitHub token (uses gh auth)   |
| CLAUDE_CODE_PATH                      | No       | claude  | Path to Claude CLI            |
| CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR | No   | true    | Preserve working directory    |
| E2B_API_KEY                           | No       | -       | Cloud sandbox (future)        |
| CLOUDFLARED_TUNNEL_TOKEN              | No       | -       | Cloudflare tunnel (future)    |
| ADW_DISABLE_GITHUB_COMMENTS           | No       | false   | Skip GitHub comments          |

---

## Appendix A: File Manifest

```
adw/
    __init__.py
    cli.py                              # Entry point
    core/
        __init__.py
        config.py                       # ADWConfig, PortConfig
        state.py                        # ADWState
        data_types.py                   # All Pydantic models
        agent.py                        # Claude Code execution
        utils.py                        # Logging, parsing, env
        health.py                       # Health checks
    integrations/
        __init__.py
        github.py                       # GitHub API via gh
        git_ops.py                      # Git operations
        workflow_ops.py                 # Shared ADW operations
        worktree_ops.py                 # Worktree management
        r2_uploader.py                  # Screenshot upload
    workflows/
        __init__.py
        wt/                             # Isolated workflows
            __init__.py
            plan_iso.py
            build_iso.py
            test_iso.py
            review_iso.py
            document_iso.py
            ship_iso.py
            sdlc_iso.py
            sdlc_zte_iso.py
            patch_iso.py
            plan_build_iso.py
            plan_build_test_iso.py
            plan_build_review_iso.py
            plan_build_test_review_iso.py
            plan_build_document_iso.py
        reg/                            # Regular workflows (deprecated)
            ...
    triggers/
        __init__.py
        trigger_webhook.py              # FastAPI webhook server
        trigger_cron.py                 # Polling trigger
commands/
    _command_index.yaml                 # Command metadata
    feature.md
    bug.md
    chore.md
    implement.md
    review.md
    document.md
    commit.md
    pull_request.md
    patch.md
    classify_issue.md
    classify_and_branch.md
    generate_branch_name.md
    classify_adw.md
    install_worktree.md
    resolve_failed_test.md
    resolve_failed_e2e_test.md
    test_e2e.md
    review_code.md
    review_bg_iso.md
    cleanup_worktrees.md
```
