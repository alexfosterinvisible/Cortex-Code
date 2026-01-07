# CxC Framework - Product Requirements Document (Claude)

Version: 1.0.0 | Generated: 2025-12-30 | Approach: Feature-Map Driven

---

## Executive Summary

CxC (Cortex Code) Framework is an orchestration system that automates the complete software development lifecycle using Claude Code agents. It processes GitHub issues through structured phases - plan, build, test, review, document, ship - enabling autonomous code generation with human oversight at key checkpoints.

**Core Value Proposition**: Transform a GitHub issue into a merged, tested, documented pull request with minimal human intervention.

---

## 1. Product Vision

### 1.1 Problem Statement

Software development involves repetitive workflows:
1. Reading and understanding issues
2. Planning implementation approach
3. Writing code to specification
4. Running tests and fixing failures
5. Reviewing changes against requirements
6. Writing documentation
7. Creating and merging pull requests

Each step requires context switching and cognitive overhead. LLM-powered agents can execute these steps, but orchestrating them requires:
- Consistent state management
- Isolation for parallel execution
- Integration with existing tools (GitHub, Git)
- Structured prompting for each phase

### 1.2 Solution

CxC Framework provides:
- **CLI interface** for triggering individual phases or full pipeline
- **Worktree isolation** for parallel workflow execution
- **State persistence** across process boundaries
- **Agent orchestration** via Claude Code with slash commands
- **GitHub integration** for issues, PRs, and comments
- **Trigger mechanisms** for automation (webhooks, cron)

### 1.3 Target Users

| User Type           | Use Case                                         |
|---------------------|--------------------------------------------------|
| Solo Developer      | Automate routine coding tasks                    |
| Development Team    | Scale throughput without scaling headcount       |
| DevOps/Platform     | Build automation pipelines                       |
| Open Source Maintainer | Triage and implement simple issues            |

---

## 2. Feature Catalog

### 2.1 Feature Category: Issue Processing

#### F-IP-01: Issue Fetching

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | Retrieves GitHub issue data including title, body, labels, comments |
| **When used**      | Start of any workflow requiring issue context        |
| **Inputs**         | Issue number, repository path                        |
| **Outputs**        | Typed GitHubIssue model                              |
| **Success Criteria** | Issue data loaded with all required fields         |
| **Edge Cases**     | Issue doesn't exist (error), rate limiting (gh handles) |

#### F-IP-02: Issue Classification

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | Determines if issue is feature, bug, or chore        |
| **When used**      | Before planning to select appropriate template       |
| **Inputs**         | GitHubIssue (number, title, body)                    |
| **Outputs**        | IssueClassSlashCommand: /feature, /bug, /chore       |
| **Success Criteria** | Returns valid classification                       |
| **Edge Cases**     | Ambiguous issue (agent picks best match), invalid response (error) |

#### F-IP-03: Branch Name Generation

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | Creates standardized branch name from issue          |
| **When used**      | After classification, before worktree creation       |
| **Inputs**         | Issue type, CxC ID, issue data                       |
| **Outputs**        | Git-safe branch name                                 |
| **Success Criteria** | Contains issue number and CxC ID, valid git branch  |
| **Edge Cases**     | Long titles (truncated), special chars (sanitized)   |

#### F-IP-04: Combined Classify and Branch

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | Performs F-IP-02 and F-IP-03 in single LLM call      |
| **When used**      | Default path in planning phase                       |
| **Inputs**         | CxC ID, minimal issue JSON                           |
| **Outputs**        | JSON with issue_class and branch_name                |
| **Success Criteria** | 2x faster than sequential, both values valid        |
| **Edge Cases**     | JSON parsing failure (retry)                         |

#### F-IP-05: Plan File Creation

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | Generates implementation plan markdown               |
| **When used**      | Planning phase after classification                  |
| **Inputs**         | Issue, classified command, working directory         |
| **Outputs**        | Plan file at specs/issue-{num}-cxc-{id}-{desc}.md    |
| **Success Criteria** | File exists with implementation steps              |
| **Edge Cases**     | Agent fails (retry), large issues (long plan)        |

---

### 2.2 Feature Category: Execution Environment

#### F-EE-01: Git Worktree Isolation

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | Creates isolated git working directory per workflow  |
| **When used**      | All *_iso workflows                                  |
| **Inputs**         | Branch name, CxC ID                                  |
| **Outputs**        | Worktree at artifacts/{project}/trees/{cxc_id}/      |
| **Success Criteria** | Directory created, branch checked out, files present |
| **Edge Cases**     | Existing worktree (removed), missing branch (created from main) |

