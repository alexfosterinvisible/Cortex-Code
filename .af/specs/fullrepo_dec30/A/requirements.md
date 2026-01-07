# CxC Framework - Requirements Specification (Claude)

## Document Information

| Field           | Value                          |
|-----------------|--------------------------------|
| Version         | 1.0                            |
| Date            | 2025-12-30                     |
| Status          | Complete                       |
| Author          | Claude Code Agent              |

---

## 1. Functional Requirements

### 1.1 CLI Interface (FR-CLI)

| ID        | Requirement                                              | Priority | Success Criteria                                                      |
|-----------|----------------------------------------------------------|----------|-----------------------------------------------------------------------|
| FR-CLI-01 | Provide unified command-line interface entry point      | P0       | `uv run cxc --help` displays all available commands                   |
| FR-CLI-02 | Support `plan` command for isolated planning workflow   | P0       | `cxc plan <issue>` creates worktree and generates plan file           |
| FR-CLI-03 | Support `build` command for implementation phase        | P0       | `cxc build <issue> <cxc-id>` executes plan in worktree                |
| FR-CLI-04 | Support `test` command for testing phase                | P0       | `cxc test <issue> <cxc-id>` runs tests with auto-resolution           |
| FR-CLI-05 | Support `review` command for review phase               | P0       | `cxc review <issue> <cxc-id>` validates implementation against spec   |
| FR-CLI-06 | Support `document` command for documentation phase      | P1       | `cxc document <issue> <cxc-id>` generates feature documentation       |
| FR-CLI-07 | Support `ship` command for shipping phase               | P0       | `cxc ship <issue> <cxc-id>` merges to main and closes issue           |
| FR-CLI-08 | Support `patch` command for quick fixes                 | P1       | `cxc patch <issue>` creates targeted fix in worktree                  |
| FR-CLI-09 | Support `sdlc` command for full lifecycle               | P0       | `cxc sdlc <issue>` chains plan-build-test-review-document             |
| FR-CLI-10 | Support `zte` command for zero-touch execution          | P1       | `cxc zte <issue>` runs SDLC with auto-merge on success                |
| FR-CLI-11 | Support `monitor` command for cron polling              | P1       | `cxc monitor` polls GitHub every 20s for new issues                   |
| FR-CLI-12 | Support `webhook` command for real-time triggers        | P1       | `cxc webhook` starts FastAPI server on configured port                |
| FR-CLI-13 | Support `--skip-e2e` flag for test command              | P2       | Tests run without E2E phase when flag present                         |
| FR-CLI-14 | Support `--skip-resolution` flag for review command     | P2       | Review skips auto-resolution of blockers when flag present            |
| FR-CLI-15 | Parse optional CxC ID as second positional argument     | P1       | Existing workflow can be resumed with explicit CxC ID                 |

### 1.2 Configuration Management (FR-CFG)

| ID        | Requirement                                              | Priority | Success Criteria                                                      |
|-----------|----------------------------------------------------------|----------|-----------------------------------------------------------------------|
| FR-CFG-01 | Load configuration from `.cxc.yaml` in project root     | P0       | CxCConfig.load() finds and parses YAML file                           |
| FR-CFG-02 | Support `project_id` field for GitHub org/repo          | P0       | State paths include project_id for isolation                          |
| FR-CFG-03 | Support `artifacts_dir` for state/worktree storage      | P0       | All artifacts stored under configured directory                       |
| FR-CFG-04 | Support `source_root` for source code location          | P1       | Build agents use correct base path                                    |
| FR-CFG-05 | Support `ports` section for backend/frontend ports      | P0       | Worktrees get deterministic port assignments                          |
| FR-CFG-06 | Support 15 concurrent port allocations per type         | P1       | Ports range 9100-9114 (backend) and 9200-9214 (frontend)              |
| FR-CFG-07 | Support `commands` list for slash command paths         | P1       | Multiple command directories merged in priority order                 |
| FR-CFG-08 | Support `app` section for project-specific settings     | P1       | Backend/frontend dirs, start/stop scripts accessible                  |
| FR-CFG-09 | Support `${CxC_FRAMEWORK}` variable expansion           | P1       | Framework path substituted in command paths                           |
| FR-CFG-10 | Load environment from `.env` via python-dotenv          | P0       | Secrets available via os.getenv                                       |
| FR-CFG-11 | Require `ANTHROPIC_API_KEY` environment variable        | P0       | Claude Code execution fails gracefully without key                    |
| FR-CFG-12 | Support optional `GITHUB_PAT` for API authentication    | P1       | Falls back to `gh auth` if not provided                               |
| FR-CFG-13 | Support optional `CLAUDE_CODE_PATH` for CLI location    | P2       | Defaults to `claude` if not specified                                 |
| FR-CFG-14 | Support `CxC_DISABLE_GITHUB_COMMENTS` to suppress posts | P2       | No GitHub comments when env var set                                   |

