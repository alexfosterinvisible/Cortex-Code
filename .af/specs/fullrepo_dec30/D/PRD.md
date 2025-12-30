# ADW Framework Product Requirements Document (Claude)

**Version:** 1.0.0
**Date:** 2025-12-30
**Document Type:** Product Requirements

---

## Executive Summary

ADW (AI Developer Workflow) is an orchestration framework that automates the entire software development lifecycle using Claude Code agents operating in isolated git worktrees. The framework processes GitHub issues through a complete pipeline: planning, building, testing, reviewing, documenting, and shipping code - with minimal human intervention.

### Value Proposition

| Stakeholder     | Value                                                       |
|:----------------|:------------------------------------------------------------|
| Developers      | Focus on high-level decisions, not implementation details   |
| Teams           | Consistent, documented, tested code with every change       |
| Organizations   | Reduced time-to-production, automated quality gates         |

---

## 1. Product Vision

### 1.1 Problem Statement

Software development involves repetitive, time-consuming tasks that follow predictable patterns:
- Reading and understanding issue requirements
- Planning implementation approaches
- Writing code that follows existing patterns
- Writing tests and fixing failures
- Reviewing code against specifications
- Documenting changes
- Creating and merging pull requests

These tasks are well-suited for AI automation, yet most AI coding tools are interactive assistants rather than autonomous workflow engines.

### 1.2 Solution

ADW Framework transforms GitHub issues into shipped code through:

1. **Autonomous Workflow Execution** - Issues are processed through a complete SDLC without manual intervention
2. **Isolated Execution Environments** - Each workflow runs in its own git worktree, enabling parallel execution
3. **Persistent State Management** - Workflows can be resumed, retried, or chained together
4. **Visual Verification** - Review phase captures screenshots proving implementation correctness
5. **Self-Healing Tests** - Failed tests trigger automatic resolution attempts

### 1.3 Target Users

| User Type           | Primary Use Case                                    |
|:--------------------|:----------------------------------------------------|
| Solo developers     | Automate implementation of feature requests         |
| Development teams   | Process issue backlog with consistent quality       |
| DevOps engineers    | Integrate ADW into CI/CD pipelines                  |
| Project managers    | Track automated development progress via comments   |

---

## 2. User Stories

### 2.1 Core User Stories

| ID     | As a...           | I want to...                                      | So that...                                        |
|:-------|:------------------|:--------------------------------------------------|:--------------------------------------------------|
| US-01  | Developer         | Run `adw sdlc 42` on any GitHub issue             | The issue is fully implemented without my coding  |
| US-02  | Developer         | See progress comments on the GitHub issue         | I know what the AI is doing at each step          |
| US-03  | Developer         | Resume a failed workflow with the same ADW ID     | I don't lose work from partial failures           |
| US-04  | Developer         | Skip E2E tests when they're flaky                 | The pipeline completes despite infrastructure issues |
| US-05  | Team lead         | Use ZTE mode for trusted changes                  | Low-risk changes ship automatically               |
| US-06  | Team lead         | Review screenshots of implemented features        | I can verify correctness without running locally  |
| US-07  | DevOps engineer   | Trigger workflows via GitHub comments             | CI/CD can initiate ADW automatically              |
| US-08  | DevOps engineer   | Run a webhook server for GitHub events            | Real-time processing of new issues                |

### 2.2 Configuration User Stories

| ID     | As a...           | I want to...                                      | So that...                                        |
|:-------|:------------------|:--------------------------------------------------|:--------------------------------------------------|
| US-09  | Developer         | Configure project-specific settings in `.adw.yaml`| ADW works with my project structure               |
| US-10  | Developer         | Add custom slash commands                         | ADW can execute project-specific operations       |
| US-11  | Developer         | Specify backend/frontend directories              | Install and test commands target correct locations|
| US-12  | Developer         | Configure port ranges for worktrees               | Multiple workflows don't conflict on ports        |

---

## 3. Functional Requirements

### 3.1 CLI Requirements

| ID       | Requirement                                                    | Priority |
|:---------|:---------------------------------------------------------------|:---------|
| FR-CLI-1 | CLI provides `plan`, `build`, `test`, `review`, `document`, `ship` commands | P0 |
| FR-CLI-2 | CLI provides `sdlc` command that chains all phases except ship | P0       |
| FR-CLI-3 | CLI provides `zte` command that includes automatic shipping    | P0       |
| FR-CLI-4 | CLI supports `--skip-e2e` flag for test command                | P1       |
| FR-CLI-5 | CLI supports `--skip-resolution` flag for review command       | P1       |
| FR-CLI-6 | CLI provides `monitor` and `webhook` trigger commands          | P1       |
| FR-CLI-7 | CLI displays help with `--help` or no arguments                | P0       |
| FR-CLI-8 | CLI exits with code 1 on any failure                           | P0       |