#### F-EE-02: Port Allocation

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | Assigns deterministic ports from CxC ID hash         |
| **When used**      | During worktree creation for dev servers             |
| **Inputs**         | CxC ID, port configuration                           |
| **Outputs**        | backend_port (9100-9114), frontend_port (9200-9214)  |
| **Success Criteria** | Same CxC ID always gets same ports                 |
| **Edge Cases**     | Port in use (app must handle), range exhausted (wraps) |

#### F-EE-03: Model Selection

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | Picks Claude model based on command and model set    |
| **When used**      | Every agent execution                                |
| **Inputs**         | Slash command, model set from state                  |
| **Outputs**        | Model name: haiku, sonnet, or opus                   |
| **Success Criteria** | Correct model per SLASH_COMMAND_MODEL_MAP          |
| **Edge Cases**     | Unknown command (default sonnet), no state (base)    |

#### F-EE-04: Prompt Templating

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | Loads slash command template and substitutes args    |
| **When used**      | Every agent execution                                |
| **Inputs**         | Slash command name, arguments list                   |
| **Outputs**        | Complete prompt string                               |
| **Success Criteria** | $ARGUMENTS replaced with joined args               |
| **Edge Cases**     | Template not found (error), multiple dirs (priority) |

---

### 2.3 Feature Category: SDLC Automation

#### F-SA-01: Planning Workflow

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | Fetches issue, creates branch, generates plan, creates PR |
| **When used**      | CLI: `cxc plan <issue>`, or as first SDLC phase      |
| **Inputs**         | Issue number, optional CxC ID                        |
| **Outputs**        | Branch with plan file, PR URL, updated state         |
| **Success Criteria** | PR created linking to issue with plan             |
| **Edge Cases**     | Existing branch (reuse), existing PR (skip creation) |

#### F-SA-02: Build Workflow

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | Implements changes per plan file                     |
| **When used**      | CLI: `cxc build <issue> <cxc_id>`, after planning    |
| **Inputs**         | Issue number, CxC ID (required)                      |
| **Outputs**        | Implemented code, commit                             |
| **Success Criteria** | /implement succeeds, changes committed             |
| **Edge Cases**     | No plan (error), complex plan (multiple attempts)    |

#### F-SA-03: Testing Workflow

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | Runs tests, auto-fixes failures up to 3 retries      |
| **When used**      | CLI: `cxc test <issue> <cxc_id>`, after build        |
| **Inputs**         | Issue number, CxC ID, optional --skip-e2e            |
| **Outputs**        | Test results, fixed code if applicable               |
| **Success Criteria** | All tests pass OR max retries exhausted            |
| **Edge Cases**     | Unfixable failures (report), no tests (skip)         |

#### F-SA-04: Review Workflow

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | Validates implementation against spec, captures screenshots |
| **When used**      | CLI: `cxc review <issue> <cxc_id>`, after testing    |
| **Inputs**         | Issue number, CxC ID, optional --skip-resolution     |
| **Outputs**        | ReviewResult with issues, screenshots                |
| **Success Criteria** | Review completes, blockers addressed if enabled    |
| **Edge Cases**     | UI not running (skip screenshots), severe blockers (fail) |

#### F-SA-05: Documentation Workflow

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | Generates documentation for implementation           |
| **When used**      | CLI: `cxc document <issue> <cxc_id>`, after review   |
| **Inputs**         | Issue number, CxC ID                                 |
| **Outputs**        | Documentation file(s), commit                        |
| **Success Criteria** | Docs created and committed                         |
| **Edge Cases**     | No docs needed (skip), existing docs (update)        |

#### F-SA-06: Ship Workflow

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | Approves PR, merges to main, closes issue            |
| **When used**      | CLI: `cxc ship <issue> <cxc_id>`, final phase        |
| **Inputs**         | Issue number, CxC ID                                 |
| **Outputs**        | Merged PR, closed issue                              |
| **Success Criteria** | PR merged, issue closed                            |
| **Edge Cases**     | Merge conflicts (fail), required reviews (error)     |

#### F-SA-07: Full SDLC Pipeline

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | Chains plan -> build -> test -> review -> document   |
| **When used**      | CLI: `cxc sdlc <issue>`                              |
| **Inputs**         | Issue number, optional --skip-e2e, --skip-resolution |
| **Outputs**        | Complete implementation ready for merge              |
| **Success Criteria** | All phases complete successfully                   |
| **Edge Cases**     | Phase failure (stop pipeline), partial completion    |

