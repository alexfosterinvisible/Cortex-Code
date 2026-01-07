# CxC Framework Design Specification (Claude)

**Version:** 1.0.0
**Date:** 2025-12-30
**Status:** Complete

---

## 1. Executive Summary

This document defines the system architecture and design for the CxC (Cortex Code) Framework. CxC is an orchestration system that automates software development lifecycle using Claude Code agents executing in isolated git worktrees.

---

## 2. Architecture Overview

### 2.1 High-Level System Architecture

```mermaid
graph TB
    subgraph Triggers
        CLI[CLI cxc command]
        WH[GitHub Webhook]
        CRON[Cron Poller]
    end

    subgraph Orchestration Layer
        ROUTER[Workflow Router]
        STATE[State Manager]
        CONFIG[Configuration Loader]
    end

    subgraph Workflow Engine
        PLAN[Plan Phase]
        BUILD[Build Phase]
        TEST[Test Phase]
        REVIEW[Review Phase]
        DOC[Document Phase]
        SHIP[Ship Phase]
    end

    subgraph Agent Layer
        AGENT[Agent Executor]
        TMPL[Template Loader]
        PROMPT[Prompt Builder]
    end

    subgraph Integration Layer
        GH[GitHub API via gh]
        GIT[Git Operations]
        WT[Worktree Manager]
        PORTS[Port Allocator]
    end

    subgraph External Systems
        GITHUB[(GitHub)]
        CLAUDE[Claude Code CLI]
        FS[(Filesystem)]
    end

    CLI --> ROUTER
    WH --> ROUTER
    CRON --> ROUTER

    ROUTER --> STATE
    ROUTER --> CONFIG
    ROUTER --> PLAN

    PLAN --> BUILD --> TEST --> REVIEW --> DOC --> SHIP

    PLAN --> AGENT
    BUILD --> AGENT
    TEST --> AGENT
    REVIEW --> AGENT
    DOC --> AGENT

    AGENT --> TMPL
    AGENT --> PROMPT
    AGENT --> CLAUDE

    PLAN --> GH
    PLAN --> GIT
    PLAN --> WT
    PLAN --> PORTS

    GH --> GITHUB
    GIT --> FS
    WT --> FS
    STATE --> FS
```

### 2.2 Component Diagram

```mermaid
graph LR
    subgraph cxc Package
        subgraph core
            A[config.py]
            B[state.py]
            C[agent.py]
            D[data_types.py]
            E[utils.py]
        end

        subgraph integrations
            F[github.py]
            G[git_ops.py]
            H[worktree_ops.py]
            I[workflow_ops.py]
        end

        subgraph workflows/wt
            J[plan_iso.py]
            K[build_iso.py]
            L[test_iso.py]
            M[review_iso.py]
            N[document_iso.py]
            O[ship_iso.py]
            P[sdlc_iso.py]
        end

        subgraph triggers
            Q[trigger_webhook.py]
            R[trigger_cron.py]
        end

        CLI_M[cli.py]
    end

    CLI_M --> J
    CLI_M --> P
    Q --> J
    Q --> P

    J --> A
    J --> B
    J --> C
    J --> F
    J --> G
    J --> H
    J --> I

    K --> B
    K --> C
    K --> I

    L --> B
    L --> C
    L --> I

    P --> J
    P --> K
    P --> L
    P --> M
    P --> N
```

---

## 3. Data Flow Diagrams

### 3.1 SDLC Pipeline Data Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant PlanISO
    participant BuildISO
    participant TestISO
    participant ReviewISO
    participant DocISO
    participant State
    participant Agent
    participant GitHub

    User->>CLI: cxc sdlc 42
    CLI->>State: ensure_cxc_id()
    State-->>CLI: cxc_id abc12345

    CLI->>PlanISO: run plan_iso
    PlanISO->>GitHub: fetch_issue(42)
    GitHub-->>PlanISO: GitHubIssue
    PlanISO->>Agent: classify_and_branch
    Agent-->>PlanISO: issue_class, branch_name
    PlanISO->>State: update(branch_name)
    PlanISO->>Agent: build_plan /feature
    Agent-->>PlanISO: plan_file path
    PlanISO->>State: update(plan_file)
    PlanISO->>GitHub: create_pr

    CLI->>BuildISO: run build_iso
    BuildISO->>State: load(cxc_id)
    State-->>BuildISO: plan_file
    BuildISO->>Agent: /implement plan
    Agent-->>BuildISO: implementation
    BuildISO->>GitHub: update_pr

    CLI->>TestISO: run test_iso
    TestISO->>State: load(cxc_id)
    TestISO->>Agent: /test
    Agent-->>TestISO: TestResult[]

    loop Until pass or max_retries
        TestISO->>Agent: /resolve_failed_test
        TestISO->>Agent: /test
    end

    CLI->>ReviewISO: run review_iso
    ReviewISO->>State: load(cxc_id)
    ReviewISO->>Agent: /review spec
    Agent-->>ReviewISO: ReviewResult

    CLI->>DocISO: run document_iso
    DocISO->>Agent: /document
    Agent-->>DocISO: doc_path

    CLI-->>User: SDLC Complete
