# ADW Framework - System Requirements Specification (Claude)

**Version**: 1.0.0
**Date**: 2025-12-30
**Purpose**: Complete system requirements for rebuilding the ADW Framework from scratch

---

## Table of Contents

1. [Overview](#overview)
2. [CLI & Entry Point Requirements](#cli--entry-point-requirements)
3. [Configuration Requirements](#configuration-requirements)
4. [State Management Requirements](#state-management-requirements)
5. [Agent Execution Requirements](#agent-execution-requirements)
6. [Workflow Orchestration Requirements](#workflow-orchestration-requirements)
7. [Git Operations Requirements](#git-operations-requirements)
8. [GitHub Integration Requirements](#github-integration-requirements)
9. [Worktree Management Requirements](#worktree-management-requirements)
10. [Port Allocation Requirements](#port-allocation-requirements)
11. [Slash Command Requirements](#slash-command-requirements)
12. [Artifact Management Requirements](#artifact-management-requirements)
13. [Logging & Observability Requirements](#logging--observability-requirements)
14. [Error Handling Requirements](#error-handling-requirements)
15. [Security Requirements](#security-requirements)

---

## Overview

ADW (Cortex Code) is an orchestration framework that automates software development using Claude Code agents in isolated git worktrees. It processes GitHub issues through a complete SDLC pipeline: plan -> build -> test -> review -> document -> ship.

---

## CLI & Entry Point Requirements

### REQ-CLI-001: Main Entry Point
| Field | Value |
|-------|-------|
| **Title** | CLI Main Entry Point via Typer |
| **Description** | The system SHALL provide a CLI entry point using the Typer library, accessible via `uv run adw` or `python -m adw.cli`. The CLI SHALL display a styled header with project name "Cortex Code (ADW)" and version. |
| **Rationale** | Provides consistent, user-friendly command-line interface for all ADW operations |
| **Acceptance Criteria** | - `uv run adw --help` displays available commands<br>- Version displayed matches package version<br>- Styled header uses Rich library formatting |

### REQ-CLI-002: SDLC Command
| Field | Value |
|-------|-------|
| **Title** | Full SDLC Pipeline Command |
| **Description** | The CLI SHALL provide an `sdlc` command that accepts `issue_number` (required), `adw_id` (optional), `--skip-e2e` flag, and `--skip-resolution` flag. It SHALL chain: plan_iso -> build_iso -> test_iso -> review_iso -> document_iso. |
| **Rationale** | Enables complete automated development workflow from issue to documentation |
| **Acceptance Criteria** | - `uv run adw sdlc 42` processes issue #42 through all phases<br>- `uv run adw sdlc 42 abc12345` uses specified ADW ID<br>- `--skip-e2e` skips end-to-end tests<br>- `--skip-resolution` skips automatic blocker resolution in review |

### REQ-CLI-003: Plan Command
| Field | Value |
|-------|-------|
| **Title** | Planning Phase Command |
| **Description** | The CLI SHALL provide a `plan` command that accepts `issue_number` (required) and `adw_id` (optional). It SHALL execute only the planning phase in isolated worktree. |
| **Rationale** | Allows running planning phase independently for iterative development |
| **Acceptance Criteria** | - Creates worktree with allocated ports<br>- Classifies issue type<br>- Generates branch name<br>- Creates implementation plan file<br>- Commits and creates/updates PR |

### REQ-CLI-004: Build Command
| Field | Value |
|-------|-------|
| **Title** | Build Phase Command |
| **Description** | The CLI SHALL provide a `build` command that requires both `issue_number` and `adw_id`. It SHALL execute the implementation phase using existing plan from prior planning phase. |
| **Rationale** | Enables separate build execution after planning approval |
| **Acceptance Criteria** | - Validates worktree exists from prior planning<br>- Loads plan file from state<br>- Executes implementation<br>- Commits changes to worktree branch |

### REQ-CLI-005: Test Command
| Field | Value |
|-------|-------|
| **Title** | Test Phase Command |
| **Description** | The CLI SHALL provide a `test` command that requires `issue_number` and `adw_id`, with optional `--skip-e2e` flag. It SHALL run unit tests and optionally E2E tests with automatic resolution loops. |
| **Rationale** | Enables isolated testing with automatic failure resolution |
| **Acceptance Criteria** | - Runs unit tests with up to 4 retry attempts<br>- Runs E2E tests with up to 2 retry attempts (unless --skip-e2e)<br>- Posts test summaries to GitHub issue |

### REQ-CLI-006: Review Command
| Field | Value |
|-------|-------|
| **Title** | Review Phase Command |
| **Description** | The CLI SHALL provide a `review` command with optional `--skip-resolution` flag. It SHALL review implementation against spec, capture screenshots, and optionally auto-resolve blockers. |
| **Rationale** | Enables automated code review with visual validation |
| **Acceptance Criteria** | - Reviews implementation against original issue spec<br>- Captures and uploads screenshots to R2<br>- Identifies blocker issues<br>- Auto-resolves blockers up to 3 attempts (unless --skip-resolution) |

### REQ-CLI-007: Document Command
| Field | Value |
|-------|-------|
| **Title** | Documentation Phase Command |
| **Description** | The CLI SHALL provide a `document` command that generates feature documentation based on implementation. |
| **Rationale** | Ensures all features are properly documented |
| **Acceptance Criteria** | - Generates documentation for implemented changes<br>- Commits documentation to worktree branch<br>- Posts documentation summary to issue |

### REQ-CLI-008: Ship Command
| Field | Value |
|-------|-------|
| **Title** | Ship/Merge Phase Command |
| **Description** | The CLI SHALL provide a `ship` command that approves and merges the PR after successful review. |
| **Rationale** | Enables zero-touch execution through to merge |
| **Acceptance Criteria** | - Approves PR via gh CLI<br>- Merges PR to main branch<br>- Posts completion summary to issue |

### REQ-CLI-009: ZTE Command
| Field | Value |
|-------|-------|
| **Title** | Zero Touch Execution Command |
| **Description** | The CLI SHALL provide a `zte` command that runs full SDLC plus automatic PR merge (sdlc + ship). |
| **Rationale** | Enables fully automated issue-to-merge workflow |
| **Acceptance Criteria** | - Executes complete SDLC pipeline<br>- Automatically approves and merges PR on success |

### REQ-CLI-010: Patch Command
| Field | Value |
|-------|-------|
| **Title** | Patch Workflow Command |
| **Description** | The CLI SHALL provide a `patch` command for smaller changes that require less rigorous workflow than full SDLC. |
| **Rationale** | Enables lightweight changes without full SDLC overhead |
| **Acceptance Criteria** | - Creates worktree if not exists<br>- Implements patch directly<br>- Commits and creates PR |

### REQ-CLI-011: Cleanup Command
| Field | Value |
|-------|-------|
| **Title** | Worktree Cleanup Command |
| **Description** | The CLI SHALL provide a `cleanup` command that removes worktrees and associated artifacts for a given ADW ID. |
| **Rationale** | Enables resource cleanup after workflow completion |
| **Acceptance Criteria** | - Removes worktree directory<br>- Optionally removes artifact directory<br>- Removes git worktree reference |

---

## Configuration Requirements

### REQ-CFG-001: YAML Configuration File
| Field | Value |
|-------|-------|
| **Title** | Project Configuration via .adw.yaml |
| **Description** | The system SHALL load project configuration from `.adw.yaml` file in project root. The file SHALL support: `project_id`, `artifacts_dir`, `source_root`, `ports` (backend_start, frontend_start), and `commands` (list of command directories). |
| **Rationale** | Enables per-project customization of ADW behavior |
| **Acceptance Criteria** | - Loads `.adw.yaml` from current working directory<br>- Falls back to defaults if file not found<br>- Validates required fields |

### REQ-CFG-002: Project ID Auto-Detection
| Field | Value |
|-------|-------|
| **Title** | Auto-detect Project ID from Git Remote |
| **Description** | If `project_id` is not specified in config, the system SHALL auto-detect it from the git remote URL using pattern `github.com[:/](.+/.+?)(\.git)?$`. |
| **Rationale** | Reduces configuration burden for standard GitHub projects |
| **Acceptance Criteria** | - Extracts org/repo from HTTPS URL<br>- Extracts org/repo from SSH URL<br>- Returns None if no git remote found |

### REQ-CFG-003: ADWConfig Singleton
| Field | Value |
|-------|-------|
| **Title** | Configuration Singleton Pattern |
| **Description** | The ADWConfig class SHALL implement singleton pattern, instantiated once per process. It SHALL provide: `project_id`, `artifacts_dir`, `source_root`, `ports`, `command_dirs`, `project_root`. |
| **Rationale** | Ensures consistent configuration access throughout application |
| **Acceptance Criteria** | - Same instance returned on repeated calls<br>- All paths resolved to absolute paths<br>- Environment variable expansion supported |

### REQ-CFG-004: Command Directory Resolution
| Field | Value |
|-------|-------|
| **Title** | Multi-source Command Directory Resolution |
| **Description** | The system SHALL resolve command directories from: (1) `${ADW_FRAMEWORK}/commands` for framework commands, (2) project-local `.claude/commands/`, and (3) any additional paths specified in config. The `${ADW_FRAMEWORK}` variable SHALL resolve to the adw package installation directory. |
| **Rationale** | Enables command layering with framework defaults and project overrides |
| **Acceptance Criteria** | - Framework commands available by default<br>- Project commands override framework commands with same name<br>- Additional custom command directories supported |

### REQ-CFG-005: Environment Variable Loading
| Field | Value |
|-------|-------|
| **Title** | Environment Variable Loading via dotenv |
| **Description** | The system SHALL load environment variables from `.env` file in project root using python-dotenv. Required variables: `ANTHROPIC_API_KEY`. Optional: `GITHUB_PAT`, `CLAUDE_CODE_PATH`. |
| **Rationale** | Enables secure credential management outside source control |
| **Acceptance Criteria** | - `.env` file loaded at startup<br>- Missing `ANTHROPIC_API_KEY` raises warning<br>- `CLAUDE_CODE_PATH` defaults to "claude" |

---

## State Management Requirements

### REQ-STATE-001: ADWState Persistence
| Field | Value |
|-------|-------|
| **Title** | JSON-based State Persistence |
| **Description** | The system SHALL persist workflow state to `adw_state.json` within the ADW artifacts directory (`artifacts/{project_id}/{adw_id}/adw_state.json`). State SHALL be saved atomically after each significant operation. |
| **Rationale** | Enables workflow resumption and cross-phase state sharing |
| **Acceptance Criteria** | - State persisted as valid JSON<br>- Atomic writes prevent corruption<br>- State loadable across process restarts |

### REQ-STATE-002: State Data Model
| Field | Value |
|-------|-------|
| **Title** | ADWStateData Pydantic Model |
| **Description** | The state SHALL conform to ADWStateData model with fields: `adw_id` (str), `issue_number` (str, optional), `branch_name` (str, optional), `plan_file` (str, optional), `issue_class` (SlashCommand, optional), `worktree_path` (str, optional), `backend_port` (int, optional), `frontend_port` (int, optional), `model_set` (Literal["base", "heavy"], optional), `all_adws` (list[str], optional). |
| **Rationale** | Ensures type-safe state handling across workflow phases |
| **Acceptance Criteria** | - All fields properly typed<br>- Optional fields default to None<br>- Model validates on load/save |

### REQ-STATE-003: State Load/Save Operations
| Field | Value |
|-------|-------|
| **Title** | State Load and Save Methods |
| **Description** | ADWState class SHALL provide: `load(adw_id, logger)` class method returning state or None, `save(caller)` instance method persisting current state, `update(**kwargs)` method for partial updates, `get(key, default)` method for field access. |
| **Rationale** | Provides clean API for state manipulation |
| **Acceptance Criteria** | - `load()` returns None if no state file exists<br>- `save()` creates directory if needed<br>- `update()` preserves existing fields not specified |

### REQ-STATE-004: Workflow Tracking
| Field | Value |
|-------|-------|
| **Title** | Track All ADW Workflow Executions |
| **Description** | The state SHALL track all ADW workflows that have run via `all_adws` list. Each workflow SHALL call `state.append_adw_id(workflow_name)` to record execution. |
| **Rationale** | Enables audit trail and debugging of workflow execution history |
| **Acceptance Criteria** | - Each workflow appends its name to `all_adws`<br>- Duplicate entries preserved (tracks re-runs)<br>- List persisted across saves |

### REQ-STATE-005: State Directory Structure
| Field | Value |
|-------|-------|
| **Title** | Hierarchical State Directory |
| **Description** | State files SHALL be organized under: `{artifacts_dir}/{project_id}/{adw_id}/adw_state.json`. The `project_id` SHALL use path-safe format (slashes replaced with OS path separator). |
| **Rationale** | Enables multiple projects and multiple workflows per project |
| **Acceptance Criteria** | - Directory created on first save<br>- Project isolation maintained<br>- ADW ID isolation maintained |

---

## Agent Execution Requirements

### REQ-AGENT-001: Claude Code CLI Integration
| Field | Value |
|-------|-------|
| **Title** | Execute Claude Code via CLI |
| **Description** | The system SHALL execute Claude Code agent via subprocess call to the `claude` CLI (or path specified in `CLAUDE_CODE_PATH`). Commands SHALL be passed via `--prompt` flag with `--yes-to-all` for non-interactive mode. |
| **Rationale** | Enables programmatic control of Claude Code agent |
| **Acceptance Criteria** | - Subprocess spawned with correct arguments<br>- Output captured for processing<br>- Exit code handled appropriately |

### REQ-AGENT-002: Template Execution
| Field | Value |
|-------|-------|
| **Title** | AgentTemplateRequest Execution |
| **Description** | The system SHALL provide `execute_template(request: AgentTemplateRequest)` function that: (1) loads slash command template, (2) substitutes `$ARGUMENTS` placeholder, (3) executes via Claude CLI, (4) returns AgentTemplateResponse with success status and output. |
| **Rationale** | Standardizes agent invocation across all workflows |
| **Acceptance Criteria** | - Template loaded from command directories<br>- Arguments properly substituted<br>- Response includes raw output and success boolean |

### REQ-AGENT-003: Model Set Selection
| Field | Value |
|-------|-------|
| **Title** | Base vs Heavy Model Selection |
| **Description** | The system SHALL select model tier based on `model_set` in state. "heavy" model (Opus) SHALL be used for: `/implement`, `/document`, `/feature`, `/bug`, `/chore`, `/patch`. "base" model (Sonnet) SHALL be used for all other commands. Model selection passed via `--model` flag to Claude CLI. |
| **Rationale** | Balances cost vs capability for different task complexities |
| **Acceptance Criteria** | - Heavy commands use opus model<br>- Other commands use sonnet model<br>- Model flag correctly passed to CLI |

### REQ-AGENT-004: Working Directory Control
| Field | Value |
|-------|-------|
| **Title** | Agent Working Directory Specification |
| **Description** | The `execute_template` function SHALL accept optional `working_dir` parameter. When specified, agent SHALL execute with that directory as cwd. This enables worktree-isolated execution. |
| **Rationale** | Enables isolated execution in worktrees |
| **Acceptance Criteria** | - Subprocess cwd set to working_dir<br>- Agent sees correct file system context<br>- Defaults to current directory if not specified |

### REQ-AGENT-005: Prompt Persistence
| Field | Value |
|-------|-------|
| **Title** | Save Agent Prompts to Artifacts |
| **Description** | Before execution, the system SHALL save the complete prompt to: `{artifacts_dir}/{project_id}/{adw_id}/{agent_name}/prompts/{timestamp}.md`. This enables debugging and audit. |
| **Rationale** | Enables debugging and reproducibility of agent interactions |
| **Acceptance Criteria** | - Prompt file created before execution<br>- Timestamp in ISO format<br>- Directory created if not exists |

### REQ-AGENT-006: Output Persistence
| Field | Value |
|-------|-------|
| **Title** | Save Agent Output to Artifacts |
| **Description** | After execution, the system SHALL append agent output to: `{artifacts_dir}/{project_id}/{adw_id}/{agent_name}/raw_output.jsonl`. Each line SHALL be JSON with timestamp, prompt hash, and output. |
| **Rationale** | Enables output analysis and debugging |
| **Acceptance Criteria** | - Output appended as JSONL line<br>- Includes execution timestamp<br>- File created if not exists |

### REQ-AGENT-007: Subprocess Environment Filtering
| Field | Value |
|-------|-------|
| **Title** | Safe Subprocess Environment |
| **Description** | The system SHALL filter environment variables passed to agent subprocess using `get_safe_subprocess_env()`. It SHALL include: PATH, HOME, USER, SHELL, LANG, LC_*, TERM, ANTHROPIC_API_KEY, GITHUB_PAT, CLAUDE_*, ADW_*, and worktree-specific PORT_* variables. |
| **Rationale** | Prevents sensitive environment leakage while enabling necessary functionality |
| **Acceptance Criteria** | - Only allowlisted variables passed<br>- API keys included for agent operation<br>- Port variables included for worktree isolation |

---

## Workflow Orchestration Requirements

### REQ-WF-001: ADW ID Generation
| Field | Value |
|-------|-------|
| **Title** | Unique ADW ID Generation |
| **Description** | The system SHALL generate 8-character unique IDs using UUID4 truncation: `str(uuid.uuid4())[:8]`. This ID SHALL be used for: state file paths, worktree paths, artifact paths, port allocation. |
| **Rationale** | Provides short, unique identifiers for workflow instances |
| **Acceptance Criteria** | - 8 character alphanumeric string<br>- Collision probability acceptably low<br>- Used consistently across all operations |

### REQ-WF-002: ensure_adw_id Function
| Field | Value |
|-------|-------|
| **Title** | ADW ID Initialization |
| **Description** | The `ensure_adw_id(issue_number, adw_id, logger)` function SHALL: (1) use provided adw_id if given, (2) else search for existing state for issue_number, (3) else generate new adw_id. It SHALL initialize ADWState with issue_number. |
| **Rationale** | Enables workflow resumption and new workflow creation |
| **Acceptance Criteria** | - Existing ID reused when provided<br>- Searches for prior state by issue<br>- Creates new ID when none found |

### REQ-WF-003: Plan Phase Workflow
| Field | Value |
|-------|-------|
| **Title** | plan_iso Workflow Steps |
| **Description** | The plan_iso workflow SHALL: (1) fetch GitHub issue details, (2) allocate ports, (3) classify issue type via `/classify_and_branch`, (4) create git worktree, (5) setup worktree environment, (6) build implementation plan via `/feature`, `/bug`, or `/chore`, (7) commit plan, (8) push and create/update PR. |
| **Rationale** | Establishes isolated environment and creates implementation roadmap |
| **Acceptance Criteria** | - Issue fetched successfully<br>- Worktree created with correct branch<br>- Plan file created and committed<br>- PR created/updated on GitHub |

### REQ-WF-004: Build Phase Workflow
| Field | Value |
|-------|-------|
| **Title** | build_iso Workflow Steps |
| **Description** | The build_iso workflow SHALL: (1) validate worktree exists (REQUIRED), (2) load plan file from state, (3) execute `/implement` with plan file, (4) commit implementation, (5) push and update PR. |
| **Rationale** | Implements the planned solution in isolated environment |
| **Acceptance Criteria** | - Fails if worktree doesn't exist<br>- Fails if plan file not in state<br>- Implementation committed to branch |

### REQ-WF-005: Test Phase Workflow
| Field | Value |
|-------|-------|
| **Title** | test_iso Workflow Steps |
| **Description** | The test_iso workflow SHALL: (1) validate worktree exists, (2) run unit tests via `/test`, (3) on failure, retry up to MAX_TEST_RETRY_ATTEMPTS (4) with `/resolve_failed_test`, (4) optionally run E2E tests via `/test_e2e`, (5) on E2E failure, retry up to MAX_E2E_TEST_RETRY_ATTEMPTS (2) with `/resolve_failed_e2e_test`, (6) post test summary to issue. |
| **Rationale** | Validates implementation with automatic failure resolution |
| **Acceptance Criteria** | - Unit tests executed<br>- Failed tests trigger resolution attempts<br>- E2E tests optional via flag<br>- Summary posted to issue |

### REQ-WF-006: Review Phase Workflow
| Field | Value |
|-------|-------|
| **Title** | review_iso Workflow Steps |
| **Description** | The review_iso workflow SHALL: (1) validate worktree exists, (2) execute `/review` against original issue, (3) capture screenshots and upload to R2, (4) parse review result for blockers, (5) if blockers and --skip-resolution not set, attempt resolution up to MAX_REVIEW_RETRY_ATTEMPTS (3), (6) update PR body with review summary. |
| **Rationale** | Validates implementation meets requirements with visual verification |
| **Acceptance Criteria** | - Review executed against issue spec<br>- Screenshots captured and uploaded<br>- Blockers identified and optionally resolved<br>- PR body updated with summary |

### REQ-WF-007: Document Phase Workflow
| Field | Value |
|-------|-------|
| **Title** | document_iso Workflow Steps |
| **Description** | The document_iso workflow SHALL: (1) validate worktree exists, (2) execute `/document` to generate feature docs, (3) commit documentation, (4) push and update PR. |
| **Rationale** | Ensures all features are properly documented |
| **Acceptance Criteria** | - Documentation generated<br>- Documentation committed<br>- Changes pushed to PR |

### REQ-WF-008: Ship Phase Workflow
| Field | Value |
|-------|-------|
| **Title** | ship_iso Workflow Steps |
| **Description** | The ship_iso workflow SHALL: (1) approve PR via `gh pr review --approve`, (2) merge PR via `gh pr merge --merge`, (3) post completion to issue. |
| **Rationale** | Enables zero-touch execution through to merge |
| **Acceptance Criteria** | - PR approved<br>- PR merged to main<br>- Issue notified of completion |

### REQ-WF-009: SDLC Chaining
| Field | Value |
|-------|-------|
| **Title** | SDLC Phase Chaining |
| **Description** | The sdlc_iso workflow SHALL chain phases sequentially via subprocess calls: plan_iso -> build_iso -> test_iso -> review_iso -> document_iso. Each phase SHALL receive the same issue_number and adw_id. Flags (--skip-e2e, --skip-resolution) SHALL be passed to appropriate phases. |
| **Rationale** | Enables complete automated workflow |
| **Acceptance Criteria** | - Each phase called with correct args<br>- Failure in any phase stops chain (except test)<br>- Test phase continues on failure with warning |

### REQ-WF-010: Patch Workflow
| Field | Value |
|-------|-------|
| **Title** | patch_iso Lightweight Workflow |
| **Description** | The patch_iso workflow SHALL: (1) create worktree if not exists, (2) execute `/patch` directly without full planning, (3) commit changes, (4) push and create/update PR. |
| **Rationale** | Enables quick fixes without full SDLC overhead |
| **Acceptance Criteria** | - Works without prior plan<br>- Creates worktree if needed<br>- Faster than full SDLC |

---

## Git Operations Requirements

### REQ-GIT-001: Branch Name Generation
| Field | Value |
|-------|-------|
| **Title** | Standardized Branch Name Format |
| **Description** | The system SHALL generate branch names via `/generate_branch_name` command with format: `{type}-issue-{number}-adw-{adw_id}-{description}` where type is feature/fix/chore, description is kebab-case summary. |
| **Rationale** | Ensures consistent, traceable branch naming |
| **Acceptance Criteria** | - Includes issue type prefix<br>- Includes issue number<br>- Includes ADW ID for uniqueness<br>- Description is kebab-case |

### REQ-GIT-002: Commit Message Generation
| Field | Value |
|-------|-------|
| **Title** | Commit Message via Agent |
| **Description** | The system SHALL generate commit messages via `/commit` command. Messages SHALL follow conventional commits format with reference to issue number. |
| **Rationale** | Ensures consistent, meaningful commit messages |
| **Acceptance Criteria** | - Conventional commit format (feat:, fix:, chore:)<br>- References issue number<br>- Describes changes accurately |

### REQ-GIT-003: Commit Changes Function
| Field | Value |
|-------|-------|
| **Title** | Git Commit Execution |
| **Description** | The `commit_changes(message, cwd)` function SHALL: (1) stage all changes via `git add -A`, (2) commit with provided message, (3) return success boolean and error message. |
| **Rationale** | Standardizes git commit operations |
| **Acceptance Criteria** | - All changes staged<br>- Commit created with message<br>- Error handling for empty commits |

### REQ-GIT-004: Push and PR Operations
| Field | Value |
|-------|-------|
| **Title** | finalize_git_operations Function |
| **Description** | The `finalize_git_operations(state, logger, cwd)` function SHALL: (1) push branch to origin, (2) create PR if not exists via `gh pr create`, (3) update existing PR if exists. It SHALL use branch name and PR info from state. |
| **Rationale** | Standardizes push and PR operations |
| **Acceptance Criteria** | - Branch pushed to remote<br>- PR created with correct base branch<br>- Existing PR updated rather than duplicated |

### REQ-GIT-005: Current Branch Detection
| Field | Value |
|-------|-------|
| **Title** | Get Current Branch Name |
| **Description** | The `get_current_branch(cwd)` function SHALL return the current git branch name via `git rev-parse --abbrev-ref HEAD`. |
| **Rationale** | Enables branch-aware operations |
| **Acceptance Criteria** | - Returns branch name string<br>- Works in worktrees<br>- Returns None on error |

---

## GitHub Integration Requirements

### REQ-GH-001: Issue Fetching
| Field | Value |
|-------|-------|
| **Title** | Fetch GitHub Issue Details |
| **Description** | The `fetch_issue(issue_number, repo_path)` function SHALL fetch issue details via `gh issue view` command. It SHALL return GitHubIssue model with: number, title, body, labels, state, author, created_at, updated_at. |
| **Rationale** | Provides issue context for planning and implementation |
| **Acceptance Criteria** | - Issue data fetched via gh CLI<br>- Parsed into GitHubIssue model<br>- All fields populated |

### REQ-GH-002: Issue Comments
| Field | Value |
|-------|-------|
| **Title** | Post Comments to Issues |
| **Description** | The `make_issue_comment(issue_number, body)` function SHALL post comment to GitHub issue via `gh issue comment`. Comments SHALL include ADW ID prefix for traceability. |
| **Rationale** | Provides visibility into workflow progress on GitHub |
| **Acceptance Criteria** | - Comment posted to correct issue<br>- ADW ID included in comment<br>- Markdown formatting preserved |

### REQ-GH-003: PR Creation
| Field | Value |
|-------|-------|
| **Title** | Create Pull Request |
| **Description** | The system SHALL create PRs via `gh pr create` with: title from commit message, body with issue reference, base branch (main/master). |
| **Rationale** | Automates PR creation for review |
| **Acceptance Criteria** | - PR created with correct title<br>- Body references issue<br>- Correct base branch used |

### REQ-GH-004: PR Updates
| Field | Value |
|-------|-------|
| **Title** | Update Pull Request |
| **Description** | The system SHALL update existing PRs via `gh pr edit` to update body with review summaries, test results, and status updates. |
| **Rationale** | Keeps PR up-to-date with workflow progress |
| **Acceptance Criteria** | - PR body updated correctly<br>- Previous content preserved where appropriate<br>- Markdown formatting maintained |

### REQ-GH-005: Repo URL Extraction
| Field | Value |
|-------|-------|
| **Title** | Extract Repository Path |
| **Description** | The `extract_repo_path(url)` function SHALL extract `org/repo` from GitHub URLs (both HTTPS and SSH formats). The `get_repo_url()` function SHALL return the origin remote URL. |
| **Rationale** | Enables GitHub API operations with correct repository context |
| **Acceptance Criteria** | - Handles HTTPS URLs<br>- Handles SSH URLs<br>- Returns org/repo format |

### REQ-GH-006: Artifact Posting
| Field | Value |
|-------|-------|
| **Title** | Post Artifacts to Issues |
| **Description** | The `post_artifact_to_issue()` function SHALL post formatted artifacts (plans, reports, etc.) to GitHub issues with: title, collapsible content block, file path reference, ADW ID prefix. |
| **Rationale** | Provides visibility into generated artifacts on GitHub |
| **Acceptance Criteria** | - Artifact posted with title<br>- Content in collapsible details block<br>- File path included for reference |

### REQ-GH-007: State Posting
| Field | Value |
|-------|-------|
| **Title** | Post State Summary to Issues |
| **Description** | The `post_state_to_issue()` function SHALL post current ADWState data to GitHub issue as JSON in collapsible block with descriptive title. |
| **Rationale** | Provides transparency into workflow state |
| **Acceptance Criteria** | - State posted as formatted JSON<br>- In collapsible block<br>- Includes descriptive title |

---

## Worktree Management Requirements

### REQ-WT-001: Worktree Creation
| Field | Value |
|-------|-------|
| **Title** | Create Isolated Git Worktree |
| **Description** | The `create_worktree(adw_id, branch_name, logger)` function SHALL: (1) create directory under `trees/{adw_id}/`, (2) create git worktree via `git worktree add`, (3) checkout or create specified branch. It SHALL return worktree path and error message. |
| **Rationale** | Enables isolated parallel execution |
| **Acceptance Criteria** | - Directory created under trees/<br>- Git worktree properly linked<br>- Branch checked out or created |

### REQ-WT-002: Worktree Validation
| Field | Value |
|-------|-------|
| **Title** | Validate Worktree Exists |
| **Description** | The `validate_worktree(adw_id, state)` function SHALL verify: (1) worktree_path exists in state, (2) directory exists on filesystem, (3) is valid git worktree. It SHALL return (valid_bool, error_message). |
| **Rationale** | Ensures worktree is usable before operations |
| **Acceptance Criteria** | - Checks path in state<br>- Checks directory exists<br>- Checks git worktree validity |

### REQ-WT-003: Worktree Environment Setup
| Field | Value |
|-------|-------|
| **Title** | Setup Worktree Environment |
| **Description** | The `setup_worktree_environment(path, backend_port, frontend_port, logger)` function SHALL: (1) create `.ports.env` file with PORT_BACKEND and PORT_FRONTEND, (2) execute `/install_worktree` command to install dependencies with custom ports. |
| **Rationale** | Prepares worktree for isolated development |
| **Acceptance Criteria** | - .ports.env created with port assignments<br>- Dependencies installed<br>- Ports configured for services |

### REQ-WT-004: Worktree Cleanup
| Field | Value |
|-------|-------|
| **Title** | Remove Worktree |
| **Description** | The cleanup process SHALL: (1) remove git worktree reference via `git worktree remove`, (2) delete worktree directory, (3) optionally delete artifact directory. |
| **Rationale** | Enables resource cleanup |
| **Acceptance Criteria** | - Git worktree deregistered<br>- Directory removed<br>- No orphaned references |

---

## Port Allocation Requirements

### REQ-PORT-001: Deterministic Port Assignment
| Field | Value |
|-------|-------|
| **Title** | Hash-based Port Allocation |
| **Description** | The `get_ports_for_adw(adw_id)` function SHALL compute deterministic ports from ADW ID hash: `backend = backend_start + (hash % 15)`, `frontend = frontend_start + (hash % 15)`. Default ranges: backend 9100-9114, frontend 9200-9214. |
| **Rationale** | Enables reproducible port assignment for resumable workflows |
| **Acceptance Criteria** | - Same ADW ID always gets same ports<br>- Ports within configured range<br>- 15 possible port pairs |

### REQ-PORT-002: Port Availability Check
| Field | Value |
|-------|-------|
| **Title** | Check Port Availability |
| **Description** | The `is_port_available(port)` function SHALL check if port is free by attempting socket bind. Returns True if available, False if in use. |
| **Rationale** | Prevents port conflicts |
| **Acceptance Criteria** | - Returns True for free ports<br>- Returns False for bound ports<br>- Handles socket errors gracefully |

### REQ-PORT-003: Alternative Port Finding
| Field | Value |
|-------|-------|
| **Title** | Find Next Available Ports |
| **Description** | The `find_next_available_ports(adw_id)` function SHALL, if deterministic ports are unavailable, scan for next available pair within range. It SHALL return (backend_port, frontend_port). |
| **Rationale** | Handles port conflicts gracefully |
| **Acceptance Criteria** | - Scans ports in order<br>- Finds first available pair<br>- Raises error if no ports available |

---

## Slash Command Requirements

### REQ-CMD-001: Command Template Format
| Field | Value |
|-------|-------|
| **Title** | Markdown Command Templates |
| **Description** | Slash commands SHALL be markdown files with `.md` extension. They SHALL contain: description, instructions for agent, and `$ARGUMENTS` placeholder for runtime substitution. |
| **Rationale** | Enables readable, maintainable command definitions |
| **Acceptance Criteria** | - Files are valid markdown<br>- $ARGUMENTS placeholder present where needed<br>- Clear instructions for agent |

### REQ-CMD-002: Issue Classification Commands
| Field | Value |
|-------|-------|
| **Title** | Issue Type Classification |
| **Description** | The `/classify_and_branch` command SHALL analyze issue content and return: (1) issue type as SlashCommand (/feature, /bug, /chore), (2) suggested branch name. Output SHALL be structured JSON. |
| **Rationale** | Enables automated issue triage |
| **Acceptance Criteria** | - Returns valid SlashCommand<br>- Returns valid branch name<br>- JSON output parseable |

### REQ-CMD-003: Planning Commands
| Field | Value |
|-------|-------|
| **Title** | Implementation Planning Commands |
| **Description** | The `/feature`, `/bug`, and `/chore` commands SHALL generate implementation plans for their respective issue types. Plans SHALL be markdown files saved to `specs/` directory. |
| **Rationale** | Enables type-specific planning strategies |
| **Acceptance Criteria** | - Plan file created in specs/<br>- Plan includes implementation steps<br>- Plan references issue requirements |

### REQ-CMD-004: Implementation Command
| Field | Value |
|-------|-------|
| **Title** | Implementation Execution |
| **Description** | The `/implement` command SHALL accept plan file path and execute the implementation according to plan. It SHALL modify source files, create new files as needed. |
| **Rationale** | Enables automated code implementation |
| **Acceptance Criteria** | - Reads and follows plan<br>- Creates/modifies files<br>- Reports implementation summary |

### REQ-CMD-005: Test Commands
| Field | Value |
|-------|-------|
| **Title** | Test Execution Commands |
| **Description** | The `/test` command SHALL run unit tests. The `/test_e2e` command SHALL run end-to-end tests. The `/resolve_failed_test` and `/resolve_failed_e2e_test` commands SHALL analyze failures and implement fixes. |
| **Rationale** | Enables automated testing with self-healing |
| **Acceptance Criteria** | - Tests executed correctly<br>- Failures captured and reported<br>- Resolution attempts fix issues |

### REQ-CMD-006: Review Command
| Field | Value |
|-------|-------|
| **Title** | Implementation Review |
| **Description** | The `/review` command SHALL compare implementation against original issue requirements. It SHALL identify blockers and suggestions. Output SHALL be structured ReviewResult. |
| **Rationale** | Enables automated code review |
| **Acceptance Criteria** | - Reviews against original spec<br>- Identifies blocker issues<br>- Provides actionable feedback |

### REQ-CMD-007: Documentation Command
| Field | Value |
|-------|-------|
| **Title** | Feature Documentation |
| **Description** | The `/document` command SHALL generate documentation for implemented features. Documentation SHALL be markdown in appropriate location. |
| **Rationale** | Ensures features are documented |
| **Acceptance Criteria** | - Documentation generated<br>- Placed in correct location<br>- Covers implemented functionality |

### REQ-CMD-008: Git Operation Commands
| Field | Value |
|-------|-------|
| **Title** | Git Commit and PR Commands |
| **Description** | The `/commit` command SHALL generate commit message. The `/pull_request` command SHALL create or update PR with appropriate title and body. |
| **Rationale** | Enables automated git operations |
| **Acceptance Criteria** | - Commit messages follow conventions<br>- PR created with correct details<br>- References issue appropriately |

### REQ-CMD-009: Worktree Commands
| Field | Value |
|-------|-------|
| **Title** | Worktree Management Commands |
| **Description** | The `/install_worktree` command SHALL install dependencies and configure services for isolated worktree. The `/cleanup_worktrees` command SHALL remove specified worktrees. |
| **Rationale** | Enables worktree lifecycle management |
| **Acceptance Criteria** | - Dependencies installed<br>- Ports configured<br>- Cleanup removes all artifacts |

### REQ-CMD-010: SlashCommand Type Safety
| Field | Value |
|-------|-------|
| **Title** | SlashCommand Literal Type |
| **Description** | The SlashCommand type SHALL be a Literal type with all valid command names: "/feature", "/bug", "/chore", "/implement", "/patch", "/review", "/document", "/test", "/test_e2e", "/resolve_failed_test", "/resolve_failed_e2e_test", "/commit", "/pull_request", "/classify_issue", "/generate_branch_name", "/classify_and_branch", "/install_worktree", "/cleanup_worktrees", "/resolve_review_blocker". |
| **Rationale** | Enables compile-time validation of command names |
| **Acceptance Criteria** | - All valid commands in Literal<br>- Type checking catches invalid commands<br>- IDE autocomplete works |

---

## Artifact Management Requirements

### REQ-ART-001: Artifact Directory Structure
| Field | Value |
|-------|-------|
| **Title** | Hierarchical Artifact Organization |
| **Description** | Artifacts SHALL be stored under: `{artifacts_dir}/{project_id}/{adw_id}/`. Subdirectories SHALL include: `{agent_name}/prompts/`, `{agent_name}/raw_output.jsonl`, `adw_state.json`. |
| **Rationale** | Enables organized artifact storage and retrieval |
| **Acceptance Criteria** | - Directory structure created on demand<br>- Agent-specific subdirectories<br>- State file at root of ADW ID directory |

### REQ-ART-002: Worktree Location
| Field | Value |
|-------|-------|
| **Title** | Worktree Storage Location |
| **Description** | Git worktrees SHALL be stored under: `{artifacts_dir}/{project_id}/trees/{adw_id}/`. This is separate from the main artifact storage to allow easier cleanup. |
| **Rationale** | Separates working code from logs/artifacts |
| **Acceptance Criteria** | - Worktrees in trees/ subdirectory<br>- ADW ID identifies worktree<br>- Can be cleaned independently |

### REQ-ART-003: Plan File Location
| Field | Value |
|-------|-------|
| **Title** | Implementation Plan Storage |
| **Description** | Implementation plans SHALL be stored in worktree at: `specs/issue-{number}-adw-{adw_id}-{description}.md`. Path SHALL be stored in state as `plan_file`. |
| **Rationale** | Plans tracked with issue and ADW ID |
| **Acceptance Criteria** | - Plan in specs/ directory<br>- Filename includes identifiers<br>- Path stored in state |

### REQ-ART-004: Screenshot Storage
| Field | Value |
|-------|-------|
| **Title** | Screenshot Upload to R2 |
| **Description** | Review screenshots SHALL be uploaded to Cloudflare R2 storage. URLs SHALL be included in review comments and PR body. |
| **Rationale** | Enables visual review verification |
| **Acceptance Criteria** | - Screenshots captured during review<br>- Uploaded to R2<br>- URLs accessible in PR |

---

## Logging & Observability Requirements

### REQ-LOG-001: Dual Logger Setup
| Field | Value |
|-------|-------|
| **Title** | File and Console Logging |
| **Description** | The `setup_logger(adw_id, workflow_name)` function SHALL create logger with: (1) file handler writing to `logs/{adw_id}/{workflow_name}.log`, (2) console handler with Rich formatting. Log level SHALL be DEBUG for file, INFO for console. |
| **Rationale** | Enables comprehensive logging with clean console output |
| **Acceptance Criteria** | - File logging at DEBUG level<br>- Console logging at INFO level<br>- Rich formatting for console<br>- Separate log files per workflow |

### REQ-LOG-002: GitHub Issue Updates
| Field | Value |
|-------|-------|
| **Title** | Progress Updates on GitHub |
| **Description** | Each significant workflow step SHALL post a comment to the GitHub issue with: ADW ID prefix, agent name, status emoji, and description. This provides visibility into workflow progress. |
| **Rationale** | Enables real-time monitoring via GitHub |
| **Acceptance Criteria** | - Comments posted at each phase<br>- ADW ID included for correlation<br>- Status clearly indicated |

### REQ-LOG-003: Terminal Output Formatting
| Field | Value |
|-------|-------|
| **Title** | Rich Terminal Output |
| **Description** | The system SHALL use Rich library for terminal output with: `print_markdown()` for formatted markdown, `print_artifact()` for artifacts with panels, `print_report()` for structured reports. Controlled by `PRINT_TERMINAL_*` flags. |
| **Rationale** | Provides readable terminal output |
| **Acceptance Criteria** | - Markdown rendered properly<br>- Artifacts in bordered panels<br>- Can be disabled via config |

---

## Error Handling Requirements

### REQ-ERR-001: RetryCode Enum
| Field | Value |
|-------|-------|
| **Title** | Standardized Retry Codes |
| **Description** | The RetryCode enum SHALL define: SUCCESS, RETRY_REQUESTED, MAX_RETRIES_EXCEEDED, UNRECOVERABLE_ERROR. These codes control workflow retry logic. |
| **Rationale** | Standardizes retry behavior across workflows |
| **Acceptance Criteria** | - All codes defined<br>- Used consistently in workflows<br>- Controls retry loops |

### REQ-ERR-002: Test Resolution Loop
| Field | Value |
|-------|-------|
| **Title** | Automatic Test Failure Resolution |
| **Description** | When tests fail, the system SHALL: (1) parse test output, (2) call `/resolve_failed_test` up to MAX_TEST_RETRY_ATTEMPTS (4), (3) re-run tests, (4) repeat until success or max attempts. E2E tests use MAX_E2E_TEST_RETRY_ATTEMPTS (2). |
| **Rationale** | Enables self-healing test failures |
| **Acceptance Criteria** | - Failures trigger resolution<br>- Max attempts respected<br>- Success breaks loop |

### REQ-ERR-003: Review Resolution Loop
| Field | Value |
|-------|-------|
| **Title** | Automatic Review Blocker Resolution |
| **Description** | When review identifies blockers, the system SHALL: (1) parse blocker issues, (2) call `/resolve_review_blocker` up to MAX_REVIEW_RETRY_ATTEMPTS (3), (3) re-run review, (4) repeat until no blockers or max attempts. |
| **Rationale** | Enables self-healing review blockers |
| **Acceptance Criteria** | - Blockers trigger resolution<br>- Max attempts respected<br>- No blockers breaks loop |

### REQ-ERR-004: Workflow Exit Codes
| Field | Value |
|-------|-------|
| **Title** | Proper Exit Code Handling |
| **Description** | Workflows SHALL exit with: 0 on success, 1 on failure. Subprocess calls SHALL check returncode and propagate failures appropriately. |
| **Rationale** | Enables proper workflow chaining and error detection |
| **Acceptance Criteria** | - Exit 0 on success<br>- Exit 1 on failure<br>- Parent processes detect failures |

---

## Security Requirements

### REQ-SEC-001: API Key Management
| Field | Value |
|-------|-------|
| **Title** | Secure API Key Storage |
| **Description** | API keys (ANTHROPIC_API_KEY, GITHUB_PAT) SHALL be stored in `.env` file, never in source code. The `.env` file SHALL be in `.gitignore`. |
| **Rationale** | Prevents credential exposure |
| **Acceptance Criteria** | - Keys in .env file<br>- .env in .gitignore<br>- No keys in source |

### REQ-SEC-002: Subprocess Environment Filtering
| Field | Value |
|-------|-------|
| **Title** | Filtered Environment for Subprocesses |
| **Description** | Subprocesses (Claude CLI, git, gh) SHALL receive filtered environment via `get_safe_subprocess_env()`. Only explicitly allowlisted variables SHALL be passed. |
| **Rationale** | Prevents sensitive environment leakage |
| **Acceptance Criteria** | - Only allowlisted vars passed<br>- Sensitive vars excluded<br>- Required vars included |

### REQ-SEC-003: Worktree Isolation
| Field | Value |
|-------|-------|
| **Title** | Isolated Worktree Execution |
| **Description** | Each workflow SHALL execute in its own git worktree with unique port assignments. This prevents interference between concurrent workflows. |
| **Rationale** | Prevents cross-workflow interference |
| **Acceptance Criteria** | - Separate directories<br>- Unique ports<br>- No shared mutable state |

---

## Edge Cases and Error Behaviors

### EDGE-001: Missing Worktree for Build
| **Scenario** | build_iso called without prior plan_iso |
| **Expected Behavior** | Exit with error "Worktree validation failed" and suggestion to run plan first |
| **Implementation** | `validate_worktree()` returns False, workflow posts error comment and exits with code 1 |

### EDGE-002: Port Conflict
| **Scenario** | Deterministic ports for ADW ID already in use |
| **Expected Behavior** | Log warning, find next available ports within range |
| **Implementation** | `is_port_available()` returns False, `find_next_available_ports()` scans for alternatives |

### EDGE-003: Empty Test Output
| **Scenario** | Test command produces no output |
| **Expected Behavior** | Parse result as success (no failures reported) |
| **Implementation** | `parse_test_result()` handles empty output gracefully |

### EDGE-004: Max Retries Exceeded
| **Scenario** | Test resolution attempts exceed MAX_TEST_RETRY_ATTEMPTS |
| **Expected Behavior** | Log warning, continue to next phase, post summary noting failures |
| **Implementation** | Retry loop breaks, `RetryCode.MAX_RETRIES_EXCEEDED` returned, workflow continues with warning |

### EDGE-005: Missing Plan File
| **Scenario** | build_iso state has plan_file but file doesn't exist |
| **Expected Behavior** | Exit with error "Plan file does not exist" |
| **Implementation** | File existence check fails, error comment posted, exit code 1 |

### EDGE-006: Concurrent Same-Issue Workflows
| **Scenario** | Two SDLC workflows started for same issue with different ADW IDs |
| **Expected Behavior** | Both execute independently in separate worktrees |
| **Implementation** | Different ADW IDs = different worktrees, different ports, no conflict |

### EDGE-007: Git Remote Not Found
| **Scenario** | Project has no git remote configured |
| **Expected Behavior** | Exit with error during project_id detection |
| **Implementation** | `get_repo_url()` raises ValueError, workflow exits with error |

### EDGE-008: GitHub Auth Failed
| **Scenario** | gh CLI not authenticated |
| **Expected Behavior** | Exit with error on first gh command |
| **Implementation** | Subprocess returns non-zero, error propagated and logged |

---

## Configuration Requirements Summary

| Config Item | Location | Required | Default |
|-------------|----------|----------|---------|
| `ANTHROPIC_API_KEY` | `.env` | Yes | - |
| `GITHUB_PAT` | `.env` | No | Uses `gh auth` |
| `CLAUDE_CODE_PATH` | `.env` | No | `claude` |
| `project_id` | `.adw.yaml` | No | Auto-detected from git |
| `artifacts_dir` | `.adw.yaml` | No | `./artifacts` |
| `source_root` | `.adw.yaml` | No | `./src` |
| `ports.backend_start` | `.adw.yaml` | No | `9100` |
| `ports.frontend_start` | `.adw.yaml` | No | `9200` |
| `commands` | `.adw.yaml` | No | Framework + local |

---

*End of Requirements Specification*