### 1.3 State Management (FR-STA)

| ID        | Requirement                                              | Priority | Success Criteria                                                      |
|-----------|----------------------------------------------------------|----------|-----------------------------------------------------------------------|
| FR-STA-01 | Generate unique 8-character CxC ID for each workflow    | P0       | IDs are unique, alphanumeric, lowercase                               |
| FR-STA-02 | Persist state to `cxc_state.json` in agents directory   | P0       | State survives process restarts                                       |
| FR-STA-03 | Track `cxc_id` field                                     | P0       | Required for all state operations                                     |
| FR-STA-04 | Track `issue_number` for GitHub issue reference         | P0       | Links workflow to source issue                                        |
| FR-STA-05 | Track `branch_name` for feature branch                  | P0       | Git operations use correct branch                                     |
| FR-STA-06 | Track `plan_file` path for spec file                    | P0       | Implement and review phases reference plan                            |
| FR-STA-07 | Track `issue_class` for issue classification            | P0       | Commit messages use correct type prefix                               |
| FR-STA-08 | Track `worktree_path` for isolated environment          | P0       | All workflow phases operate in worktree                               |
| FR-STA-09 | Track `backend_port` and `frontend_port`                | P0       | Servers start on allocated ports                                      |
| FR-STA-10 | Track `model_set` for LLM model selection               | P1       | Heavy/base model selection persists                                   |
| FR-STA-11 | Track `all_cxcs` list of workflow phases run            | P2       | Audit trail of phase execution                                        |
| FR-STA-12 | Support `CxCState.load(cxc_id)` for state retrieval     | P0       | Returns None if state file missing                                    |
| FR-STA-13 | Support `state.save(workflow_step)` with logging        | P0       | Logs which phase saved state                                          |
| FR-STA-14 | Support `state.update(**kwargs)` for field updates      | P0       | Only core fields persisted, others ignored                            |
| FR-STA-15 | Support stdin/stdout piping for state transfer          | P2       | Enables workflow chaining via pipes                                   |
| FR-STA-16 | Validate state via Pydantic CxCStateData model          | P1       | Invalid data raises validation errors                                 |

### 1.4 Worktree Management (FR-WRK)

| ID        | Requirement                                              | Priority | Success Criteria                                                      |
|-----------|----------------------------------------------------------|----------|-----------------------------------------------------------------------|
| FR-WRK-01 | Create git worktree for each workflow instance          | P0       | `git worktree add` succeeds with unique path                          |
| FR-WRK-02 | Allocate deterministic ports from CxC ID hash           | P0       | Same CxC ID always gets same ports                                    |
| FR-WRK-03 | Write `.ports.env` file in worktree root                | P0       | Contains BACKEND_PORT and FRONTEND_PORT                               |
| FR-WRK-04 | Create worktree under `artifacts/{project_id}/trees/`   | P0       | Isolation per project                                                 |
| FR-WRK-05 | Validate worktree exists before dependent phases        | P0       | Build/test/review require existing worktree                           |
| FR-WRK-06 | Support worktree cleanup via cleanup command            | P2       | `git worktree remove` and directory deletion                          |
| FR-WRK-07 | Install worktree dependencies after creation            | P1       | Run install script in worktree context                                |

### 1.5 Agent Execution (FR-AGT)