### 3.2 Planning Requirements

| ID        | Requirement                                                   | Priority |
|:----------|:--------------------------------------------------------------|:---------|
| FR-PLAN-1 | Classify issues as /feature, /bug, or /chore automatically    | P0       |
| FR-PLAN-2 | Generate branch names following pattern: `{type}-issue-{N}-adw-{ID}-{slug}` | P0 |
| FR-PLAN-3 | Create isolated git worktree for each workflow                | P0       |
| FR-PLAN-4 | Allocate deterministic ports based on ADW ID hash             | P0       |
| FR-PLAN-5 | Install dependencies in worktree (uv sync, bun install)       | P1       |
| FR-PLAN-6 | Create plan file in specs/ directory                          | P0       |
| FR-PLAN-7 | Create or update pull request after planning                  | P0       |
| FR-PLAN-8 | Post progress comments to GitHub issue                        | P0       |

### 3.3 Build Requirements

| ID         | Requirement                                                  | Priority |
|:-----------|:-------------------------------------------------------------|:---------|
| FR-BUILD-1 | Execute implementation based on plan file                    | P0       |
| FR-BUILD-2 | Commit changes with descriptive message                      | P0       |
| FR-BUILD-3 | Push changes and update PR                                   | P0       |
| FR-BUILD-4 | Use heavy model (Opus) for implementation                    | P0       |

### 3.4 Test Requirements

| ID        | Requirement                                                   | Priority |
|:----------|:--------------------------------------------------------------|:---------|
| FR-TEST-1 | Run unit tests and parse results as JSON                      | P0       |
| FR-TEST-2 | Attempt resolution for failed tests (up to 4 attempts)        | P0       |
| FR-TEST-3 | Run E2E tests unless --skip-e2e specified                     | P1       |
| FR-TEST-4 | Attempt resolution for failed E2E tests (up to 2 attempts)    | P1       |
| FR-TEST-5 | Post comprehensive test summary to issue                      | P0       |
| FR-TEST-6 | Exit with failure if any tests remain failed                  | P0       |

### 3.5 Review Requirements

| ID          | Requirement                                                 | Priority |
|:------------|:------------------------------------------------------------|:---------|
| FR-REVIEW-1 | Compare implementation against spec file                    | P0       |
| FR-REVIEW-2 | Capture screenshots of critical functionality               | P0       |
| FR-REVIEW-3 | Classify issues as skippable, tech_debt, or blocker         | P0       |
| FR-REVIEW-4 | Create patch plans for blocker issues                       | P1       |
| FR-REVIEW-5 | Retry review after resolving blockers (up to 3 attempts)    | P1       |
| FR-REVIEW-6 | Upload screenshots to R2 storage if configured              | P2       |
| FR-REVIEW-7 | Update PR body with review summary and screenshots          | P0       |

### 3.6 Documentation Requirements

| ID       | Requirement                                                    | Priority |
|:---------|:---------------------------------------------------------------|:---------|
| FR-DOC-1 | Generate documentation based on git diff and spec file         | P1       |
| FR-DOC-2 | Create doc file in app_docs/ directory                         | P1       |
| FR-DOC-3 | Copy screenshots to app_docs/assets/                           | P2       |
| FR-DOC-4 | Update conditional_docs.md with new entry                      | P2       |
| FR-DOC-5 | Skip documentation if no changes detected                      | P1       |

### 3.7 Ship Requirements

| ID        | Requirement                                                   | Priority |
|:----------|:--------------------------------------------------------------|:---------|
| FR-SHIP-1 | Validate all state fields are populated before shipping       | P0       |
| FR-SHIP-2 | Approve pull request via GitHub API                           | P0       |
| FR-SHIP-3 | Merge feature branch to main with --no-ff                     | P0       |
| FR-SHIP-4 | Push merged changes to origin                                 | P0       |
| FR-SHIP-5 | Close GitHub issue after successful merge                     | P0       |
| FR-SHIP-6 | Post success summary to issue                                 | P0       |

### 3.8 State Management Requirements