#### F-SA-08: Zero Touch Execution

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | Full SDLC + automatic merge (no human intervention)  |
| **When used**      | CLI: `cxc zte <issue>`, webhook trigger              |
| **Inputs**         | Issue number, optional flags                         |
| **Outputs**        | Merged PR, closed issue, deployed code               |
| **Success Criteria** | Issue resolved end-to-end                          |
| **Edge Cases**     | Any failure stops pipeline                           |

---

### 2.4 Feature Category: Persistence

#### F-PE-01: State Management

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | Persists workflow state to JSON file                 |
| **When used**      | Throughout all workflows                             |
| **Inputs**         | CxC ID, state updates                                |
| **Outputs**        | cxc_state.json at artifacts/{project}/{cxc_id}/      |
| **Success Criteria** | State survives process restarts                    |
| **Edge Cases**     | Corrupt file (error), missing file (create)          |

#### F-PE-02: Artifact Organization

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | Organizes outputs in structured directory hierarchy  |
| **When used**      | All agent executions and workflow outputs            |
| **Inputs**         | CxC ID, agent name, output type                      |
| **Outputs**        | Files at artifacts/{project}/{cxc_id}/{agent}/       |
| **Success Criteria** | All outputs discoverable and organized             |
| **Edge Cases**     | Large outputs (no size limit), many CxCs (cleanup)   |

#### F-PE-03: Prompt/Output Logging

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | Saves every prompt and JSONL output                  |
| **When used**      | Every agent execution                                |
| **Inputs**         | Prompt text, agent output stream                     |
| **Outputs**        | prompts/{command}.txt, raw_output.jsonl              |
| **Success Criteria** | Complete audit trail                               |
| **Edge Cases**     | Very long outputs (no truncation on disk)            |

#### F-PE-04: Configuration Management

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | Loads and validates project configuration            |
| **When used**      | Initialization of any workflow                       |
| **Inputs**         | .cxc.yaml in project root                            |
| **Outputs**        | CxCConfig dataclass                                  |
| **Success Criteria** | All paths resolved, defaults applied               |
| **Edge Cases**     | Missing config (defaults), invalid YAML (error)      |

---

### 2.5 Feature Category: Triggers

#### F-TR-01: CLI Triggers

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | Entry point for all workflows via cxc command        |
| **When used**      | Developer-initiated execution                        |
| **Inputs**         | Command name, arguments, flags                       |
| **Outputs**        | Workflow execution, exit code                        |
| **Success Criteria** | Correct workflow invoked with args                 |
| **Edge Cases**     | Invalid command (help), missing args (error)         |

#### F-TR-02: Webhook Triggers

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | FastAPI server processing GitHub webhook events      |
| **When used**      | Automated execution from issue comments              |
| **Inputs**         | GitHub webhook payload                               |
| **Outputs**        | Background workflow execution                        |
| **Success Criteria** | Trigger words detected, workflow launched          |
| **Edge Cases**     | Bot comments (skip), invalid payload (ignore)        |

#### F-TR-03: Cron Triggers

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | Polls for issues and triggers workflows              |
| **When used**      | Automated batch processing                           |
| **Inputs**         | Poll interval, filter criteria                       |
| **Outputs**        | Multiple workflow executions                         |
| **Success Criteria** | New issues detected and processed                  |
| **Edge Cases**     | No new issues (no-op), many issues (throttle)        |

---

### 2.6 Feature Category: Integrations

#### F-IN-01: GitHub API

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | All GitHub operations via gh CLI                     |
| **When used**      | Issue fetching, PR creation, comments                |
| **Inputs**         | gh CLI commands                                      |
| **Outputs**        | Typed models from JSON                               |
| **Success Criteria** | Operations complete successfully                   |
| **Edge Cases**     | Auth failure (error), rate limit (gh handles)        |

#### F-IN-02: Git Operations

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | Branch management, commits, pushes                   |
| **When used**      | Throughout all workflows                             |
| **Inputs**         | Git commands                                         |
| **Outputs**        | Success/failure with error message                   |
| **Success Criteria** | Git operations complete                            |
| **Edge Cases**     | Conflicts (fail), dirty state (error)                |

#### F-IN-03: Claude Code Agent