| ID        | Requirement                                              | Priority | Success Criteria                                                      |
|-----------|----------------------------------------------------------|----------|-----------------------------------------------------------------------|
| FR-AGT-01 | Execute Claude Code CLI with slash commands             | P0       | `claude -p "<prompt>" --output-format stream-json`                    |
| FR-AGT-02 | Load command templates from markdown files              | P0       | `$ARGUMENTS` placeholder replaced with args                           |
| FR-AGT-03 | Support variable substitution ($1, $2, $3, etc.)        | P0       | Positional args substituted in templates                              |
| FR-AGT-04 | Parse JSONL output stream for result extraction         | P0       | Find `type: result` message and extract output                        |
| FR-AGT-05 | Handle agent execution errors gracefully                | P1       | Return AgentPromptResponse with success=False                         |
| FR-AGT-06 | Log prompts and responses to artifacts directory        | P1       | Full audit trail for debugging                                        |
| FR-AGT-07 | Support `model_set` selection (base vs heavy)           | P1       | Sonnet for base, Opus for heavy tasks                                 |
| FR-AGT-08 | Use heavy model for `/implement`, `/document` commands  | P1       | Complex tasks use Opus                                                |
| FR-AGT-09 | Pass working directory to agent for worktree context    | P0       | Agent operates in correct directory                                   |
| FR-AGT-10 | Set timeout for agent execution                         | P1       | Long-running agents terminate after limit                             |

### 1.6 GitHub Integration (FR-GH)

| ID        | Requirement                                              | Priority | Success Criteria                                                      |
|-----------|----------------------------------------------------------|----------|-----------------------------------------------------------------------|
| FR-GH-01  | Fetch issue details via `gh issue view` command         | P0       | Returns GitHubIssue model with title, body, labels                    |
| FR-GH-02  | Post comments to issues via `gh issue comment`          | P0       | Progress updates visible on GitHub issue                              |
| FR-GH-03  | Support CxC_DISABLE_GITHUB_COMMENTS environment flag    | P2       | No comments posted when disabled                                      |
| FR-GH-04  | Classify issues as feature/bug/chore/patch              | P0       | `/classify_issue` returns correct type                                |
| FR-GH-05  | Generate branch names from issue metadata               | P0       | Format: `<type>-issue-<num>-cxc-<id>-<slug>`                          |
| FR-GH-06  | Combined classification + branch generation             | P1       | Single LLM call returns both values                                   |
| FR-GH-07  | Create pull requests via `gh pr create`                 | P0       | PR links to issue and includes summary                                |
| FR-GH-08  | Approve pull requests via `gh pr review`                | P1       | Auto-approve for ZTE workflow                                         |
| FR-GH-09  | Merge pull requests via `gh pr merge`                   | P1       | No-ff merge preserves commit history                                  |
| FR-GH-10  | Close issues after successful ship                      | P1       | Issue marked closed on merge                                          |
| FR-GH-11  | Fetch open issues for cron trigger                      | P1       | List issues without CxC comments                                      |
| FR-GH-12  | Parse issue comments for CxC commands                   | P1       | Detect `cxc_sdlc_iso`, `model_set heavy`, etc.                        |
| FR-GH-13  | Extract repository path from git remote URL             | P0       | `org/repo` format for API calls                                       |

### 1.7 Git Operations (FR-GIT)

| ID        | Requirement                                              | Priority | Success Criteria                                                      |
|-----------|----------------------------------------------------------|----------|-----------------------------------------------------------------------|
| FR-GIT-01 | Create feature branches from main                       | P0       | Branch exists with correct naming convention                          |
| FR-GIT-02 | Commit changes with structured messages                 | P0       | Format: `<agent>: <type>: <description>`                              |
| FR-GIT-03 | Push branches to origin                                 | P0       | Remote tracking branch created                                        |
| FR-GIT-04 | Finalize git operations (commit + push + PR update)     | P0       | Atomic completion of git workflow                                     |
| FR-GIT-05 | Get PR number for branch name                           | P1       | Lookup existing PR for updates                                        |
| FR-GIT-06 | Update PR body with comprehensive summary               | P1       | Review/test results added to PR                                       |
| FR-GIT-07 | Support working directory override for worktree ops     | P0       | Git commands run in specified directory                               |

### 1.8 Workflow Phases (FR-WFL)

#### 1.8.1 Plan Phase