```

### 3.2 Plan Phase Detail Flow

```mermaid
flowchart TD
    A[Start Plan Phase] --> B[Load Environment]
    B --> C{CxC ID Provided?}
    C -->|No| D[Generate CxC ID]
    C -->|Yes| E[Load Existing State]
    D --> F[Initialize State]
    E --> F

    F --> G[Fetch GitHub Issue]
    G --> H[Classify Issue and Generate Branch]
    H --> I[Update State with Classification]

    I --> J{Worktree Exists?}
    J -->|Yes| K[Validate Worktree]
    J -->|No| L[Allocate Ports]

    L --> M[Create Worktree]
    M --> N[Setup Environment]
    N --> O[Run /install_worktree]

    K --> P[Execute Planning Template]
    O --> P

    P --> Q{Plan Success?}
    Q -->|No| R[Error and Exit]
    Q -->|Yes| S[Save Plan File Path to State]

    S --> T[Commit Plan]
    T --> U[Push Branch]
    U --> V[Create/Update PR]
    V --> W[Post State to Issue]
    W --> X[End Plan Phase]
```

### 3.3 Test Resolution Loop

```mermaid
flowchart TD
    A[Start Test Phase] --> B[Load State]
    B --> C[Validate Worktree]
    C --> D[Initialize Attempt Counter]

    D --> E[Run /test Command]
    E --> F[Parse Test Results]

    F --> G{All Tests Passed?}
    G -->|Yes| H[Post Success Summary]
    G -->|No| I{Max Attempts Reached?}

    I -->|Yes| J[Post Failure Summary]
    I -->|No| K[Get Failed Tests]

    K --> L[For Each Failed Test]
    L --> M[Run /resolve_failed_test]
    M --> N{Resolution Success?}
    N -->|Yes| O[Increment Resolved]
    N -->|No| P[Increment Unresolved]

    O --> Q{More Failed Tests?}
    P --> Q
    Q -->|Yes| L
    Q -->|No| R{Any Resolved?}

    R -->|Yes| S[Increment Attempt]
    R -->|No| J
    S --> E

    H --> T[Run E2E Tests]
    J --> T

    T --> U[Commit Results]
    U --> V[End Test Phase]
```

---

## 4. Component Designs

### 4.1 Core Module Architecture

#### 4.1.1 Configuration System (cxc/core/config.py)

```mermaid
classDiagram
    class CxCConfig {
        +Path project_root
        +str project_id
        +Path artifacts_dir
        +PortConfig ports
        +Path source_root
        +List~Path~ commands
        +dict app_config
        +load() CxCConfig
        +get_agents_dir(cxc_id) Path
        +get_worktree_dir() Path
    }

    class PortConfig {
        +int backend_start
        +int backend_count
        +int frontend_start
        +int frontend_count
    }

    CxCConfig --> PortConfig
```

**Design Decisions:**
1. Configuration loaded from `.cxc.yaml` in project root
2. Fallback to framework defaults if not found
3. Immutable after load (dataclass)
4. Paths resolved relative to project root

#### 4.1.2 State Management (cxc/core/state.py)

```mermaid
classDiagram
    class CxCState {
        +str cxc_id
        +dict data
        +Logger logger
        +load(cxc_id) CxCState
        +save(caller_name)
        +update(**kwargs)
        +get(key, default)
        +append_cxc_id(workflow_name)
        -_get_state_path() Path
    }