| Attribute          | Value                                                |
|--------------------|------------------------------------------------------|
| **What it does**   | Executes prompts via Claude Code CLI                 |
| **When used**      | Every agent execution                                |
| **Inputs**         | Prompt, model, flags                                 |
| **Outputs**        | AgentPromptResponse with result                      |
| **Success Criteria** | Agent completes task                               |
| **Edge Cases**     | Timeout (retry), error (retry), API down (fail)      |

---

## 3. User Journeys

### 3.1 Journey: Manual SDLC Execution

```
Developer                     CxC                          GitHub
    |                          |                              |
    |-- cxc sdlc 42 ---------->|                              |
    |                          |-- fetch_issue(42) ---------->|
    |                          |<-- issue data ---------------|
    |                          |                              |
    |                          |-- classify + branch -------->|
    |                          |   (Claude Code)              |
    |                          |                              |
    |                          |-- create worktree            |
    |                          |-- build_plan --------------->|
    |                          |   (Claude Code)              |
    |                          |-- commit plan                |
    |                          |-- push branch -------------->|
    |                          |-- create PR ----------------->|
    |                          |                              |
    |                          |-- implement_plan ----------->|
    |                          |   (Claude Code)              |
    |                          |-- commit code                |
    |                          |-- push ---------------------->|
    |                          |                              |
    |                          |-- run tests ----------------->|
    |                          |   (Claude Code)              |
    |                          |                              |
    |                          |-- review ------------------->|
    |                          |   (Claude Code)              |
    |                          |                              |
    |                          |-- document ----------------->|
    |                          |   (Claude Code)              |
    |                          |-- push final --------------->|
    |                          |                              |
    |<-- PR ready for review --|                              |
```

### 3.2 Journey: Webhook-Triggered ZTE

```
User                          GitHub                        CxC
  |                              |                            |
  |-- Comment: "cxc_sdlc_zte_iso" -->|                       |
  |                              |-- webhook -------------->|
  |                              |                          |
  |                              |   (CxC runs full SDLC)   |
  |                              |                          |
  |                              |<-- approve PR -----------|
  |                              |<-- merge PR -------------|
  |                              |<-- close issue ----------|
  |                              |                          |
  |<-- Notification: merged -----|                          |
```

### 3.3 Journey: Resuming Failed Workflow

```
Developer                     CxC
    |                          |
    |-- cxc build 42 abc12345 ->|  (resume from failed build)
    |                          |
    |                          |-- load state(abc12345)
    |                          |-- get worktree_path
    |                          |-- get plan_file
    |                          |
    |                          |-- implement_plan
    |                          |   (retry from where left off)
    |                          |
    |<-- build complete -------|
```

---

## 4. Acceptance Criteria

### 4.1 Core Functionality

| ID      | Criterion                                                    | Priority |
|---------|--------------------------------------------------------------|----------|
| AC-01   | Can process GitHub issue through full SDLC pipeline          | P0       |
| AC-02   | State persists across process restarts                       | P0       |
| AC-03   | Worktrees enable parallel workflow execution                 | P0       |
| AC-04   | Model selection based on command and model_set               | P0       |
| AC-05   | Retry logic handles transient Claude Code failures           | P1       |
| AC-06   | Bot comments don't trigger infinite loops                    | P0       |
| AC-07   | CLI provides access to all workflow phases                   | P0       |
| AC-08   | Webhook triggers workflows from issue comments               | P1       |

### 4.2 Integration

| ID      | Criterion                                                    | Priority |
|---------|--------------------------------------------------------------|----------|
| AC-10   | Fetches issues via gh CLI                                    | P0       |
| AC-11   | Creates PRs via gh CLI                                       | P0       |
| AC-12   | Comments on issues with CxC identifier                       | P0       |
| AC-13   | Creates and manages git branches                             | P0       |
| AC-14   | Executes Claude Code with correct parameters                 | P0       |

### 4.3 Configuration

| ID      | Criterion                                                    | Priority |
|---------|--------------------------------------------------------------|----------|
| AC-20   | Loads configuration from .cxc.yaml                           | P0       |
| AC-21   | Supports ${CxC_FRAMEWORK} variable expansion                 | P0       |
| AC-22   | Provides sensible defaults for optional config               | P1       |
| AC-23   | Environment variables loaded from .env                       | P0       |

### 4.4 Observability