| ID          | Requirement                                            | Priority | Success Criteria                                                      |
|-------------|--------------------------------------------------------|----------|-----------------------------------------------------------------------|
| FR-WFL-P01  | Fetch issue from GitHub                                | P0       | Issue metadata available for planning                                 |
| FR-WFL-P02  | Classify issue type (feature/bug/chore)                | P0       | Correct slash command determined                                      |
| FR-WFL-P03  | Generate standardized branch name                      | P0       | Branch follows naming convention                                      |
| FR-WFL-P04  | Create git worktree with allocated ports               | P0       | Worktree ready for development                                        |
| FR-WFL-P05  | Execute planning agent with issue context              | P0       | Agent creates spec file                                               |
| FR-WFL-P06  | Create spec file in `specs/` directory                 | P0       | Markdown plan with sections for implementation                        |
| FR-WFL-P07  | Create initial commit with plan file                   | P0       | Plan committed to feature branch                                      |
| FR-WFL-P08  | Create pull request for branch                         | P0       | PR exists for tracking progress                                       |
| FR-WFL-P09  | Post progress to GitHub issue                          | P1       | User sees planning status                                             |
| FR-WFL-P10  | Save state with plan file path                         | P0       | Subsequent phases can find plan                                       |

#### 1.8.2 Build Phase

| ID          | Requirement                                            | Priority | Success Criteria                                                      |
|-------------|--------------------------------------------------------|----------|-----------------------------------------------------------------------|
| FR-WFL-B01  | Load state and validate worktree exists                | P0       | Fails if worktree missing                                             |
| FR-WFL-B02  | Find spec file from state                              | P0       | Plan path retrieved correctly                                         |
| FR-WFL-B03  | Execute `/implement` command with spec file            | P0       | Agent implements plan steps                                           |
| FR-WFL-B04  | Commit implementation changes                          | P0       | Code changes committed                                                |
| FR-WFL-B05  | Push and update PR                                     | P0       | Changes visible on GitHub                                             |
| FR-WFL-B06  | Post progress to GitHub issue                          | P1       | User sees build status                                                |

#### 1.8.3 Test Phase

| ID          | Requirement                                            | Priority | Success Criteria                                                      |
|-------------|--------------------------------------------------------|----------|-----------------------------------------------------------------------|
| FR-WFL-T01  | Load state and validate worktree exists                | P0       | Fails if worktree missing                                             |
| FR-WFL-T02  | Execute `/test` command in worktree                    | P0       | Test suite runs                                                       |
| FR-WFL-T03  | Parse test results as JSON array                       | P0       | TestResult list extracted                                             |
| FR-WFL-T04  | Attempt resolution of failed tests                     | P1       | `/resolve_failed_test` for each failure                               |
| FR-WFL-T05  | Retry tests after resolution (max 4 attempts)          | P1       | Loop until pass or max attempts                                       |
| FR-WFL-T06  | Execute `/test_e2e` if not skipped                     | P2       | E2E tests run with Playwright                                         |
| FR-WFL-T07  | Attempt resolution of failed E2E tests                 | P2       | `/resolve_failed_e2e_test` for each failure                           |
| FR-WFL-T08  | Retry E2E tests after resolution (max 2 attempts)      | P2       | Fewer retries for UI tests                                            |
| FR-WFL-T09  | Post comprehensive test summary                        | P1       | All results visible on issue                                          |
| FR-WFL-T10  | Commit test results regardless of pass/fail            | P0       | State captured for review phase                                       |
| FR-WFL-T11  | Continue workflow even with test failures              | P1       | Allow review to assess severity                                       |

#### 1.8.4 Review Phase

| ID          | Requirement                                            | Priority | Success Criteria                                                      |
|-------------|--------------------------------------------------------|----------|-----------------------------------------------------------------------|
| FR-WFL-R01  | Load state and validate worktree exists                | P0       | Fails if worktree missing                                             |
| FR-WFL-R02  | Find spec file from state                              | P0       | Review has requirements to validate                                   |
| FR-WFL-R03  | Execute `/review` command with spec file               | P0       | Agent reviews implementation                                          |
| FR-WFL-R04  | Classify issues as blocker/tech_debt/skippable         | P0       | Severity determines workflow outcome                                  |
| FR-WFL-R05  | Capture screenshots of critical functionality          | P1       | Visual proof of working features                                      |
| FR-WFL-R06  | Upload screenshots to R2 if configured                 | P2       | Persistent URLs for GitHub display                                    |
| FR-WFL-R07  | Resolve blocker issues automatically                   | P1       | Create patch plans and implement                                      |
| FR-WFL-R08  | Retry review after resolution (max 3 attempts)         | P1       | Loop until no blockers or max attempts                                |
| FR-WFL-R09  | Post review summary with issue details                 | P0       | Stakeholders see review outcome                                       |
| FR-WFL-R10  | Update PR body with review results                     | P1       | Comprehensive PR description                                          |