```

**State Schema:**
```json
{
    "cxc_id": "abc12345",
    "issue_number": "42",
    "branch_name": "feat-issue-42-cxc-abc12345-add-auth",
    "plan_file": "specs/issue-42-cxc-abc12345-add-auth.md",
    "issue_class": "/feature",
    "worktree_path": "/path/to/trees/abc12345",
    "backend_port": 9100,
    "frontend_port": 9200,
    "model_set": "base",
    "cxc_workflow_history": ["cxc_plan_iso", "cxc_build_iso"]
}
```

**Design Decisions:**
1. JSON file persistence at `artifacts/{project_id}/{cxc_id}/cxc_state.json`
2. Automatic save on update for crash recovery
3. Caller tracking for debugging
4. Optional logger injection

#### 4.1.3 Agent Execution (cxc/core/agent.py)

```mermaid
classDiagram
    class AgentTemplateRequest {
        +str agent_name
        +SlashCommand slash_command
        +List~str~ args
        +str cxc_id
        +Optional~str~ working_dir
    }

    class AgentPromptResponse {
        +bool success
        +str output
        +Optional~str~ error
        +Optional~str~ session_id
        +Optional~int~ duration_ms
        +Optional~float~ cost_usd
    }

    class execute_template {
        <<function>>
        +execute_template(request) AgentPromptResponse
    }

    execute_template ..> AgentTemplateRequest
    execute_template ..> AgentPromptResponse
```

**Execution Flow:**
1. Load template from `commands/{slash_command}.md`
2. Substitute `$1`, `$2`, `$3` with positional args
3. Build Claude Code CLI command
4. Execute with `--output-format jsonl`
5. Parse JSONL for result extraction
6. Save prompt and output to artifacts

**Model Selection Logic:**
```python
HEAVY_COMMANDS = {"/implement", "/document", "/feature", "/bug", "/chore", "/patch"}
model = "opus" if slash_command in HEAVY_COMMANDS else "sonnet"
```

### 4.2 Integration Layer Architecture

#### 4.2.1 GitHub Integration (cxc/integrations/github.py)

```mermaid
classDiagram
    class GitHubIntegration {
        <<module>>
        +fetch_issue(number, repo) GitHubIssue
        +make_issue_comment(number, body)
        +create_pull_request(title, body, branch)
        +list_prs(branch) List~dict~
        +get_repo_url() str
        +extract_repo_path(url) str
    }
```

**Design Decisions:**
1. All operations via `gh` CLI (not direct API)
2. Authentication via `GITHUB_PAT` or `gh auth`
3. JSON output parsing via `--json` flag
4. Subprocess execution with safe environment

#### 4.2.2 Git Operations (cxc/integrations/git_ops.py)

```mermaid
classDiagram
    class GitOperations {
        <<module>>
        +create_branch(name, cwd) Tuple~bool, str~
        +commit_changes(message, cwd) Tuple~bool, str~
        +push_branch(branch, cwd) Tuple~bool, str~
        +get_current_branch(cwd) str
        +finalize_git_operations(state, logger, cwd)
    }
```

**Design Decisions:**
1. All operations support explicit `cwd` for worktree context
2. Return tuple of (success, error_message)
3. Use git CLI commands directly
4. No GitPython for subprocess isolation

#### 4.2.3 Worktree Management (cxc/integrations/worktree_ops.py)

```mermaid
classDiagram
    class WorktreeOperations {
        <<module>>
        +create_worktree(cxc_id, branch, logger) Tuple~str, str~
        +validate_worktree(cxc_id, state) Tuple~bool, str~
        +setup_worktree_environment(path, backend_port, frontend_port, logger)
        +get_ports_for_cxc(cxc_id) Tuple~int, int~
        +is_port_available(port) bool
        +find_next_available_ports(cxc_id) Tuple~int, int~
    }
```

**Port Allocation Algorithm:**
```python
def get_ports_for_cxc(cxc_id: str) -> Tuple[int, int]:
    # Deterministic hash-based allocation
    hash_val = int(hashlib.md5(cxc_id.encode()).hexdigest(), 16)
    offset = hash_val % 15  # 0-14 range
    backend_port = 9100 + offset
    frontend_port = 9200 + offset
    return backend_port, frontend_port
```

**Worktree Directory Structure:**
```
artifacts/{org}/{repo}/
  trees/
    {cxc_id}/
      .git                 # Worktree git directory
      .ports.env           # Port configuration
      specs/               # Plan files
      src/                 # Source code
      ...                  # Full project structure