| ID      | Criterion                                                    | Priority |
|---------|--------------------------------------------------------------|----------|
| AC-30   | Logs to both console and file                                | P1       |
| AC-31   | Saves all prompts sent to Claude Code                        | P1       |
| AC-32   | Saves all agent outputs as JSONL                             | P1       |
| AC-33   | State file contains complete workflow metadata               | P0       |

---

## 5. Success Metrics

### 5.1 Adoption Metrics

| Metric                      | Target         | Measurement                    |
|-----------------------------|----------------|--------------------------------|
| Issues processed per week   | >10            | Count of completed SDLC runs   |
| Workflow success rate       | >80%           | Successful / Total executions  |
| Time to first PR            | <10 min        | Issue creation to PR created   |

### 5.2 Quality Metrics

| Metric                      | Target         | Measurement                    |
|-----------------------------|----------------|--------------------------------|
| Test pass rate after build  | >90%           | Tests passing / Total tests    |
| Review approval rate        | >70%           | Reviews with no blockers       |
| Manual intervention rate    | <20%           | Runs requiring human fix       |

### 5.3 Performance Metrics

| Metric                      | Target         | Measurement                    |
|-----------------------------|----------------|--------------------------------|
| Classification latency      | <30s           | Time for classify_issue        |
| Planning latency            | <5min          | Time for full plan_iso         |
| Full SDLC latency           | <30min         | Time for complete sdlc_iso     |

---

## 6. Constraints and Dependencies

### 6.1 Technical Constraints

| Constraint                  | Impact                                      |
|-----------------------------|---------------------------------------------|
| Python 3.10+                | Required for type hints and syntax          |
| Claude Code CLI             | Must be installed and authenticated         |
| GitHub CLI (gh)             | Must be installed and authenticated         |
| Git                         | Must be installed, repo must have remote    |

### 6.2 External Dependencies

| Dependency                  | Version       | Purpose                        |
|-----------------------------|---------------|--------------------------------|
| python-dotenv               | >=1.0.0       | Environment loading            |
| pydantic                    | >=2.0.0       | Data validation                |
| pyyaml                      | >=6.0.0       | Config parsing                 |
| fastapi                     | >=0.100.0     | Webhook server                 |
| uvicorn                     | >=0.23.0      | ASGI server                    |
| rich                        | >=13.0.0      | Terminal output                |

### 6.3 Operational Dependencies

| Dependency                  | Requirement                                 |
|-----------------------------|---------------------------------------------|
| ANTHROPIC_API_KEY           | Valid API key with Claude access            |
| GitHub repository           | With issues enabled, write access           |
| Network access              | To api.anthropic.com, api.github.com        |

---

## 7. Risks and Mitigations

### 7.1 Technical Risks

| Risk                        | Probability | Impact | Mitigation                     |
|-----------------------------|-------------|--------|--------------------------------|
| Agent produces wrong code   | High        | Medium | Review phase catches issues    |
| API rate limiting           | Medium      | Low    | Retry logic, gh handles        |
| State corruption            | Low         | High   | State validation on load       |
| Worktree conflicts          | Low         | Medium | Unique paths per CxC ID        |

### 7.2 Operational Risks

| Risk                        | Probability | Impact | Mitigation                     |
|-----------------------------|-------------|--------|--------------------------------|
| Infinite webhook loop       | Medium      | High   | Bot identifier filtering       |
| API key exposure            | Low         | High   | .env file, filtered env        |
| Resource exhaustion         | Low         | Medium | Worktree cleanup, port range   |

### 7.3 User Experience Risks

| Risk                        | Probability | Impact | Mitigation                     |
|-----------------------------|-------------|--------|--------------------------------|
| Complex setup               | Medium      | Medium | setup_cxc_example.py script    |
| Unclear error messages      | Medium      | Medium | Detailed logging, state dumps  |
| Unexpected behavior         | Medium      | Medium | Typed models, validation       |

---

## 8. Future Roadmap

### 8.1 Short-term (Q1)

- [ ] E2B sandbox support for secure execution
- [ ] Screenshot upload to R2/S3
- [ ] Parallel phase execution where possible
- [ ] Better error recovery and resumption

### 8.2 Medium-term (Q2)

- [ ] Web UI for monitoring workflows
- [ ] Slack/Discord notifications
- [ ] Custom model provider support
- [ ] Multi-repo orchestration

### 8.3 Long-term (Q3+)

- [ ] Learning from past executions
- [ ] Automatic prompt optimization
- [ ] Cost optimization features
- [ ] Enterprise SSO integration