| ID         | Requirement                                                  | Priority |
|:-----------|:-------------------------------------------------------------|:---------|
| FR-STATE-1 | Persist workflow state to JSON file                          | P0       |
| FR-STATE-2 | Generate unique 8-character ADW IDs                          | P0       |
| FR-STATE-3 | Track which workflow phases have run                         | P0       |
| FR-STATE-4 | Support loading existing state to resume workflows           | P0       |
| FR-STATE-5 | Validate state against Pydantic schema                       | P1       |
| FR-STATE-6 | Support stdin/stdout piping for workflow chaining            | P2       |

### 3.9 Configuration Requirements

| ID        | Requirement                                                   | Priority |
|:----------|:--------------------------------------------------------------|:---------|
| FR-CFG-1  | Load configuration from .adw.yaml file                        | P0       |
| FR-CFG-2  | Walk up directory tree to find config file                    | P0       |
| FR-CFG-3  | Use sensible defaults for missing config                      | P0       |
| FR-CFG-4  | Support ${ADW_FRAMEWORK} variable expansion in paths          | P0       |
| FR-CFG-5  | Support custom command directories                            | P1       |
| FR-CFG-6  | Support app-specific configuration (backend_dir, etc.)        | P1       |

---

## 4. Non-Functional Requirements

### 4.1 Performance Requirements

| ID       | Requirement                                                    | Target   |
|:---------|:---------------------------------------------------------------|:---------|
| NFR-P-1  | Port allocation must be O(1) via hash                          | <1ms     |
| NFR-P-2  | State load/save operations                                     | <100ms   |
| NFR-P-3  | Config loading                                                 | <50ms    |
| NFR-P-4  | Combined classify+branch LLM call                              | 2x faster than separate |

### 4.2 Reliability Requirements

| ID       | Requirement                                                    | Target   |
|:---------|:---------------------------------------------------------------|:---------|
| NFR-R-1  | Workflow failures must not corrupt state                       | 100%     |
| NFR-R-2  | Partial failures must be resumable                             | 100%     |
| NFR-R-3  | Git operations must restore original branch on failure         | 100%     |
| NFR-R-4  | PR approval failures must not block shipping                   | Continue |

### 4.3 Security Requirements

| ID       | Requirement                                                    | Priority |
|:---------|:---------------------------------------------------------------|:---------|
| NFR-S-1  | API keys stored in .env files, never committed                 | P0       |
| NFR-S-2  | No force pushes to any branch                                  | P0       |
| NFR-S-3  | No modification of git config                                  | P0       |
| NFR-S-4  | Validate worktree before destructive operations                | P0       |

### 4.4 Maintainability Requirements

| ID       | Requirement                                                    | Priority |
|:---------|:---------------------------------------------------------------|:---------|
| NFR-M-1  | All agent prompts saved to artifacts for debugging             | P0       |
| NFR-M-2  | Comprehensive logging at each workflow phase                   | P0       |
| NFR-M-3  | Test coverage for all core modules                             | P1       |
| NFR-M-4  | Type hints on all public functions                             | P1       |

---

## 5. Use Case Flows

### 5.1 UC-01: Basic Feature Implementation

**Preconditions:**
- GitHub issue #42 exists with feature description
- .adw.yaml configured in project
- Claude API key set in environment

**Flow:**
```
1. Developer runs: uv run adw sdlc 42
2. System generates ADW ID: abc12345
3. System fetches issue from GitHub
4. System classifies issue as /feature
5. System generates branch: feat-issue-42-adw-abc12345-add-auth
6. System creates worktree at trees/abc12345/
7. System installs dependencies
8. System creates plan at specs/issue-42-adw-abc12345-sdlc_planner-add-auth.md
9. System commits and pushes plan
10. System creates PR
11. System implements plan
12. System runs tests
13. System reviews implementation
14. System generates documentation
15. System posts final summary to issue
16. Developer reviews PR and merges
```

**Postconditions:**
- Feature branch exists with implementation
- PR created with review summary
- Issue has progress comments
- Documentation generated

### 5.2 UC-02: Zero Touch Execution

**Preconditions:**
- Low-risk issue identified
- ZTE enabled for repository

**Flow:**
```
1. Comment on issue: adw_sdlc_zte_iso
2. Webhook triggers ZTE workflow
3. Phases 1-15 from UC-01 execute
4. System approves PR
5. System merges to main
6. System closes issue
7. System posts success message
```