#### 1.8.5 Document Phase

| ID          | Requirement                                            | Priority | Success Criteria                                                      |
|-------------|--------------------------------------------------------|----------|-----------------------------------------------------------------------|
| FR-WFL-D01  | Load state and validate worktree exists                | P0       | Fails if worktree missing                                             |
| FR-WFL-D02  | Check for changes against origin/main                  | P1       | Skip if no changes                                                    |
| FR-WFL-D03  | Execute `/document` command with spec file             | P0       | Agent generates documentation                                         |
| FR-WFL-D04  | Create documentation in `app_docs/` directory          | P0       | Markdown file with feature description                                |
| FR-WFL-D05  | Copy screenshots to `app_docs/assets/`                 | P2       | Visual documentation preserved                                        |
| FR-WFL-D06  | Update `conditional_docs.md` with new entry            | P2       | Future agents know when to read docs                                  |
| FR-WFL-D07  | Track agentic KPIs (never fails workflow)              | P3       | Performance metrics captured                                          |
| FR-WFL-D08  | Commit documentation changes                           | P0       | Docs part of feature branch                                           |

#### 1.8.6 Ship Phase

| ID          | Requirement                                            | Priority | Success Criteria                                                      |
|-------------|--------------------------------------------------------|----------|-----------------------------------------------------------------------|
| FR-WFL-S01  | Load state and validate all fields populated           | P0       | Ship requires complete workflow                                       |
| FR-WFL-S02  | Validate worktree exists                               | P0       | State matches file system                                             |
| FR-WFL-S03  | Approve PR for branch                                  | P1       | PR has approval status                                                |
| FR-WFL-S04  | Merge feature branch to main (no-ff)                   | P0       | Preserves commit history                                              |
| FR-WFL-S05  | Push merged main to origin                             | P0       | Production code updated                                               |
| FR-WFL-S06  | Close source GitHub issue                              | P1       | Issue marked as resolved                                              |
| FR-WFL-S07  | Post success message to issue                          | P0       | User notified of completion                                           |

#### 1.8.7 SDLC Orchestration

| ID          | Requirement                                            | Priority | Success Criteria                                                      |
|-------------|--------------------------------------------------------|----------|-----------------------------------------------------------------------|
| FR-WFL-O01  | Chain phases: plan -> build -> test -> review -> doc   | P0       | Full lifecycle in sequence                                            |
| FR-WFL-O02  | Stop on plan failure                                   | P0       | No build without valid plan                                           |
| FR-WFL-O03  | Stop on build failure                                  | P0       | No test without implementation                                        |
| FR-WFL-O04  | Continue on test failure with warning                  | P1       | Allow review to assess impact                                         |
| FR-WFL-O05  | Stop on review failure                                 | P0       | No doc/ship with blockers                                             |
| FR-WFL-O06  | Pass `--skip-e2e` to test phase                        | P2       | Flag propagates correctly                                             |
| FR-WFL-O07  | Pass `--skip-resolution` to review phase               | P2       | Flag propagates correctly                                             |
| FR-WFL-O08  | Generate CxC ID if not provided                        | P0       | New workflows get unique ID                                           |
| FR-WFL-O09  | Reuse CxC ID if provided                               | P0       | Resume existing workflow                                              |
| FR-WFL-O10  | Print phase headers during execution                   | P1       | User sees progress                                                    |

#### 1.8.8 ZTE (Zero Touch Execution)