---

## 9. Glossary

| Term                | Definition                                          |
|---------------------|-----------------------------------------------------|
| CxC                 | Cortex Code                               |
| CxC ID              | 8-character unique identifier per workflow instance |
| Isolated Workflow   | Workflow running in dedicated git worktree          |
| Model Set           | Configuration selecting model tier (base/heavy)     |
| Slash Command       | Template command executed via Claude Code           |
| SDLC                | Software Development Life Cycle                     |
| ZTE                 | Zero Touch Execution (full automation)              |
| Worktree            | Isolated git working directory                      |

---

## 10. Appendix: CLI Command Reference

```bash
# Individual phases
cxc plan <issue_number> [cxc_id]
cxc build <issue_number> <cxc_id>
cxc test <issue_number> <cxc_id> [--skip-e2e]
cxc review <issue_number> <cxc_id> [--skip-resolution]
cxc document <issue_number> <cxc_id>
cxc ship <issue_number> <cxc_id>

# Combined workflows
cxc sdlc <issue_number> [cxc_id] [--skip-e2e] [--skip-resolution]
cxc zte <issue_number> [cxc_id] [--skip-e2e] [--skip-resolution]
cxc patch <issue_number> [cxc_id]

# Triggers
cxc monitor   # Start cron monitor
cxc webhook   # Start webhook server
```

---

## 11. Appendix: Configuration Reference

### 11.1 .cxc.yaml

```yaml
# Required
project_id: "org/repo"

# Optional with defaults
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
  custom_setting: value
```

### 11.2 .env

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-xxx

# Optional
GITHUB_PAT=ghp_xxx              # Uses gh auth if not set
CLAUDE_CODE_PATH=claude         # Path to Claude CLI
CxC_DISABLE_GITHUB_COMMENTS=0   # Disable GitHub comments
```

---

## 12. Appendix: Feature Implementation Matrix

| Feature ID | Module                  | Function(s)                           | Tests                    |
|------------|-------------------------|---------------------------------------|--------------------------|
| F-IP-01    | integrations/github.py  | fetch_issue                           | test_github.py           |
| F-IP-02    | integrations/workflow_ops.py | classify_issue                    | test_workflow_ops.py     |
| F-IP-03    | integrations/workflow_ops.py | generate_branch_name              | test_workflow_ops.py     |
| F-IP-04    | integrations/workflow_ops.py | classify_and_generate_branch      | test_workflow_ops.py     |
| F-IP-05    | integrations/workflow_ops.py | build_plan                        | test_workflow_ops.py     |
| F-EE-01    | integrations/worktree_ops.py | create_worktree                   | test_worktree_ops.py     |
| F-EE-02    | integrations/worktree_ops.py | allocate_ports                    | test_worktree_ops.py     |
| F-EE-03    | core/agent.py           | get_model_for_slash_command           | test_agent.py            |
| F-EE-04    | core/agent.py           | execute_template                      | test_agent.py            |
| F-SA-01    | workflows/wt/plan_iso.py | run                                  | test_workflow_plan.py    |
| F-SA-02    | workflows/wt/build_iso.py | run                                 | test_workflow_sdlc.py    |
| F-SA-03    | workflows/wt/test_iso.py | run                                  | test_workflow_sdlc.py    |
| F-SA-04    | workflows/wt/review_iso.py | run                                | test_workflow_sdlc.py    |
| F-SA-05    | workflows/wt/document_iso.py | run                              | test_workflow_sdlc.py    |
| F-SA-06    | workflows/wt/ship_iso.py | run                                  | test_workflow_sdlc.py    |
| F-SA-07    | workflows/wt/sdlc_iso.py | run                                  | test_workflow_sdlc.py    |
| F-SA-08    | workflows/wt/sdlc_zte_iso.py | run                              | test_workflow_sdlc.py    |
| F-PE-01    | core/state.py           | CxCState class                        | test_state.py            |
| F-PE-04    | core/config.py          | CxCConfig.load                        | test_config.py           |
| F-TR-01    | cli.py                  | main                                  | test_cli.py              |
| F-TR-02    | triggers/trigger_webhook.py | handle_webhook                    | test_webhook.py          |
| F-IN-01    | integrations/github.py  | all functions                         | test_github.py           |
| F-IN-02    | integrations/git_ops.py | all functions                         | test_git_ops.py          |
| F-IN-03    | core/agent.py           | prompt_claude_code*                   | test_agent.py            |