**Postconditions:**
- Code shipped to production
- Issue closed
- No human intervention required

### 5.3 UC-03: Test Failure Recovery

**Preconditions:**
- Build phase completed
- Tests failing due to implementation bug

**Flow:**
```
1. System runs tests
2. 3 tests fail
3. Attempt 1: System runs /resolve_failed_test for each
4. 2 tests resolved
5. System re-runs tests
6. 1 test still failing
7. Attempt 2: System runs /resolve_failed_test
8. Test resolved
9. System re-runs tests
10. All tests pass
```

**Postconditions:**
- All tests passing
- Resolution commits in history

### 5.4 UC-04: Review Issue Resolution

**Preconditions:**
- Implementation complete
- Review identifies blocker issue

**Flow:**
```
1. System runs review
2. Review identifies blocker: "Button color wrong"
3. System creates patch plan
4. System implements patch
5. System commits patch
6. System re-runs review
7. Review passes
8. Screenshots uploaded to R2
```

**Postconditions:**
- Blocker resolved
- PR body updated with screenshots
- Review marked as successful

### 5.5 UC-05: Resume Failed Workflow

**Preconditions:**
- Plan phase completed (adw-abc12345)
- Build phase failed due to network error

**Flow:**
```
1. Developer runs: uv run adw build 42 abc12345
2. System loads existing state
3. System validates worktree exists
4. System resumes from build phase
5. Build completes successfully
6. Developer continues with: uv run adw test 42 abc12345
```

**Postconditions:**
- Workflow resumed without re-planning
- State preserved across sessions

---

## 6. Data Requirements

### 6.1 State Data Model

```
ADWState:
  adw_id: string (8 chars, required)
  issue_number: string (nullable)
  branch_name: string (nullable)
  plan_file: string (nullable)
  issue_class: "/feature" | "/bug" | "/chore" | "/patch" (nullable)
  worktree_path: string (nullable)
  backend_port: integer (nullable)
  frontend_port: integer (nullable)
  model_set: "base" | "heavy" (nullable)
  all_adws: array of strings
```

### 6.2 GitHub Issue Data Model

```
GitHubIssue:
  number: integer
  title: string
  body: string
  state: "open" | "closed"
  author: GitHubUser
  assignees: array of GitHubUser
  labels: array of GitHubLabel
  milestone: GitHubMilestone (nullable)
  comments: array of GitHubComment
  created_at: datetime
  updated_at: datetime
  closed_at: datetime (nullable)
  url: string
```

### 6.3 Review Result Data Model

```
ReviewResult:
  success: boolean
  review_summary: string
  review_issues: array of ReviewIssue
  screenshots: array of strings (paths)
  screenshot_urls: array of strings (R2 URLs)

ReviewIssue:
  review_issue_number: integer
  screenshot_path: string (nullable)
  screenshot_url: string (nullable)
  issue_description: string
  issue_resolution: string
  issue_severity: "skippable" | "tech_debt" | "blocker"
```

---

## 7. Integration Requirements

### 7.1 GitHub Integration

| Integration Point     | Method            | Authentication           |
|:----------------------|:------------------|:-------------------------|
| Fetch issue           | `gh issue view`   | gh auth or GITHUB_PAT    |
| Post comment          | `gh issue comment`| gh auth or GITHUB_PAT    |
| Create PR             | `gh pr create`    | gh auth or GITHUB_PAT    |
| Update PR             | `gh pr edit`      | gh auth or GITHUB_PAT    |
| Approve PR            | `gh pr review`    | gh auth or GITHUB_PAT    |
| Close issue           | `gh issue close`  | gh auth or GITHUB_PAT    |

### 7.2 Claude Code Integration

| Integration Point     | Method                | Configuration            |
|:----------------------|:----------------------|:-------------------------|
| Execute prompt        | `claude --print -p`   | ANTHROPIC_API_KEY        |
| Model selection       | `--model` flag        | base or heavy            |
| Working directory     | CLI cwd               | worktree_path            |

### 7.3 Cloudflare R2 Integration

| Integration Point     | Method                | Configuration            |
|:----------------------|:----------------------|:-------------------------|
| Upload screenshot     | boto3 S3 client       | R2 credentials           |
| Generate URL          | Bucket URL + key      | CLOUDFLARE_R2_BUCKET_NAME|

---

## 8. Success Metrics

### 8.1 Adoption Metrics