| ID          | Requirement                                            | Priority | Success Criteria                                                      |
|-------------|--------------------------------------------------------|----------|-----------------------------------------------------------------------|
| FR-WFL-Z01  | Run full SDLC plus ship phase                          | P1       | Complete automation                                                   |
| FR-WFL-Z02  | Stop on test failure (stricter than SDLC)              | P1       | No auto-merge with failing tests                                      |
| FR-WFL-Z03  | Stop on review failure                                 | P1       | No auto-merge with blockers                                           |
| FR-WFL-Z04  | Continue on documentation failure                      | P2       | Docs are non-blocking                                                 |
| FR-WFL-Z05  | Auto-merge to main on success                          | P1       | Hands-free deployment                                                 |
| FR-WFL-Z06  | Post ZTE status messages to issue                      | P1       | Clear automation feedback                                             |

### 1.9 Triggers (FR-TRG)

#### 1.9.1 Webhook Trigger

| ID          | Requirement                                            | Priority | Success Criteria                                                      |
|-------------|--------------------------------------------------------|----------|-----------------------------------------------------------------------|
| FR-TRG-W01  | Accept POST requests at `/gh-webhook` endpoint         | P1       | GitHub events received                                                |
| FR-TRG-W02  | Parse GitHub issue and issue_comment events            | P1       | Event payload extracted                                               |
| FR-TRG-W03  | Detect CxC workflow commands in issue body/comments    | P1       | `cxc_sdlc_iso`, `cxc_plan_iso`, etc.                                  |
| FR-TRG-W04  | Ignore CxC bot comments to prevent loops               | P0       | No infinite recursion                                                 |
| FR-TRG-W05  | Extract CxC ID if provided in comment                  | P1       | Resume existing workflow                                              |
| FR-TRG-W06  | Extract model_set from comment                         | P2       | `model_set heavy` triggers Opus                                       |
| FR-TRG-W07  | Launch workflow in background subprocess               | P0       | Respond within GitHub timeout                                         |
| FR-TRG-W08  | Return 200 immediately to prevent retries              | P0       | GitHub doesn't retry                                                  |
| FR-TRG-W09  | Validate dependent workflows require CxC ID            | P1       | build/test/review/doc/ship need existing worktree                     |
| FR-TRG-W10  | Provide `/health` endpoint for monitoring              | P2       | System status check                                                   |

#### 1.9.2 Cron Trigger

| ID          | Requirement                                            | Priority | Success Criteria                                                      |
|-------------|--------------------------------------------------------|----------|-----------------------------------------------------------------------|
| FR-TRG-C01  | Poll GitHub every 20 seconds                           | P2       | Regular check cadence                                                 |
| FR-TRG-C02  | Detect new issues without comments                     | P2       | Auto-process fresh issues                                             |
| FR-TRG-C03  | Detect issues with `cxc` in latest comment             | P2       | Comment-triggered processing                                          |
| FR-TRG-C04  | Track processed issues to prevent duplicates           | P2       | Each issue processed once per trigger                                 |
| FR-TRG-C05  | Handle graceful shutdown on SIGINT/SIGTERM             | P2       | Clean exit                                                            |
| FR-TRG-C06  | Trigger plan workflow for qualifying issues            | P2       | Default to planning phase                                             |

### 1.10 Slash Commands (FR-CMD)

| ID         | Requirement                                             | Priority | Success Criteria                                                      |
|------------|--------------------------------------------------------|----------|-----------------------------------------------------------------------|
| FR-CMD-01  | `/feature` - Create feature implementation plan        | P0       | Spec file with phases and tasks                                       |
| FR-CMD-02  | `/bug` - Create bug fix plan                           | P0       | Spec with root cause analysis                                         |
| FR-CMD-03  | `/chore` - Create maintenance task plan                | P0       | Minimal plan for simple tasks                                         |
| FR-CMD-04  | `/patch` - Create focused fix for review issues        | P1       | Targeted 2-5 step patch plan                                          |
| FR-CMD-05  | `/implement` - Execute implementation plan             | P0       | All plan tasks completed                                              |
| FR-CMD-06  | `/review` - Validate against specification             | P0       | JSON with success, issues, screenshots                                |
| FR-CMD-07  | `/document` - Generate feature documentation           | P1       | Markdown file with usage guide                                        |
| FR-CMD-08  | `/test` - Run test suite and report results            | P0       | JSON array of TestResult                                              |
| FR-CMD-09  | `/test_e2e` - Run E2E tests with Playwright            | P2       | JSON array of E2ETestResult                                           |
| FR-CMD-10  | `/resolve_failed_test` - Fix specific test failure     | P1       | Test passes after resolution                                          |
| FR-CMD-11  | `/resolve_failed_e2e_test` - Fix E2E test failure      | P2       | E2E test passes after resolution                                      |
| FR-CMD-12  | `/classify_issue` - Determine issue type               | P0       | Returns /feature, /bug, /chore, or /patch                             |
| FR-CMD-13  | `/classify_and_branch` - Combined classification       | P1       | JSON with issue_class and branch_name                                 |
| FR-CMD-14  | `/commit` - Generate git commit message                | P0       | Structured commit message                                             |
| FR-CMD-15  | `/pull_request` - Create GitHub PR                     | P0       | Returns PR URL                                                        |
| FR-CMD-16  | `/generate_branch_name` - Create standardized name     | P1       | Follows naming convention                                             |