```

### 4.3 Workflow Engine Architecture

#### 4.3.1 Workflow Phase Interface

```mermaid
classDiagram
    class WorkflowPhase {
        <<interface>>
        +main()
    }

    class PlanISO {
        +main()
        -fetch_issue()
        -classify_and_branch()
        -create_worktree()
        -build_plan()
        -commit_and_push()
    }

    class BuildISO {
        +main()
        -load_state()
        -validate_worktree()
        -implement_plan()
        -commit_and_push()
    }

    class TestISO {
        +main()
        -run_tests()
        -parse_results()
        -resolve_failures()
        -run_e2e_tests()
    }

    class SDLCISO {
        +main()
        -run_workflow_module()
    }

    WorkflowPhase <|-- PlanISO
    WorkflowPhase <|-- BuildISO
    WorkflowPhase <|-- TestISO
    WorkflowPhase <|-- SDLCISO

    SDLCISO --> PlanISO
    SDLCISO --> BuildISO
    SDLCISO --> TestISO
```

**Phase Chaining:**
```mermaid
stateDiagram-v2
    [*] --> Plan
    Plan --> Build : success
    Plan --> [*] : failure
    Build --> Test : success
    Build --> [*] : failure
    Test --> Review : success/warnings
    Test --> [*] : max_retries_exceeded
    Review --> Document : no_blockers
    Review --> Patch : has_blockers
    Patch --> Test
    Document --> Ship : zte_enabled
    Document --> [*] : normal_mode
    Ship --> [*]
```

---

## 5. Data Models

### 5.1 Core Data Types

```mermaid
classDiagram
    class GitHubIssue {
        +int number
        +str title
        +Optional~str~ body
        +str state
        +dict author
        +List~dict~ labels
        +str url
        +str createdAt
        +str updatedAt
    }

    class TestResult {
        +str test_name
        +str test_purpose
        +bool passed
        +Optional~str~ error_message
        +str execution_command
    }

    class E2ETestResult {
        +str test_name
        +str test_purpose
        +bool passed
        +Optional~str~ error_message
        +str execution_command
        +List~str~ test_steps
        +List~str~ screenshots
    }

    class ReviewResult {
        +bool success
        +str review_summary
        +List~ReviewIssue~ review_issues
        +List~str~ screenshots
    }

    class ReviewIssue {
        +int review_issue_number
        +str screenshot_path
        +str issue_description
        +str issue_resolution
        +IssueSeverity issue_severity
    }

    ReviewResult --> ReviewIssue
    E2ETestResult --|> TestResult
```

### 5.2 Type Literals

```python
# Slash Commands
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

# Issue Classification
IssueClassSlashCommand = Literal["/feature", "/bug", "/chore", "/patch"]

# Model Selection
ModelSet = Literal["base", "heavy"]

# Issue Severity
IssueSeverity = Literal["skippable", "tech_debt", "blocker"]
```

---

## 6. Command Template System

### 6.1 Template Structure

```mermaid
graph TB
    subgraph Template File
        H[Header: Title and Description]
        V[VARIABLES Section]
        I[INSTRUCTIONS Section]
        R[RELEVANT_FILES Section]
        F[FORMAT Section]
        RP[REPORT Section]
    end

    subgraph Substitution
        A1["$1 -> arg[0]"]
        A2["$2 -> arg[1]"]
        A3["$3 -> arg[2]"]
        AR["$ARGUMENTS -> raw args"]
    end

    H --> V
    V --> I
    I --> R
    R --> F
    F --> RP

    V --> A1
    V --> A2
    V --> A3
    I --> AR
```

### 6.2 Template Categories

| Category           | Commands                                                     | Model |
| :----------------- | :----------------------------------------------------------- | :---- |
| Classification     | `/classify_issue`, `/classify_and_branch`                    | haiku |
| Planning           | `/feature`, `/bug`, `/chore`, `/patch`                       | opus  |
| Implementation     | `/implement`                                                 | opus  |
| Testing            | `/test`, `/test_e2e`, `/resolve_failed_test`, `/resolve_failed_e2e_test` | sonnet |
| Review             | `/review`                                                    | sonnet |
| Documentation      | `/document`                                                  | opus  |
| Infrastructure     | `/install_worktree`, `/cleanup_worktrees`, `/commit`, `/pull_request` | sonnet |
| App-specific       | `/prepare_app`, `/start`, `/health_check`, `/prime`          | sonnet |

### 6.3 Template Search Order

```mermaid
flowchart LR
    A[Request /command] --> B{Found in project commands?}
    B -->|Yes| C[Use project template]
    B -->|No| D{Found in framework commands?}
    D -->|Yes| E[Use framework template]
    D -->|No| F{Found in .claude/commands?}
    F -->|Yes| G[Use .claude template]
    F -->|No| H[Error: Command not found]
