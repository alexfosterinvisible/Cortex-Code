# ADW Framework - Architecture & Design Specification (Claude)

**Version**: 1.0.0
**Date**: 2025-12-30
**Purpose**: Complete architecture and design decisions for rebuilding the ADW Framework from scratch

---

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Component Architecture](#component-architecture)
3. [Data Flow](#data-flow)
4. [State Machine & Transitions](#state-machine--transitions)
5. [Key Design Decisions](#key-design-decisions)
6. [Extension Mechanisms](#extension-mechanisms)
7. [Integration Patterns](#integration-patterns)
8. [Concurrency Model](#concurrency-model)
9. [Error Handling Strategy](#error-handling-strategy)
10. [Security Architecture](#security-architecture)

---

## High-Level Architecture

### System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL SYSTEMS                            │
├─────────────────┬─────────────────┬─────────────────┬───────────────────┤
│   GitHub API    │   Claude Code   │   Git CLI       │   Cloudflare R2   │
│   (via gh CLI)  │   (Agent)       │                 │   (Screenshots)   │
└────────┬────────┴────────┬────────┴────────┬────────┴─────────┬─────────┘
         │                 │                 │                   │
         ▼                 ▼                 ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         ADW FRAMEWORK                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                         CLI LAYER (Typer)                           ││
│  │  sdlc │ plan │ build │ test │ review │ document │ ship │ zte │ patch││
│  └───────────────────────────┬─────────────────────────────────────────┘│
│                              ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                     WORKFLOW ORCHESTRATION                          ││
│  │  plan_iso │ build_iso │ test_iso │ review_iso │ document_iso │ ...  ││
│  └───────────────────────────┬─────────────────────────────────────────┘│
│                              ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                         CORE LAYER                                  ││
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        ││
│  │  │ Config  │ │  State  │ │  Agent  │ │  Types  │ │  Utils  │        ││
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘        ││
│  └───────────────────────────┬─────────────────────────────────────────┘│
│                              ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                     INTEGRATIONS LAYER                              ││
│  │  ┌───────────┐ ┌───────────┐ ┌───────────────┐ ┌───────────────────┐││
│  │  │  GitHub   │ │  Git Ops  │ │  Worktree Ops │ │   Workflow Ops    │││
│  │  └───────────┘ └───────────┘ └───────────────┘ └───────────────────┘││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                     COMMANDS LAYER                                  ││
│  │  /feature │ /bug │ /chore │ /implement │ /test │ /review │ ...      ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
         │                                                       │
         ▼                                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          FILE SYSTEM                                     │
├─────────────────────────────────────────────────────────────────────────┤
│  artifacts/{project_id}/{adw_id}/   │  trees/{adw_id}/                  │
│    ├── adw_state.json               │    └── <git worktree>             │
│    ├── {agent}/prompts/             │                                   │
│    └── {agent}/raw_output.jsonl     │                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Package Structure

```
adw/
├── __init__.py              # Package initialization, version export
├── cli.py                   # Entry point - routes CLI commands to workflows
│
├── core/                    # Core framework machinery
│   ├── __init__.py
│   ├── config.py            # ADWConfig - loads .adw.yaml, manages paths
│   ├── state.py             # ADWState - persistent JSON state per workflow
│   ├── agent.py             # Claude Code execution - prompts, retry logic
│   ├── data_types.py        # Pydantic models, Literals, enums
│   └── utils.py             # Logging, env vars, ID generation
│
├── integrations/            # External system integrations
│   ├── __init__.py
│   ├── github.py            # GitHub API via gh CLI
│   ├── git_ops.py           # Git operations (commits, branches)
│   ├── workflow_ops.py      # Shared ADW operations (classify, plan, build)
│   └── worktree_ops.py      # Git worktree and port management
│
├── workflows/               # Workflow implementations
│   ├── __init__.py
│   ├── wt/                  # Worktree-isolated workflows (primary)
│   │   ├── __init__.py
│   │   ├── plan_iso.py      # Planning phase
│   │   ├── build_iso.py     # Implementation phase
│   │   ├── test_iso.py      # Testing phase
│   │   ├── review_iso.py    # Review phase
│   │   ├── document_iso.py  # Documentation phase
│   │   ├── ship_iso.py      # Merge phase
│   │   ├── patch_iso.py     # Lightweight patch
│   │   └── sdlc_iso.py      # Complete SDLC chain
│   │
│   └── reg/                 # Regular workflows (deprecated)
│       └── ...
│
├── triggers/                # External trigger mechanisms
│   ├── __init__.py
│   ├── trigger_webhook.py   # FastAPI webhook for GitHub events
│   └── trigger_cron.py      # Polling-based trigger
│
commands/                    # Slash command templates (separate from adw/)
├── feature.md
├── bug.md
├── chore.md
├── implement.md
├── test.md
├── test_e2e.md
├── review.md
├── document.md
├── classify_and_branch.md
├── resolve_failed_test.md
├── resolve_failed_e2e_test.md
├── resolve_review_blocker.md
├── install_worktree.md
├── cleanup_worktrees.md
├── commit.md
└── pull_request.md
```

---

## Component Architecture

### Core Components

#### 1. ADWConfig (Singleton)

```
┌─────────────────────────────────────────────────────────────┐
│                        ADWConfig                             │
├─────────────────────────────────────────────────────────────┤
│ Responsibilities:                                            │
│ - Load and parse .adw.yaml configuration                    │
│ - Resolve paths (artifacts, source, commands)               │
│ - Auto-detect project_id from git remote                    │
│ - Provide singleton access to config values                 │
├─────────────────────────────────────────────────────────────┤
│ Properties:                                                  │
│ - project_id: str (org/repo format)                         │
│ - artifacts_dir: Path (resolved absolute)                   │
│ - source_root: Path (resolved absolute)                     │
│ - ports: PortConfig (backend_start, frontend_start)         │
│ - command_dirs: list[Path]                                  │
│ - project_root: Path                                        │
├─────────────────────────────────────────────────────────────┤
│ Methods:                                                     │
│ - get_artifact_dir(adw_id) -> Path                          │
│ - get_worktree_dir(adw_id) -> Path                          │
│ - resolve_command(name) -> Path | None                      │
└─────────────────────────────────────────────────────────────┘
```

**Design Rationale**: Singleton pattern ensures consistent configuration across all components. Lazy loading enables testing without full initialization.

#### 2. ADWState (Instance per ADW ID)

```
┌─────────────────────────────────────────────────────────────┐
│                         ADWState                             │
├─────────────────────────────────────────────────────────────┤
│ Responsibilities:                                            │
│ - Persist workflow state to JSON file                       │
│ - Provide typed access to state fields                      │
│ - Track workflow execution history                          │
│ - Enable workflow resumption                                │
├─────────────────────────────────────────────────────────────┤
│ Data (ADWStateData model):                                   │
│ - adw_id: str                                               │
│ - issue_number: str | None                                  │
│ - branch_name: str | None                                   │
│ - plan_file: str | None                                     │
│ - issue_class: SlashCommand | None                          │
│ - worktree_path: str | None                                 │
│ - backend_port: int | None                                  │
│ - frontend_port: int | None                                 │
│ - model_set: "base" | "heavy" | None                        │
│ - all_adws: list[str] (execution history)                   │
├─────────────────────────────────────────────────────────────┤
│ Methods:                                                     │
│ - load(adw_id, logger) -> ADWState | None  [classmethod]    │
│ - save(caller: str) -> None                                 │
│ - update(**kwargs) -> None                                  │
│ - get(key, default=None) -> Any                             │
│ - append_adw_id(workflow_name) -> None                      │
└─────────────────────────────────────────────────────────────┘
```

**Design Rationale**: Instance-based (not singleton) to support multiple concurrent workflows. JSON format enables easy debugging and manual intervention.

#### 3. Agent Execution (execute_template)

```
┌─────────────────────────────────────────────────────────────┐
│                     execute_template                         │
├─────────────────────────────────────────────────────────────┤
│ Input: AgentTemplateRequest                                  │
│   - agent_name: str                                         │
│   - slash_command: SlashCommand                             │
│   - args: list[str]                                         │
│   - adw_id: str                                             │
│   - working_dir: Path | None                                │
├─────────────────────────────────────────────────────────────┤
│ Process:                                                     │
│ 1. Load command template from command_dirs                  │
│ 2. Substitute $ARGUMENTS with args                          │
│ 3. Save prompt to artifacts                                 │
│ 4. Determine model (base/heavy) from command                │
│ 5. Build subprocess command:                                │
│    - claude --yes-to-all --model {model} --prompt {prompt}  │
│ 6. Execute with filtered environment                        │
│ 7. Capture stdout/stderr                                    │
│ 8. Save output to artifacts                                 │
├─────────────────────────────────────────────────────────────┤
│ Output: AgentTemplateResponse                                │
│   - success: bool                                           │
│   - output: str                                             │
│   - error: str | None                                       │
└─────────────────────────────────────────────────────────────┘
```

**Design Rationale**: Template-based execution enables customization without code changes. Model selection based on command type optimizes cost/capability trade-off.

### Integration Components

#### 4. GitHub Integration

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Integration                        │
├─────────────────────────────────────────────────────────────┤
│ Functions:                                                   │
│ - fetch_issue(number, repo) -> GitHubIssue                  │
│ - make_issue_comment(number, body) -> None                  │
│ - get_repo_url() -> str                                     │
│ - extract_repo_path(url) -> str (org/repo)                  │
│ - post_artifact_to_issue(...) -> None                       │
│ - post_state_to_issue(...) -> None                          │
├─────────────────────────────────────────────────────────────┤
│ Implementation:                                              │
│ - All operations via gh CLI subprocess                      │
│ - Uses gh auth for authentication (or GITHUB_PAT)           │
│ - JSON output parsing for structured data                   │
└─────────────────────────────────────────────────────────────┘
```

#### 5. Git Operations

```
┌─────────────────────────────────────────────────────────────┐
│                      Git Operations                          │
├─────────────────────────────────────────────────────────────┤
│ Functions:                                                   │
│ - commit_changes(message, cwd) -> (success, error)          │
│ - get_current_branch(cwd) -> str                            │
│ - finalize_git_operations(state, logger, cwd) -> None       │
│   - Pushes branch                                           │
│   - Creates/updates PR                                      │
├─────────────────────────────────────────────────────────────┤
│ Implementation:                                              │
│ - All operations via git CLI subprocess                     │
│ - Works in both main repo and worktrees                     │
│ - Uses cwd parameter for worktree context                   │
└─────────────────────────────────────────────────────────────┘
```

#### 6. Worktree Operations

```
┌─────────────────────────────────────────────────────────────┐
│                    Worktree Operations                       │
├─────────────────────────────────────────────────────────────┤
│ Creation & Validation:                                       │
│ - create_worktree(adw_id, branch, logger) -> (path, error)  │
│ - validate_worktree(adw_id, state) -> (valid, error)        │
├─────────────────────────────────────────────────────────────┤
│ Port Management:                                             │
│ - get_ports_for_adw(adw_id) -> (backend, frontend)          │
│ - is_port_available(port) -> bool                           │
│ - find_next_available_ports(adw_id) -> (backend, frontend)  │
├─────────────────────────────────────────────────────────────┤
│ Environment Setup:                                           │
│ - setup_worktree_environment(path, backend, frontend, log)  │
│   - Creates .ports.env                                      │
│   - Runs /install_worktree command                          │
└─────────────────────────────────────────────────────────────┘
```

#### 7. Workflow Operations

```
┌─────────────────────────────────────────────────────────────┐
│                    Workflow Operations                       │
├─────────────────────────────────────────────────────────────┤
│ ADW ID Management:                                           │
│ - ensure_adw_id(issue, adw_id, logger) -> str               │
│ - make_adw_id() -> str (8-char UUID)                        │
├─────────────────────────────────────────────────────────────┤
│ Issue Processing:                                            │
│ - classify_and_generate_branch(issue, adw_id, log)          │
│   -> (command, branch, error)                               │
│ - classify_issue(issue, adw_id, log) -> (command, error)    │
│ - generate_branch_name(issue, cmd, adw_id, log) -> (name, e)│
├─────────────────────────────────────────────────────────────┤
│ Plan/Build Operations:                                       │
│ - build_plan(issue, cmd, adw_id, log, wd) -> Response       │
│ - implement_plan(plan_file, adw_id, log, wd) -> Response    │
├─────────────────────────────────────────────────────────────┤
│ Git Integration:                                             │
│ - create_commit(agent, issue, cmd, adw_id, log, cwd)        │
│   -> (message, error)                                       │
├─────────────────────────────────────────────────────────────┤
│ GitHub Formatting:                                           │
│ - format_issue_message(adw_id, agent, msg) -> str           │
│ - post_artifact_to_issue(...) -> None                       │
│ - post_state_to_issue(...) -> None                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Complete SDLC Flow

```
                     ┌─────────────────┐
                     │  GitHub Issue   │
                     │    #42          │
                     └────────┬────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                           PLAN PHASE (plan_iso)                           │
├──────────────────────────────────────────────────────────────────────────┤
│ 1. ensure_adw_id() → "abc12345"                                          │
│ 2. fetch_issue(42) → GitHubIssue                                         │
│ 3. get_ports_for_adw("abc12345") → (9103, 9203)                          │
│ 4. classify_and_generate_branch(issue) → ("/feature", "feature-42-...")  │
│ 5. create_worktree("abc12345", branch) → "/trees/abc12345/"              │
│ 6. setup_worktree_environment(path, 9103, 9203)                          │
│ 7. execute_template(/feature, issue) → plan file path                    │
│ 8. commit_changes("plan: ...") in worktree                               │
│ 9. finalize_git_operations() → push + create PR                          │
├──────────────────────────────────────────────────────────────────────────┤
│ State After: {adw_id, issue_number, branch_name, plan_file, worktree_path}│
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          BUILD PHASE (build_iso)                          │
├──────────────────────────────────────────────────────────────────────────┤
│ 1. validate_worktree("abc12345") → True                                  │
│ 2. Load plan_file from state                                             │
│ 3. execute_template(/implement, plan_file) → implementation              │
│ 4. create_commit() → commit message                                      │
│ 5. commit_changes() in worktree                                          │
│ 6. finalize_git_operations() → push                                      │
├──────────────────────────────────────────────────────────────────────────┤
│ State After: implementation committed to PR                               │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          TEST PHASE (test_iso)                            │
├──────────────────────────────────────────────────────────────────────────┤
│ 1. validate_worktree() → True                                            │
│ 2. execute_template(/test) → TestResult                                  │
│ 3. If failures:                                                          │
│    Loop (max 4 times):                                                   │
│      a. execute_template(/resolve_failed_test, failures)                 │
│      b. commit_changes()                                                 │
│      c. execute_template(/test) → check if fixed                         │
│ 4. If --skip-e2e not set:                                                │
│    execute_template(/test_e2e) → E2ETestResult                           │
│    Same resolution loop (max 2 times)                                    │
│ 5. Post test summary to issue                                            │
├──────────────────────────────────────────────────────────────────────────┤
│ State After: tests pass (or warnings logged)                              │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         REVIEW PHASE (review_iso)                         │
├──────────────────────────────────────────────────────────────────────────┤
│ 1. validate_worktree() → True                                            │
│ 2. execute_template(/review, issue) → ReviewResult                       │
│ 3. Capture screenshots → upload to R2                                    │
│ 4. Parse blockers from ReviewResult                                      │
│ 5. If blockers and --skip-resolution not set:                            │
│    Loop (max 3 times):                                                   │
│      a. execute_template(/resolve_review_blocker, blocker)               │
│      b. commit_changes()                                                 │
│      c. execute_template(/review) → check if fixed                       │
│ 6. Update PR body with review summary + screenshots                      │
├──────────────────────────────────────────────────────────────────────────┤
│ State After: review complete, PR updated                                  │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                       DOCUMENT PHASE (document_iso)                       │
├──────────────────────────────────────────────────────────────────────────┤
│ 1. validate_worktree() → True                                            │
│ 2. execute_template(/document) → documentation                           │
│ 3. commit_changes()                                                      │
│ 4. finalize_git_operations() → push                                      │
├──────────────────────────────────────────────────────────────────────────┤
│ State After: documentation committed                                      │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │
                                   ▼
                     ┌─────────────────┐
                     │   PR Ready for  │
                     │     Merge       │
                     └─────────────────┘
```

### Agent Execution Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        execute_template() Flow                            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                  │
│  │ Load Template│    │ Substitute  │    │   Save      │                  │
│  │ from commands/│──▶│ $ARGUMENTS  │──▶│   Prompt    │                  │
│  └─────────────┘    └─────────────┘    └──────┬──────┘                  │
│                                                │                          │
│                                                ▼                          │
│                                       ┌─────────────┐                    │
│                                       │ Determine   │                    │
│                                       │ Model (base/│                    │
│                                       │   heavy)    │                    │
│                                       └──────┬──────┘                    │
│                                              │                            │
│                                              ▼                            │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                     Build Claude CLI Command                         ││
│  │  claude --yes-to-all --model {model} --prompt "{prompt}"             ││
│  │  Working Directory: {working_dir or cwd}                             ││
│  │  Environment: get_safe_subprocess_env()                              ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                              │                            │
│                                              ▼                            │
│                                       ┌─────────────┐                    │
│                                       │  Execute    │                    │
│                                       │  Subprocess │                    │
│                                       └──────┬──────┘                    │
│                                              │                            │
│                                              ▼                            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                  │
│  │ Capture     │    │   Save      │    │   Return    │                  │
│  │ stdout/err  │──▶│   Output    │──▶│ Response    │                  │
│  └─────────────┘    └─────────────┘    └─────────────┘                  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## State Machine & Transitions

### Workflow State Machine

```
                                ┌─────────────────┐
                                │    INITIAL      │
                                │  (No ADW ID)    │
                                └────────┬────────┘
                                         │ ensure_adw_id()
                                         ▼
                              ┌──────────────────────┐
                              │    INITIALIZED       │
                              │ {adw_id, issue_num}  │
                              └──────────┬───────────┘
                                         │ plan_iso
                                         ▼
        ┌────────────────────────────────────────────────────────┐
        │                        PLANNED                          │
        │ {adw_id, issue_number, branch_name, plan_file,          │
        │  worktree_path, backend_port, frontend_port}            │
        └─────────────────────────┬──────────────────────────────┘
                                  │ build_iso
                                  ▼
                       ┌──────────────────────┐
                       │       BUILT          │
                       │ (implementation      │
                       │  committed)          │
                       └──────────┬───────────┘
                                  │ test_iso
                                  ▼
                       ┌──────────────────────┐
                       │       TESTED         │
                       │ (tests passed or     │
                       │  warnings noted)     │
                       └──────────┬───────────┘
                                  │ review_iso
                                  ▼
                       ┌──────────────────────┐
                       │      REVIEWED        │
                       │ (review complete,    │
                       │  PR updated)         │
                       └──────────┬───────────┘
                                  │ document_iso
                                  ▼
                       ┌──────────────────────┐
                       │     DOCUMENTED       │
                       │ (docs committed)     │
                       └──────────┬───────────┘
                                  │ ship_iso
                                  ▼
                       ┌──────────────────────┐
                       │       SHIPPED        │
                       │ (PR merged)          │
                       └──────────────────────┘
```

### Test Resolution State Machine

```
                          ┌─────────────┐
                          │  RUN TESTS  │
                          └──────┬──────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
             ┌────────────┐           ┌────────────┐
             │   PASSED   │           │   FAILED   │
             └────────────┘           └──────┬─────┘
                                             │
                                             ▼
                                    ┌────────────────┐
                                    │ attempts < MAX?│
                                    └───────┬────────┘
                                   yes│          │no
                                      ▼          ▼
                              ┌────────────┐  ┌────────────────┐
                              │  RESOLVE   │  │ MAX_RETRIES_   │
                              │  FAILURE   │  │ EXCEEDED       │
                              └──────┬─────┘  └────────────────┘
                                     │              │
                                     │              │ (continue with
                                     │              │  warning)
                                     │              ▼
                                     │        ┌────────────┐
                                     │        │  CONTINUE  │
                                     │        └────────────┘
                                     │
                                     │ commit fix
                                     ▼
                              ┌────────────┐
                              │ RUN TESTS  │ ◀─────┐
                              └──────┬─────┘       │
                                     │             │
                                     └─────────────┘
                                      (loop back)
```

---

## Key Design Decisions

### DD-001: Git Worktree Isolation

**Decision**: Use git worktrees for parallel, isolated workflow execution.

**Context**: Multiple workflows may run concurrently on the same repository. Each workflow modifies files and needs its own branch.

**Alternatives Considered**:
1. Single working directory with branch switching (rejected: race conditions)
2. Clone repository for each workflow (rejected: expensive, slow)
3. Docker containers (rejected: complexity, not needed for file-level isolation)

**Consequences**:
- (+) True parallel execution without interference
- (+) Lightweight compared to full clones
- (+) Native git integration (shared refs)
- (-) Requires git version with worktree support
- (-) Additional cleanup needed

### DD-002: Deterministic Port Allocation

**Decision**: Compute ports deterministically from ADW ID hash.

**Context**: Each isolated workflow may run services (backend, frontend) that need unique ports.

**Formula**:
```python
backend = backend_start + (hash(adw_id) % 15)  # 9100-9114
frontend = frontend_start + (hash(adw_id) % 15)  # 9200-9214
```

**Alternatives Considered**:
1. Random port allocation (rejected: not reproducible for resumption)
2. Port registry file (rejected: synchronization issues)
3. Dynamic port finding each time (rejected: not resumable)

**Consequences**:
- (+) Resumable workflows get same ports
- (+) No external coordination needed
- (+) Simple implementation
- (-) Collision possible if 15+ concurrent workflows
- (-) Must check availability and fallback

### DD-003: Subprocess-Based Claude Execution

**Decision**: Execute Claude Code via subprocess calls to `claude` CLI.

**Context**: Need to invoke Claude Code agent for planning, implementation, review.

**Alternatives Considered**:
1. API integration (rejected: Claude Code is CLI-only)
2. Python SDK (rejected: doesn't exist for Claude Code)
3. Screen automation (rejected: fragile, slow)

**Consequences**:
- (+) Works with existing Claude Code CLI
- (+) Captures stdout/stderr naturally
- (+) No SDK dependencies
- (-) Process spawning overhead
- (-) Error handling via exit codes only

### DD-004: Template-Based Commands

**Decision**: Commands are markdown templates with `$ARGUMENTS` substitution.

**Context**: Agents need detailed instructions that may evolve independently of code.

**Alternatives Considered**:
1. Hardcoded prompts in Python (rejected: hard to modify)
2. YAML configuration (rejected: less readable for prompts)
3. Database-stored prompts (rejected: overkill, deployment complexity)

**Consequences**:
- (+) Easy to modify without code changes
- (+) Version controlled with repository
- (+) Readable markdown format
- (+) Multiple command directories supported
- (-) No parameterized validation
- (-) Template loading on each execution

### DD-005: Model Selection by Command Type

**Decision**: Use "heavy" (Opus) for complex tasks, "base" (Sonnet) for simple tasks.

**Heavy commands**: `/implement`, `/document`, `/feature`, `/bug`, `/chore`, `/patch`
**Base commands**: All others

**Context**: Balance cost vs. capability for different task complexities.

**Alternatives Considered**:
1. Single model for all (rejected: wasteful or underpowered)
2. User-specified per call (rejected: user burden)
3. Automatic complexity detection (rejected: unpredictable)

**Consequences**:
- (+) Optimized cost/capability trade-off
- (+) Predictable model selection
- (+) Simple implementation
- (-) Not task-adaptive within command type
- (-) Manual maintenance of heavy command list

### DD-006: JSON State Persistence

**Decision**: Store workflow state as JSON file.

**Context**: State must persist across process restarts and be shared across workflow phases.

**Alternatives Considered**:
1. Database (rejected: deployment complexity)
2. Environment variables (rejected: size limits, not persistent)
3. YAML (rejected: no strong advantage over JSON)
4. Pickle (rejected: not human-readable, security concerns)

**Consequences**:
- (+) Human-readable for debugging
- (+) Standard format, wide support
- (+) Easy manual intervention
- (+) No external dependencies
- (-) No concurrent write protection (acceptable for single-workflow)
- (-) No query capability

### DD-007: GitHub Issue as Progress Dashboard

**Decision**: Post workflow progress and artifacts as issue comments.

**Context**: Users need visibility into automated workflow execution.

**Alternatives Considered**:
1. Dedicated dashboard (rejected: requires hosting)
2. Slack/Discord notifications (rejected: requires integration)
3. Log files only (rejected: poor discoverability)

**Consequences**:
- (+) Native GitHub experience
- (+) Tied to issue context
- (+) No additional infrastructure
- (+) Accessible to all issue followers
- (-) Can create many comments
- (-) Limited formatting options

### DD-008: Resolution Loops with Max Retries

**Decision**: Auto-retry failed tests/reviews with resolution attempts, capped by max retries.

**Test**: MAX_TEST_RETRY_ATTEMPTS = 4
**E2E Test**: MAX_E2E_TEST_RETRY_ATTEMPTS = 2
**Review**: MAX_REVIEW_RETRY_ATTEMPTS = 3

**Context**: Automated development may produce failures that are fixable by the agent.

**Alternatives Considered**:
1. No auto-retry (rejected: leaves fixable issues)
2. Infinite retry (rejected: may never terminate)
3. Adaptive retry based on error type (rejected: complexity)

**Consequences**:
- (+) Self-healing for many issues
- (+) Guaranteed termination
- (+) Reasonable defaults based on experience
- (-) May waste attempts on unfixable issues
- (-) Fixed limits may be suboptimal for some cases

---

## Extension Mechanisms

### 1. Custom Command Templates

**Mechanism**: Add command files to project-local `.claude/commands/` or specify additional directories in `.adw.yaml`.

**Resolution Order**:
1. Project-local `.claude/commands/`
2. Config-specified directories
3. Framework `${ADW_FRAMEWORK}/commands`

**Later directories can override earlier ones** (project overrides framework).

### 2. Custom Workflows

**Mechanism**: Create new workflow modules following the pattern in `adw/workflows/wt/`.

**Required Elements**:
- `main()` function as entry point
- Load/validate state
- Use `execute_template()` for agent calls
- Update state appropriately
- Handle errors and post to GitHub

### 3. External Triggers

**Mechanism**: Use `trigger_webhook.py` (FastAPI) or `trigger_cron.py` (polling) as templates.

**Webhook Integration**:
- GitHub webhook posts to `/webhook` endpoint
- Parse event type and payload
- Map to appropriate workflow
- Execute via subprocess

**Cron Integration**:
- Poll GitHub for new issues with specific labels
- Map label to workflow
- Execute via subprocess

### 4. Configuration Extensions

**Mechanism**: Add fields to `.adw.yaml` parsed by custom code.

**Pattern**:
1. Extend config schema in `config.py`
2. Access via `ADWConfig` singleton
3. Use in workflows/integrations

---

## Integration Patterns

### CLI Subprocess Pattern

All external tool integrations use subprocess pattern:

```python
def run_external_tool(cmd: list[str], cwd: Path = None) -> tuple[bool, str]:
    """
    Pattern for external tool execution.
    """
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        env=get_safe_subprocess_env()  # Filtered environment
    )

    if result.returncode != 0:
        return False, result.stderr

    return True, result.stdout
```

**Applied To**: `git`, `gh`, `claude`

### Agent Call Pattern

All agent invocations use template pattern:

```python
def call_agent(slash_command: SlashCommand, args: list[str], adw_id: str,
               working_dir: Path = None) -> AgentTemplateResponse:
    """
    Pattern for agent invocation.
    """
    request = AgentTemplateRequest(
        agent_name="ops",  # or specific agent
        slash_command=slash_command,
        args=args,
        adw_id=adw_id,
        working_dir=working_dir,
    )

    response = execute_template(request)

    if not response.success:
        # Handle error
        pass

    return response
```

### GitHub Progress Pattern

All workflows post progress to issues:

```python
def workflow_step(issue_number: str, adw_id: str, step_name: str):
    """
    Pattern for workflow step with progress posting.
    """
    # Before step
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "agent", f"Starting {step_name}")
    )

    # Execute step
    result = do_step()

    # After step
    if result.success:
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "agent", f"Completed {step_name}")
        )
    else:
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "agent", f"Failed {step_name}: {result.error}")
        )
```

---

## Concurrency Model

### Single-Workflow Execution

Within a single ADW ID, execution is **strictly sequential**:

```
plan_iso → build_iso → test_iso → review_iso → document_iso
    ↓          ↓           ↓           ↓             ↓
 (state)   (state)     (state)     (state)       (state)
```

Each phase updates state and passes to next.

### Multi-Workflow Parallelism

Different ADW IDs can execute **fully in parallel**:

```
Issue #42 (adw: abc12345)         Issue #43 (adw: def67890)
├── trees/abc12345/               ├── trees/def67890/
├── ports: 9103, 9203             ├── ports: 9107, 9207
└── state: artifacts/.../abc12345 └── state: artifacts/.../def67890
```

**No coordination needed** - each workflow has:
- Own worktree directory
- Own port allocation
- Own state file
- Own artifact directory

### Subprocess Isolation

Each agent call is isolated subprocess:

```
┌──────────────────────────────────────────────────────────────┐
│ ADW Process                                                   │
│   ├── subprocess: claude --prompt "..."                      │
│   │     └── (isolated execution)                             │
│   ├── subprocess: git commit ...                             │
│   │     └── (isolated execution)                             │
│   └── subprocess: gh pr create ...                           │
│         └── (isolated execution)                             │
└──────────────────────────────────────────────────────────────┘
```

---

## Error Handling Strategy

### Layer-Based Error Handling

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLI Layer                                      │
│  - Catches all unhandled exceptions                                     │
│  - Displays user-friendly error message                                 │
│  - Returns appropriate exit code (0/1)                                  │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────┐
│                         Workflow Layer                                   │
│  - Logs errors with context                                             │
│  - Posts error to GitHub issue                                          │
│  - Calls sys.exit(1) on failure                                         │
│  - Saves state before exiting                                           │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────┐
│                       Integration Layer                                  │
│  - Returns (success, error) tuples                                      │
│  - Does NOT exit or raise (usually)                                     │
│  - Logs errors for debugging                                            │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────┐
│                          Core Layer                                      │
│  - Raises exceptions for programming errors                             │
│  - Returns None for "not found" cases                                   │
│  - Uses Pydantic for validation errors                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### RetryCode Enum

```python
class RetryCode(Enum):
    SUCCESS = "success"
    RETRY_REQUESTED = "retry_requested"
    MAX_RETRIES_EXCEEDED = "max_retries_exceeded"
    UNRECOVERABLE_ERROR = "unrecoverable_error"
```

Used in test/review resolution loops to control flow.

### Error Response Pattern

Functions that may fail return tuple:

```python
def operation() -> tuple[ResultType | None, str | None]:
    """
    Returns (result, error).
    - (result, None) on success
    - (None, "error message") on failure
    """
```

---

## Security Architecture

### Credential Management

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Credential Storage                                │
├─────────────────────────────────────────────────────────────────────────┤
│ .env file (gitignored)                                                  │
│   ANTHROPIC_API_KEY=sk-ant-xxx                                          │
│   GITHUB_PAT=ghp_xxx (optional, uses gh auth otherwise)                 │
│   CLAUDE_CODE_PATH=/path/to/claude                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Environment Loading                                 │
├─────────────────────────────────────────────────────────────────────────┤
│ load_dotenv() at workflow entry                                         │
│ Credentials available via os.environ                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Subprocess Environment                                │
├─────────────────────────────────────────────────────────────────────────┤
│ get_safe_subprocess_env() filters to allowlist:                         │
│   PATH, HOME, USER, SHELL, LANG, LC_*, TERM                             │
│   ANTHROPIC_API_KEY, GITHUB_PAT                                         │
│   CLAUDE_*, ADW_*, PORT_*                                               │
└─────────────────────────────────────────────────────────────────────────┘
```

### Isolation Boundaries

```
┌───────────────────────────────────────────────────────────────────────┐
│                       Isolation Layers                                 │
├───────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  1. Process Isolation                                                  │
│     └── Each Claude agent runs as separate subprocess                  │
│         └── Cannot access parent process memory                        │
│                                                                        │
│  2. Filesystem Isolation                                               │
│     └── Each workflow has own worktree                                 │
│         └── Separate directory tree                                    │
│         └── Own .ports.env                                             │
│                                                                        │
│  3. Network Isolation (Port-level)                                     │
│     └── Each workflow has unique port allocation                       │
│         └── Services don't conflict                                    │
│                                                                        │
│  4. State Isolation                                                    │
│     └── Each ADW ID has own state file                                 │
│         └── No shared mutable state                                    │
│                                                                        │
└───────────────────────────────────────────────────────────────────────┘
```

### Security Boundaries Not Provided

**Note**: ADW does NOT provide:
- Container isolation (agent can access filesystem)
- Network isolation (agent can make network calls)
- Resource limits (agent can consume CPU/memory)
- Sandboxing (relies on Claude Code's built-in safety)

These are intentional - the agent needs file access to do its job.

---

*End of Design Specification*