### 1.11 R2 Integration (FR-R2)

| ID        | Requirement                                              | Priority | Success Criteria                                                      |
|-----------|----------------------------------------------------------|----------|-----------------------------------------------------------------------|
| FR-R2-01  | Upload screenshots to Cloudflare R2                     | P3       | Files accessible via public URL                                       |
| FR-R2-02  | Support optional R2 configuration via env vars          | P3       | Graceful degradation without R2                                       |
| FR-R2-03  | Return local path if upload disabled or fails           | P3       | Fallback behavior                                                     |
| FR-R2-04  | Organize uploads by CxC ID                              | P3       | Path: `cxc/{cxc_id}/review/{filename}`                                |

### 1.12 Health Checks (FR-HLT)

| ID        | Requirement                                              | Priority | Success Criteria                                                      |
|-----------|----------------------------------------------------------|----------|-----------------------------------------------------------------------|
| FR-HLT-01 | Check required environment variables                    | P1       | ANTHROPIC_API_KEY validation                                          |
| FR-HLT-02 | Check git repository configuration                      | P1       | Valid remote URL                                                      |
| FR-HLT-03 | Check GitHub CLI authentication                         | P1       | `gh auth status` succeeds                                             |
| FR-HLT-04 | Check Claude Code CLI functionality                     | P1       | Simple prompt returns result                                          |
| FR-HLT-05 | Return comprehensive health status                      | P1       | HealthCheckResult with all check results                              |

---

## 2. Non-Functional Requirements

### 2.1 Performance (NFR-PER)

| ID         | Requirement                                             | Priority | Success Criteria                                                      |
|------------|--------------------------------------------------------|----------|-----------------------------------------------------------------------|
| NFR-PER-01 | Webhook responds within 10 seconds                     | P0       | GitHub doesn't retry                                                  |
| NFR-PER-02 | Support 15 concurrent workflow instances               | P1       | Port allocation supports concurrency                                  |
| NFR-PER-03 | State save/load completes in under 100ms               | P1       | Minimal I/O overhead                                                  |
| NFR-PER-04 | Cron polling completes cycle in under 5 seconds        | P2       | Efficient GitHub API usage                                            |

### 2.2 Reliability (NFR-REL)

| ID         | Requirement                                             | Priority | Success Criteria                                                      |
|------------|--------------------------------------------------------|----------|-----------------------------------------------------------------------|
| NFR-REL-01 | State persists across process restarts                 | P0       | Workflows can be resumed                                              |
| NFR-REL-02 | Failed phases log detailed error information           | P0       | Root cause identifiable                                               |
| NFR-REL-03 | Worktree isolation prevents cross-workflow interference| P0       | Parallel workflows don't conflict                                     |
| NFR-REL-04 | Git operations are atomic within phase                 | P1       | No partial commits                                                    |
| NFR-REL-05 | CxC bot comment loop prevention                        | P0       | No infinite webhook triggers                                          |

### 2.3 Maintainability (NFR-MNT)

| ID         | Requirement                                             | Priority | Success Criteria                                                      |
|------------|--------------------------------------------------------|----------|-----------------------------------------------------------------------|
| NFR-MNT-01 | Modular workflow structure (one file per phase)        | P1       | Easy to modify individual phases                                      |
| NFR-MNT-02 | Clear separation between core, integrations, workflows | P1       | Organized package structure                                           |
| NFR-MNT-03 | Pydantic models for all data structures                | P1       | Type-safe data handling                                               |
| NFR-MNT-04 | Consistent logging format across modules               | P1       | Unified log analysis                                                  |
| NFR-MNT-05 | Comprehensive test coverage                            | P2       | Unit and integration tests                                            |