```

---

## 7. Trigger Mechanisms

### 7.1 CLI Router

```mermaid
flowchart TD
    A[cxc command] --> B{Parse subcommand}

    B -->|plan| C[plan_iso.main]
    B -->|build| D[build_iso.main]
    B -->|test| E[test_iso.main]
    B -->|review| F[review_iso.main]
    B -->|document| G[document_iso.main]
    B -->|ship| H[ship_iso.main]
    B -->|sdlc| I[sdlc_iso.main]
    B -->|zte| J[sdlc_zte_iso.main]

    subgraph "SDLC Orchestration"
        I --> C
        C --> D
        D --> E
        E --> F
        F --> G
    end

    subgraph "ZTE Orchestration"
        J --> I
        I --> H
    end
```

### 7.2 Webhook Flow

```mermaid
sequenceDiagram
    participant GH as GitHub
    participant WH as Webhook Server
    participant Parser as CxC Parser
    participant WF as Workflow

    GH->>WH: POST /api/github/issue_comment
    WH->>WH: Verify signature
    WH->>Parser: Parse comment body

    alt Contains CxC keyword
        Parser-->>WH: workflow_type, cxc_id, model_set
        WH->>WF: Spawn subprocess
        WF-->>WH: PID
        WH-->>GH: 202 Accepted
    else No CxC keyword
        Parser-->>WH: None
        WH-->>GH: 200 OK (ignored)
    end
```

**Magic Keywords:**
```python
CxC_KEYWORDS = {
    "cxc_plan_iso": "plan_iso",
    "cxc_build_iso": "build_iso",
    "cxc_test_iso": "test_iso",
    "cxc_review_iso": "review_iso",
    "cxc_document_iso": "document_iso",
    "cxc_ship_iso": "ship_iso",
    "cxc_sdlc_iso": "sdlc_iso",
    "cxc_sdlc_zte_iso": "sdlc_zte_iso",
}
```

---

## 8. Artifact Organization

### 8.1 Directory Structure

```
project-root/
  .cxc.yaml                     # Project configuration
  .env                          # Environment variables
  specs/
    issue-42-cxc-abc12345-add-auth.md     # Implementation plans
    patch/
      issue-42-review-fix.md              # Patch plans
  app_docs/
    feature-abc12345-auth.md              # Generated docs
    assets/
      01_login_screen.png                 # Review screenshots
  artifacts/
    org/
      repo/
        abc12345/                         # CxC instance
          cxc_state.json                  # Workflow state
          ops/
            prompts/
              2025-12-30_12-00-00.md      # Saved prompts
            execution.log                  # Execution logs
          sdlc_planner/
            raw_output.jsonl              # Agent output
          sdlc_implementor/
            raw_output.jsonl
          test_runner/
            raw_output.jsonl
          reviewer/
            review_img/
              01_critical_feature.png
            raw_output.jsonl
        trees/
          abc12345/                       # Git worktree
            .ports.env                    # Port configuration
            .git/                         # Worktree git
            src/
            specs/
            ...
```

### 8.2 Logging Strategy

```mermaid
flowchart TD
    A[Agent Execution] --> B[Console Handler]
    A --> C[File Handler]

    B --> D[INFO+ to stdout]
    C --> E[DEBUG+ to execution.log]

    A --> F[JSONL Output]
    F --> G[Parse result]
    G --> H[Save raw_output.jsonl]

    A --> I[Prompt Content]
    I --> J[Save prompts/timestamp.md]
```

---

## 9. Security Considerations

### 9.1 Environment Variable Handling

```python
SAFE_ENV_VARS = {
    # Required
    "ANTHROPIC_API_KEY",
    "CLAUDE_CODE_PATH",

    # Optional secrets
    "GITHUB_PAT",
    "E2B_API_KEY",

    # System essentials
    "HOME", "USER", "PATH", "SHELL", "TERM",
    "PYTHONPATH", "PYTHONUNBUFFERED",
}

