# ADW Framework - C4 Architecture Diagrams (Claude)

> **For**: New developers onboarding to the ADW Framework
> **C4 Model**: Context, Container, Component diagrams + Data Flow

---

## Quick Navigation

| Diagram                                                | What It Shows          | Best For                              |
| ------------------------------------------------------ | ---------------------- | ------------------------------------- |
| [Level 1: Context](#level-1-system-context)            | ADW + external systems | Understanding the ecosystem           |
| [Level 2: Container](#level-2-containers)              | Internal packages      | Finding where code lives              |
| [Level 3: Core](#level-3-core-components)              | Core module internals  | Understanding state/config/agent      |
| [Level 3: Integrations](#level-3-integrations-components) | Integration internals  | Understanding GitHub/Git/Worktree ops |
| [Data Flow](#data-flow-sdlc-execution-path)            | SDLC execution path    | Following a workflow end-to-end       |

---

## What is C4?

C4 is a lightweight architecture documentation approach with 4 levels of abstraction:

1. **Context** - How the system fits in the world (users, external systems)
2. **Container** - High-level technical building blocks (packages, databases, services)
3. **Component** - Internal components within each container
4. **Code** - Class/function level (not included here - too detailed)

Read diagrams **top-down**: start with Context, zoom into Containers, then Components.

---

## Level 1: System Context

*Shows ADW and everything it interacts with*

```mermaid
flowchart TB
    subgraph Actors
        Dev[Developer]
        GHWebhook[GitHub Webhook]
    end

    subgraph ADW[ADW Framework]
        ADWSystem[ADW Orchestrator]
    end

    subgraph External[External Systems]
        GitHub[GitHub API via gh CLI]
        Claude[Claude Code CLI]
        Git[Git CLI]
        R2[Cloudflare R2 optional]
    end

    Dev -->|CLI commands| ADWSystem
    GHWebhook -->|Issue events| ADWSystem
    ADWSystem -->|Issues PRs Comments| GitHub
    ADWSystem -->|Prompts JSONL| Claude
    ADWSystem -->|Worktrees Branches| Git
    ADWSystem -->|Screenshots| R2
```

**ASCII version:**

```
     +-------------+       +------------------+
     |  Developer  |       | GitHub Webhook   |
     +------+------+       +--------+---------+
            |                       |
            | CLI commands          | Issue events
            v                       v
    +-------+-----------------------+---------+
    |                                         |
    |           ADW Orchestrator              |
    |                                         |
    +--+----------+----------+----------+-----+
       |          |          |          |
       v          v          v          v
  +--------+ +--------+ +--------+ +----------+
  | GitHub | | Claude | |  Git   | |    R2    |
  |  API   | |  Code  | |  CLI   | | optional |
  +--------+ +--------+ +--------+ +----------+
```

### Key Takeaways

| Actor/System       | Interaction                                           |
| ------------------ | ----------------------------------------------------- |
| **Developer**      | Runs `uv run adw sdlc 42` to process GitHub issues    |
| **GitHub Webhook** | Triggers workflows when issues are created/commented  |
| **GitHub API**     | Read issues, post comments, create PRs (via `gh` CLI) |
| **Claude Code**    | Execute AI prompts, receive JSONL streaming output    |
| **Git**            | Create worktrees, branches, commits, push changes     |
| **Cloudflare R2**  | Optional - store screenshots for review phase         |

---

## Level 2: Containers

*Shows the major packages inside ADW*

```mermaid
flowchart TB
    subgraph Entry[Entry Points]
        CLI[CLI - adw/cli.py]
        Triggers[Triggers - FastAPI]
    end

    subgraph Workflows[Workflows - adw/workflows/wt/]
        Plan[plan_iso]
        Build[build_iso]
        Test[test_iso]
        Review[review_iso]
        Document[document_iso]
        Ship[ship_iso]
        SDLC[sdlc_iso Orchestrator]
    end

    subgraph Core[Core - adw/core/]
        Config[ADWConfig]
        State[ADWState]
        Agent[Agent]
        Types[DataTypes]
        Utils[Utils]
    end

    subgraph Integrations[Integrations - adw/integrations/]
        GHOps[GitHub Ops]
        GitOps[Git Ops]
        WTOps[Worktree Ops]
        WFOps[Workflow Ops]
        R2Up[R2 Uploader]
    end

    subgraph Storage[Artifacts - Filesystem]
        StateFiles[adw_state.json]
        Logs[raw_output.jsonl]
        Trees[trees/adw-id/]
    end

    CLI --> SDLC
    CLI --> Plan
    CLI --> Build
    Triggers --> SDLC

    SDLC --> Plan
    SDLC --> Build
    SDLC --> Test
    SDLC --> Review
    SDLC --> Document
    SDLC --> Ship

    Plan --> Core
    Build --> Core
    Test --> Core
    Review --> Core

    Plan --> Integrations
    Build --> Integrations
    Test --> Integrations
    Review --> Integrations

    Core --> Storage
    Integrations --> Storage
```

**ASCII version:**

```
+-------------------ENTRY POINTS--------------------+
|   +------------+            +----------------+    |
|   | CLI        |            | Triggers       |    |
|   | adw/cli.py |            | FastAPI/Cron   |    |
|   +-----+------+            +-------+--------+    |
+---------|-----------------------|------------------+
          |                       |
          v                       v
+-------------------WORKFLOWS-----------------------+
|  +--------+ +--------+ +--------+ +--------+      |
|  |plan_iso| |build_  | |test_   | |review_ |      |
|  +--------+ |iso     | |iso     | |iso     |      |
|             +--------+ +--------+ +--------+      |
|  +----------+ +--------+                          |
|  |document_ | |ship_iso|   +------------------+   |
|  |iso       | +--------+   | sdlc_iso         |   |
|  +----------+              | (orchestrator)   |   |
|                            +------------------+   |
+--------+------------------------------+-----------+
         |                              |
         v                              v
+--------+--------+          +----------+---------+
| CORE            |          | INTEGRATIONS       |
| adw/core/       |          | adw/integrations/  |
|-----------------|          |--------------------|
| ADWConfig       |          | GitHub Ops         |
| ADWState        |          | Git Ops            |
| Agent           |          | Worktree Ops       |
| DataTypes       |          | Workflow Ops       |
| Utils           |          | R2 Uploader        |
+--------+--------+          +----------+---------+
         |                              |
         v                              v
+-------------------STORAGE---------------------+
|  adw_state.json   raw_output.jsonl   trees/  |
+-----------------------------------------------+
```

### Container Summary

| Container        | Path                | Purpose                                    |
| ---------------- | ------------------- | ------------------------------------------ |
| **CLI**          | `adw/cli.py`        | Entry point, routes commands to workflows  |
| **Triggers**     | `adw/triggers/`     | Webhook server (FastAPI), cron monitor     |
| **Workflows**    | `adw/workflows/wt/` | SDLC phases - isolated worktree workflows  |
| **Core**         | `adw/core/`         | Config, state, agent execution, data types |
| **Integrations** | `adw/integrations/` | GitHub, Git, worktree, R2 operations       |
| **Storage**      | `artifacts/`        | State JSON, agent logs, git worktrees      |

---

## Level 3: Core Components

*Zooms into the `adw/core/` package*

```mermaid
flowchart TB
    subgraph Core[Core Package]
        Config[ADWConfig - config.py]
        State[ADWState - state.py]
        Agent[Agent - agent.py]
        Types[DataTypes - data_types.py]
        Utils[Utils - utils.py]

        Config --> State
        State --> Agent
        Types --> State
        Types --> Agent
        Utils --> Agent
    end

    subgraph External[External Calls]
        ClaudeCLI[Claude Code subprocess]
        FileSystem[Filesystem artifacts/]
    end

    Agent --> ClaudeCLI
    State --> FileSystem
    Config --> FileSystem
```

**ASCII version:**

```
+---------------------CORE PACKAGE-----------------------+
|                                                        |
|  +---------------+                                     |
|  | ADWConfig     |------------------+                  |
|  | config.py     |                  |                  |
|  +-------+-------+                  |                  |
|          |                          v                  |
|          |               +------------------+          |
|          +-------------->| ADWState         |          |
|                          | state.py         |          |
|                          +--------+---------+          |
|                                   |                    |
|  +---------------+                v                    |
|  | DataTypes     |       +--------+---------+          |
|  | data_types.py |------>| Agent            |          |
|  +---------------+       | agent.py         |          |
|                          +--------+---------+          |
|  +---------------+                ^                    |
|  | Utils         |----------------+                    |
|  | utils.py      |                                     |
|  +---------------+                                     |
|                                                        |
+-------------------+------------------+-----------------+
                    |                  |
                    v                  v
          +------------------+  +------------------+
          | Claude Code CLI  |  | Filesystem       |
          | subprocess.Popen |  | artifacts/       |
          +------------------+  +------------------+
```

### Core Component Details

| Component     | File            | Key Functions                                               |
| ------------- | --------------- | ----------------------------------------------------------- |
| **ADWConfig** | `config.py`     | `load()`, `get_agents_dir()`, `get_trees_dir()`             |
| **ADWState**  | `state.py`      | `save()`, `load()`, `update()`, `get_working_directory()`   |
| **Agent**     | `agent.py`      | `execute_template()`, `prompt_claude_code()`, `parse_jsonl` |
| **DataTypes** | `data_types.py` | `ADWStateData`, `AgentPromptRequest`, `RetryCode`           |
| **Utils**     | `utils.py`      | `setup_logger()`, `check_env_vars()`, `get_safe_env()`      |

---

## Level 3: Integrations Components

*Zooms into the `adw/integrations/` package*

```mermaid
flowchart TB
    subgraph Integrations[Integrations Package]
        GHOps[GitHub Ops - github.py]
        GitOps[Git Ops - git_ops.py]
        WTOps[Worktree Ops - worktree_ops.py]
        WFOps[Workflow Ops - workflow_ops.py]
        R2Up[R2 Uploader - r2_uploader.py]

        WFOps --> GHOps
        WFOps --> GitOps
        WFOps --> WTOps
    end

    subgraph External[External Systems]
        GH[gh CLI]
        Git[git CLI]
        R2[Cloudflare R2 API]
    end

    GHOps --> GH
    GitOps --> Git
    WTOps --> Git
    R2Up --> R2
```

**ASCII version:**

```
+------------------INTEGRATIONS PACKAGE------------------+
|                                                        |
|                +--------------------+                  |
|                | Workflow Ops       |                  |
|                | workflow_ops.py    |                  |
|                +---------+----------+                  |
|                          |                             |
|          +---------------+---------------+             |
|          |               |               |             |
|          v               v               v             |
|   +------------+  +------------+  +--------------+     |
|   | GitHub Ops |  | Git Ops    |  | Worktree Ops |     |
|   | github.py  |  | git_ops.py |  | worktree_ops |     |
|   +-----+------+  +-----+------+  +-------+------+     |
|         |               |                 |            |
|         |               |                 |            |
|         |         +-----+-----+           |            |
|         |         |           |           |            |
+---------|---------|-----------|-----------|------------+
          |         |           |           |
          v         v           v           v
     +--------+ +--------+ +--------+ +-----------+
     | gh CLI | |git CLI | |git CLI | | R2 API    |
     +--------+ +--------+ +--------+ +-----------+
                                      (R2 Uploader)
```

### Integrations Component Details

| Component        | File              | Key Functions                                           |
| ---------------- | ----------------- | ------------------------------------------------------- |
| **GitHub Ops**   | `github.py`       | `fetch_issue()`, `make_issue_comment()`, `get_repo_url` |
| **Git Ops**      | `git_ops.py`      | `commit_changes()`, `finalize_git_operations()`         |
| **Worktree Ops** | `worktree_ops.py` | `create_worktree()`, `validate_worktree()`, `get_ports` |
| **Workflow Ops** | `workflow_ops.py` | `ensure_adw_id()`, `classify_issue()`, `build_plan()`   |
| **R2 Uploader**  | `r2_uploader.py`  | `upload_screenshot()`, `get_public_url()`               |

---

## Data Flow: SDLC Execution Path

*Shows how data flows through a complete `adw sdlc 42` run*

```mermaid
flowchart TB
    Issue[GitHub Issue]

    subgraph Plan[1 - Plan Phase]
        P1[fetch_issue] --> P2[classify_issue]
        P2 --> P3[generate_branch]
        P3 --> P4[create_worktree]
        P4 --> P5[build_plan]
        P5 --> P6[commit_push]
        P6 --> P7[create_pr]
    end

    subgraph Build[2 - Build Phase]
        B1[load_state] --> B2[implement]
        B2 --> B3[commit]
    end

    subgraph Test[3 - Test Phase]
        T1[pytest] --> T2[auto_fix_3x]
        T2 --> T3[e2e_optional]
    end

    subgraph Review[4 - Review Phase]
        R1[review] --> R2[screenshots]
        R2 --> R3[remediate_3x]
    end

    subgraph Doc[5 - Document Phase]
        D1[document] --> D2[save_docs]
    end

    subgraph Ship[6 - Ship Phase ZTE]
        S1[approve_pr] --> S2[merge_squash]
    end

    PR[Merged PR]

    Issue --> P1
    P7 --> B1
    B3 --> T1
    T3 --> R1
    R3 --> D1
    D2 --> S1
    S2 --> PR
```

**ASCII version:**

```
                      +----------------+
                      | GitHub Issue   |
                      +-------+--------+
                              |
                              v
+======================1. PLAN PHASE=======================+
|                                                          |
|  fetch_issue -> classify_issue -> generate_branch        |
|                                         |                |
|                                         v                |
|  create_pr <- commit_push <- build_plan <- create_wt     |
|                                                          |
+=============================+============================+
                              |
                              v
+======================2. BUILD PHASE======================+
|                                                          |
|  load_state ---------> implement ---------> commit       |
|                                                          |
+=============================+============================+
                              |
                              v
+======================3. TEST PHASE=======================+
|                                                          |
|  pytest ---------> auto_fix (x3) ---------> e2e (opt)    |
|                                                          |
+=============================+============================+
                              |
                              v
+======================4. REVIEW PHASE=====================+
|                                                          |
|  review ---------> screenshots ---------> remediate (x3) |
|                                                          |
+=============================+============================+
                              |
                              v
+======================5. DOCUMENT PHASE===================+
|                                                          |
|  document ---------> save_docs                           |
|                                                          |
+=============================+============================+
                              |
                              v
+======================6. SHIP PHASE (ZTE)=================+
|                                                          |
|  approve_pr ---------> merge_squash                      |
|                                                          |
+=============================+============================+
                              |
                              v
                      +----------------+
                      |   Merged PR    |
                      +----------------+
```

### Phase-by-Phase Breakdown

| Phase        | Key Operations                                   | State Changes                                         |
| ------------ | ------------------------------------------------ | ----------------------------------------------------- |
| **Plan**     | Fetch issue, classify, create worktree, gen plan | `issue_class`, `branch_name`, `worktree_path`, `plan` |
| **Build**    | Load plan file, execute `/implement`             | Code changes committed                                |
| **Test**     | Run pytest, auto-fix up to 3x                    | Tests passing                                         |
| **Review**   | Validate against spec, screenshots               | Review artifacts                                      |
| **Document** | Generate feature docs                            | `app_docs/` updated                                   |
| **Ship**     | Approve PR, squash merge                         | PR merged to main                                     |

---

## Key Concepts Reference

| Concept               | Description                                                                     |
| --------------------- | ------------------------------------------------------------------------------- |
| **ADW ID**            | 8-character unique identifier per workflow instance (e.g., `abc12345`)          |
| **Isolated Worktree** | Each workflow runs in `artifacts/{project_id}/trees/{adw-id}/`                  |
| **Port Allocation**   | Deterministic: backend 9100-9114, frontend 9200-9214                            |
| **Model Selection**   | `base` uses Sonnet, `heavy` uses Opus (configured per command)                  |
| **State Persistence** | `adw_state.json` tracks: adw_id, issue_number, branch_name, plan_file, worktree |

---

## File Structure After ADW Run

```
artifacts/{org}/{repo}/
    {adw-id}/
        adw_state.json           # Workflow state
        sdlc_planner/
            raw_output.jsonl     # Claude Code output
            prompts/
                feature.txt      # Saved prompt
        sdlc_implementor/
        tester/
        reviewer/
            review_img/          # Screenshots
        documenter/
    trees/
        {adw-id}/                # Git worktree (full repo clone)
            .ports.env           # Backend/frontend ports
            specs/
                issue-42-adw-abc12345-add-auth.md
```

---

## See Also

- [ORCHESTRATOR_GUIDE.md](./ORCHESTRATOR_GUIDE.md) - Detailed workflow documentation
- [README.md](../README.md) - Setup and configuration
- [commands/](../commands/) - Slash command templates