| Metric                            | Target              |
|:----------------------------------|:--------------------|
| Issues processed per month        | 100+                |
| Unique projects using ADW         | 10+                 |
| ZTE success rate                  | 80%+                |

### 8.2 Quality Metrics

| Metric                            | Target              |
|:----------------------------------|:--------------------|
| First-pass test success rate      | 70%+                |
| Review pass rate (no blockers)    | 80%+                |
| Documentation generated           | 100% of features    |

### 8.3 Efficiency Metrics

| Metric                            | Target              |
|:----------------------------------|:--------------------|
| Time from issue to PR             | <30 minutes         |
| Time from issue to merge (ZTE)    | <1 hour             |
| LLM cost per issue                | <$10                |

---

## 9. Risks and Mitigations

### 9.1 Technical Risks

| Risk                              | Likelihood | Impact | Mitigation                    |
|:----------------------------------|:-----------|:-------|:------------------------------|
| LLM hallucination in code         | Medium     | High   | Test + review phases          |
| Port conflicts                    | Low        | Medium | Hash-based allocation         |
| Worktree corruption               | Low        | High   | Validation before operations  |
| API rate limits                   | Medium     | Medium | Retry with backoff            |

### 9.2 Business Risks

| Risk                              | Likelihood | Impact | Mitigation                    |
|:----------------------------------|:-----------|:-------|:------------------------------|
| Unexpected LLM costs              | Medium     | Medium | Cost tracking in responses    |
| Incorrect auto-merge (ZTE)        | Low        | High   | State validation before ship  |
| Security issue in generated code  | Low        | High   | Review phase catches blockers |

---

## 10. Glossary

| Term           | Definition                                                      |
|:---------------|:----------------------------------------------------------------|
| ADW            | AI Developer Workflow - the framework name                      |
| ADW ID         | 8-character unique identifier for workflow instances            |
| Slash command  | Template-based command (e.g., /feature, /implement)             |
| Worktree       | Isolated git working directory for parallel execution           |
| ZTE            | Zero Touch Execution - fully automated shipping                 |
| Heavy model    | Opus-class model for complex tasks                              |
| Base model     | Sonnet-class model for simpler tasks                            |
| Blocker        | Review issue that must be resolved before shipping              |
| Tech debt      | Issue logged but not blocking current release                   |

---

## 11. Appendices

### Appendix A: File Naming Conventions

| File Type        | Pattern                                                |
|:-----------------|:-------------------------------------------------------|
| Plan file        | `specs/issue-{N}-adw-{ID}-sdlc_planner-{slug}.md`      |
| Patch plan       | `specs/patch/patch-adw-{ID}-{slug}.md`                 |
| State file       | `artifacts/{org}/{repo}/{adw-id}/adw_state.json`       |
| Documentation    | `app_docs/feature-{adw-id}-{slug}.md`                  |
| Worktree         | `artifacts/{org}/{repo}/trees/{adw-id}/`               |

### Appendix B: Branch Naming Convention

```
{type}-issue-{number}-adw-{adw_id}-{slug}
```

| Component | Description                        | Example            |
|:----------|:-----------------------------------|:-------------------|
| type      | feat, bug, or chore                | feat               |
| number    | GitHub issue number                | 42                 |
| adw_id    | 8-character workflow ID            | abc12345           |
| slug      | 3-6 words from issue title         | add-user-auth      |

**Full example:** `feat-issue-42-adw-abc12345-add-user-authentication`

### Appendix C: Commit Message Convention

```
{agent}: {type}: {message}
```

| Component | Description                        | Example            |
|:----------|:-----------------------------------|:-------------------|
| agent     | Workflow agent name                | sdlc_planner       |
| type      | feat, bug, or chore                | feat               |
| message   | Present tense, <50 chars           | add auth module    |

**Full example:** `sdlc_planner: feat: add user authentication module`

### Appendix D: GitHub Comment Triggers

| Comment Pattern       | Action                                        |
|:----------------------|:----------------------------------------------|
| `adw_plan_iso`        | Run plan workflow only                        |
| `adw_sdlc_iso`        | Run full SDLC (no ship)                       |
| `adw_sdlc_zte_iso`    | Run full SDLC with auto-ship                  |
| `model_set heavy`     | Use heavy models for all commands             |

### Appendix E: Exit Codes

| Code | Meaning                                              |
|:-----|:-----------------------------------------------------|
| 0    | Success                                              |
| 1    | Failure (missing state, validation error, etc.)      |