def get_safe_subprocess_env() -> dict:
    """Filter env vars for subprocess execution."""
    return {k: os.getenv(k) for k in SAFE_ENV_VARS if os.getenv(k)}
```

### 9.2 Webhook Signature Verification

```python
def verify_github_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook signature."""
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

---

## 10. Error Handling Strategy

### 10.1 Phase-Level Error Handling

```mermaid
flowchart TD
    A[Phase Execution] --> B{Success?}
    B -->|Yes| C[Update State]
    B -->|No| D[Log Error]

    D --> E[Post to Issue]
    E --> F{Recoverable?}

    F -->|Yes| G[Attempt Recovery]
    F -->|No| H[Exit with Error Code]

    G --> I{Recovery Success?}
    I -->|Yes| A
    I -->|No| H

    C --> J[Save State]
    J --> K[Continue to Next Phase]
```

### 10.2 Test Resolution Strategy

| Attempt | Action                                  | On Failure                    |
| :------ | :-------------------------------------- | :---------------------------- |
| 1       | Run tests                               | Identify failures             |
| 2       | Resolve each failure with agent         | Track resolved vs unresolved  |
| 3       | Re-run tests after resolution           | If resolved > 0, continue     |
| 4       | Final attempt after second resolution   | Accept remaining failures     |
| Max     | Post summary with remaining failures    | Continue to review phase      |

---

## 11. Performance Optimizations

### 11.1 Combined Classification

Instead of two LLM calls:
```
classify_issue() -> /feature
generate_branch_name() -> feat-issue-42-...
```

Single call via `/classify_and_branch`:
```json
{"issue_class": "/feature", "branch_name": "feat-issue-42-cxc-abc123-add-auth"}
```

**Impact:** 50% reduction in classification latency

### 11.2 Deterministic Port Allocation

Instead of scanning for available ports:
```python
for port in range(9100, 9115):
    if is_available(port):
        return port
```

Hash-based allocation:
```python
offset = hash(cxc_id) % 15
return 9100 + offset
```

**Impact:** O(1) vs O(n) port allocation

### 11.3 State Persistence Strategy

- Save state after each update (crash recovery)
- Load state once per phase (not per function)
- JSON format for human readability and debugging

---

## 12. Extensibility Points

### 12.1 Custom Command Templates

```
project/.claude/commands/
  prepare_app.md      # Custom app preparation
  start.md            # Custom app startup
  test_e2e.md         # Custom E2E test execution
  health_check.md     # Custom health checks
  e2e/
    test_login.md     # Feature-specific E2E tests
    test_search.md
```

### 12.2 App-Specific Configuration

```yaml
# .cxc.yaml
app:
  backend_dir: "./app/server"
  frontend_dir: "./app/client"
  test_command: "pytest tests/ -v"
  reset_db_script: "./scripts/reset_db.sh"
  start_script: "./scripts/start.sh"
  typecheck_command: "npm run typecheck"
  build_command: "npm run build"
```

### 12.3 Workflow Customization

- Composite workflows in `workflows/wt/` (e.g., `plan_build_iso.py`)
- Flags for phase skipping (`--skip-e2e`, `--skip-resolution`)
- Model set override via webhook comment (`model_set heavy`)

---

## 13. Dependencies

### 13.1 Python Dependencies

| Package         | Version    | Purpose                        |
| :-------------- | :--------- | :----------------------------- |
| python-dotenv   | >=1.0.0    | Environment variable loading   |
| pydantic        | >=2.0.0    | Data validation and models     |
| pyyaml          | >=6.0.0    | YAML configuration parsing     |
| GitPython       | >=3.0.0    | Git repository operations      |
| schedule        | >=1.2.0    | Cron trigger scheduling        |
| fastapi         | >=0.100.0  | Webhook server                 |
| uvicorn         | >=0.23.0   | ASGI server for webhooks       |
| aiosqlite       | >=0.19.0   | Async SQLite for state         |
| boto3           | >=1.26.0   | R2/S3 artifact uploads         |
| rich            | >=13.0.0   | Terminal output formatting     |

### 13.2 External Dependencies

| Tool         | Purpose                       |
| :----------- | :---------------------------- |
| `claude`     | Claude Code CLI               |
| `gh`         | GitHub CLI                    |
| `git`        | Version control               |
| `uv`         | Python package manager        |

---

*End of Design Specification*