### 2.4 Extensibility (NFR-EXT)

| ID         | Requirement                                             | Priority | Success Criteria                                                      |
|------------|--------------------------------------------------------|----------|-----------------------------------------------------------------------|
| NFR-EXT-01 | Pluggable command templates via commands directories   | P1       | Project overrides framework commands                                  |
| NFR-EXT-02 | Configuration via YAML file                            | P0       | No code changes for project setup                                     |
| NFR-EXT-03 | Environment-based secrets management                   | P0       | Standard .env pattern                                                 |
| NFR-EXT-04 | Clear interface between CxC and Claude Code            | P1       | Agent abstraction layer                                               |

### 2.5 Security (NFR-SEC)

| ID         | Requirement                                             | Priority | Success Criteria                                                      |
|------------|--------------------------------------------------------|----------|-----------------------------------------------------------------------|
| NFR-SEC-01 | Secrets stored in .env file only                       | P0       | No hardcoded credentials                                              |
| NFR-SEC-02 | Safe subprocess environment filtering                  | P1       | Only required vars passed to subprocesses                             |
| NFR-SEC-03 | No credential logging                                  | P0       | API keys not in logs                                                  |
| NFR-SEC-04 | GitHub PAT optional (falls back to gh auth)            | P1       | Minimal credential requirements                                       |

### 2.6 Usability (NFR-USA)

| ID         | Requirement                                             | Priority | Success Criteria                                                      |
|------------|--------------------------------------------------------|----------|-----------------------------------------------------------------------|
| NFR-USA-01 | Clear CLI help text                                    | P1       | `--help` explains all commands                                        |
| NFR-USA-02 | Progress updates on GitHub issues                      | P1       | User visibility into workflow state                                   |
| NFR-USA-03 | Structured error messages                              | P1       | Actionable error guidance                                             |
| NFR-USA-04 | Setup script for easy onboarding                       | P1       | Single command project setup                                          |

---

## 3. Constraints

| ID       | Constraint                                               |
|----------|----------------------------------------------------------|
| CON-01   | Requires Python 3.12 or higher                           |
| CON-02   | Requires `uv` package manager                            |
| CON-03   | Requires GitHub CLI (`gh`) installed and authenticated   |
| CON-04   | Requires Claude Code CLI installed                       |
| CON-05   | Must operate within GitHub API rate limits               |
| CON-06   | Worktrees require git 2.5+ with worktree support         |
| CON-07   | R2 integration requires Cloudflare account (optional)    |
| CON-08   | E2E tests require Playwright browser automation          |

---

## 4. Dependencies

| Dependency       | Purpose                                    | Required |
|------------------|--------------------------------------------|----------|
| python-dotenv    | Environment variable loading               | Yes      |
| pydantic         | Data validation and serialization          | Yes      |
| PyYAML           | Configuration file parsing                 | Yes      |
| fastapi          | Webhook server                             | Optional |
| uvicorn          | ASGI server for webhook                    | Optional |
| boto3            | R2 upload via S3 API                       | Optional |
| schedule         | Cron trigger scheduling                    | Optional |
| pytest           | Test execution                             | Dev      |
| ruff             | Linting                                    | Dev      |

---

## 5. Glossary

| Term             | Definition                                                                |
|------------------|---------------------------------------------------------------------------|
| CxC              | Cortex Code - the framework name                                |
| CxC ID           | 8-character unique identifier for a workflow instance                     |
| Worktree         | Git worktree providing isolated development environment                   |
| SDLC             | Software Development Life Cycle - plan/build/test/review/document/ship   |
| ZTE              | Zero Touch Execution - fully automated SDLC with auto-merge              |
| Slash Command    | Markdown template invoked via `/command` syntax                           |
| Model Set        | Selection between base (Sonnet) and heavy (Opus) LLM models               |
| Spec File        | Implementation plan created during planning phase                         |
| Issue Class      | Categorization as feature, bug, chore, or patch                           |
