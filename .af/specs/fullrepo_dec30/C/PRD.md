# ADW Framework Product Requirements Document (Claude)

**Version:** 1.0.0
**Date:** 2025-12-30
**Status:** Complete
**Product Owner:** AI Developer Workflow Team

---

## 1. Executive Summary

### 1.1 Product Vision

ADW (AI Developer Workflow) Framework transforms software development by automating the complete development lifecycle using Claude Code agents. It enables teams to process GitHub issues through automated planning, implementation, testing, review, and documentation phases, with each workflow running in isolated git worktrees for parallel execution.

### 1.2 Problem Statement

Modern software development faces several challenges:

1. **Manual process overhead**: Developers spend significant time on repetitive tasks like setting up branches, writing boilerplate, running tests, and creating documentation.

2. **Context switching**: Moving between planning, coding, testing, and review requires constant context shifts that reduce productivity.

3. **Inconsistent quality**: Without standardized workflows, code quality varies based on individual practices and available time.

4. **Parallel work conflicts**: Multiple developers working on the same repository risk merge conflicts and environment collisions.

5. **Knowledge loss**: Implementation decisions and rationale are often not captured, making future maintenance difficult.

### 1.3 Solution Overview

ADW Framework provides:

- **Automated SDLC Pipeline**: GitHub issue to merged PR with minimal human intervention
- **Isolated Execution**: Git worktrees with dedicated ports for parallel workflows
- **AI-Powered Development**: Claude Code agents execute planning, implementation, testing, and review
- **Persistent State**: Workflow progress tracked and resumable across phases
- **Flexible Triggers**: CLI, webhooks, and scheduled polling for various use cases

---

## 2. Target Users

### 2.1 Primary Personas

#### Persona 1: Solo Developer

| Attribute        | Details                                                    |
| :--------------- | :--------------------------------------------------------- |
| **Name**         | Alex                                                       |
| **Role**         | Full-stack developer                                       |
| **Context**      | Working on personal projects or small team projects        |
| **Pain Points**  | Limited time for testing and documentation; wants to ship faster |
| **Goals**        | Automate repetitive tasks; maintain code quality           |
| **ADW Usage**    | CLI-driven workflows; local development with `adw sdlc`    |

#### Persona 2: Team Lead

| Attribute        | Details                                                    |
| :--------------- | :--------------------------------------------------------- |
| **Name**         | Jordan                                                     |
| **Role**         | Engineering team lead                                      |
| **Context**      | Managing 5-10 person team; multiple parallel features      |
| **Pain Points**  | Code review bottleneck; inconsistent implementation quality |
| **Goals**        | Scale development throughput; ensure consistent practices  |
| **ADW Usage**    | Webhook triggers from GitHub; ZTE for approved issues      |

#### Persona 3: DevOps Engineer

| Attribute        | Details                                                    |
| :--------------- | :--------------------------------------------------------- |
| **Name**         | Sam                                                        |
| **Role**         | DevOps / Platform engineer                                 |
| **Context**      | Managing CI/CD pipelines; infrastructure automation        |
| **Pain Points**  | Manual steps in deployment pipelines; environment conflicts |
| **Goals**        | Fully automated pipelines; reproducible environments       |
| **ADW Usage**    | Webhook server deployment; cron-based issue polling        |

### 2.2 Secondary Personas

- **Open Source Maintainer**: Uses ADW to handle community contributions
- **Startup Founder**: Uses ADW to move fast with limited resources
- **Enterprise Architect**: Evaluates ADW for organizational adoption

---

## 3. User Stories

### 3.1 Epic: Automated Planning

#### US-001: Issue Classification

> **As a** developer
> **I want to** have issues automatically classified by type
> **So that** the appropriate planning template is selected

**Acceptance Criteria:**
1. System classifies issues as feature, bug, chore, or patch
2. Classification uses issue title, body, and labels
3. Classification completes in < 5 seconds
4. Invalid issues return explicit error

---

#### US-002: Branch Name Generation

> **As a** developer
> **I want to** have branch names generated from issue details
> **So that** branches follow consistent naming conventions

**Acceptance Criteria:**
1. Branch format: `<type>-issue-<number>-adw-<id>-<slug>`
2. Slug derived from issue title (3-6 words, hyphenated)
3. Type matches classification (feat, bug, chore)
4. Branch name is unique per issue

---

#### US-003: Implementation Plan Creation

> **As a** developer
> **I want to** receive a detailed implementation plan
> **So that** I understand the full scope before coding begins

**Acceptance Criteria:**
1. Plan includes problem statement, solution approach, and phased tasks
2. Plan identifies relevant files and their purposes
3. Plan includes testing strategy and acceptance criteria
4. Plan saved to `specs/` directory with descriptive filename
5. Plan posted as collapsible comment on GitHub issue

---

### 3.2 Epic: Isolated Execution

#### US-004: Worktree Creation

> **As a** developer
> **I want to** have each workflow run in an isolated worktree
> **So that** multiple workflows can run in parallel without conflicts

**Acceptance Criteria:**
1. Worktree created at `trees/<adw_id>/`
2. Feature branch checked out in worktree
3. Worktree contains full project structure
4. Main repository remains untouched during execution

---

#### US-005: Port Allocation

> **As a** developer running multiple workflows
> **I want to** have unique ports assigned to each workflow
> **So that** applications don't conflict with each other

**Acceptance Criteria:**
1. Backend port assigned from 9100-9114 range
2. Frontend port assigned from 9200-9214 range
3. Ports are deterministic based on ADW ID
4. Fallback to next available port if collision detected
5. Ports saved to `.ports.env` for script access

---

#### US-006: Worktree Environment Setup

> **As a** developer
> **I want to** have the worktree fully configured for development
> **So that** the application runs correctly in isolation

**Acceptance Criteria:**
1. Dependencies installed via `uv sync` / `npm install`
2. Environment files copied and configured
3. Database reset if reset script exists
4. Port configuration applied to all configs

---

### 3.3 Epic: Automated Implementation

#### US-007: Plan Execution

> **As a** developer
> **I want to** have the implementation plan automatically executed
> **So that** code is written according to the plan

**Acceptance Criteria:**
1. Plan file read from state
2. Each task in plan executed in order
3. Implementation follows existing patterns in codebase
4. Changes committed to feature branch
5. Implementation report posted to issue

---

#### US-008: Implementation Commit

> **As a** developer
> **I want to** have implementation changes committed with clear messages
> **So that** the git history is meaningful

**Acceptance Criteria:**
1. Commit message references issue number
2. Commit message describes changes made
3. All new and modified files included
4. Commit pushed to remote branch
5. PR updated with latest changes

---

### 3.4 Epic: Automated Testing

#### US-009: Test Suite Execution

> **As a** developer
> **I want to** have tests run automatically after implementation
> **So that** I know if the code works correctly

**Acceptance Criteria:**
1. Unit tests executed via configured test command
2. Test results parsed into structured format
3. Pass/fail count reported
4. Detailed results posted to GitHub issue

---

#### US-010: Test Failure Resolution

> **As a** developer
> **I want to** have failing tests automatically fixed
> **So that** I don't need to manually debug each failure

**Acceptance Criteria:**
1. Each failing test analyzed for root cause
2. Fix attempted via `/resolve_failed_test` command
3. Test re-run after fix attempt
4. Maximum 4 retry attempts before accepting failures
5. Resolution status reported per test

---

#### US-011: E2E Test Execution

> **As a** developer
> **I want to** have end-to-end tests validate UI functionality
> **So that** user-facing features work correctly

**Acceptance Criteria:**
1. E2E tests executed via Playwright MCP
2. Application started with correct port configuration
3. Screenshots captured for test evidence
4. Maximum 2 retry attempts for E2E failures
5. E2E can be skipped with `--skip-e2e` flag

---

### 3.5 Epic: Automated Review

#### US-012: Spec Compliance Review

> **As a** developer
> **I want to** have implementation validated against the plan
> **So that** the code meets requirements

**Acceptance Criteria:**
1. Spec file located from branch name
2. Git diff analyzed against spec requirements
3. Each acceptance criterion verified
4. Review success/failure determined

---

#### US-013: Visual Review

> **As a** developer
> **I want to** see screenshots of the implemented feature
> **So that** I can verify the UI looks correct

**Acceptance Criteria:**
1. Application started and navigated to feature
2. 1-5 critical screenshots captured
3. Screenshots saved to `review_img/` directory
4. Screenshots posted to GitHub issue
5. Descriptive filenames (e.g., `01_login_screen.png`)

---

#### US-014: Issue Identification

> **As a** developer
> **I want to** know about any issues found during review
> **So that** I can address them before merging

**Acceptance Criteria:**
1. Issues categorized as: skippable, tech_debt, blocker
2. Each issue includes description and suggested resolution
3. Blocker issues prevent automatic merge
4. Issues reported in structured JSON format

---

### 3.6 Epic: Documentation

#### US-015: Feature Documentation

> **As a** developer
> **I want to** have documentation generated for new features
> **So that** future developers understand what was built

**Acceptance Criteria:**
1. Documentation created at `app_docs/feature-<id>-<name>.md`
2. Content based on git diff and spec file
3. Includes: overview, what was built, how to use, testing
4. Review screenshots included in documentation
5. Conditional docs index updated

---

### 3.7 Epic: Zero-Touch Execution

#### US-016: Automatic PR Merge

> **As a** team lead
> **I want to** have PRs automatically merged when all checks pass
> **So that** approved features ship without manual intervention

**Acceptance Criteria:**
1. All tests must pass
2. No blocker issues from review
3. PR approved via `gh pr review --approve`
4. PR merged via squash merge
5. Only enabled for ZTE workflows

---

### 3.8 Epic: Trigger Mechanisms

#### US-017: CLI Invocation

> **As a** developer
> **I want to** trigger workflows from the command line
> **So that** I can integrate ADW into my local workflow

**Acceptance Criteria:**
1. Commands: `plan`, `build`, `test`, `review`, `document`, `sdlc`, `zte`
2. Issue number as required argument
3. Optional ADW ID for resuming workflows
4. Flags: `--skip-e2e`, `--skip-resolution`
5. Help text available via `--help`

---

#### US-018: GitHub Webhook Trigger

> **As a** team lead
> **I want to** trigger workflows via issue comments
> **So that** team members can start workflows from GitHub

**Acceptance Criteria:**
1. Comment parsed for magic keywords
2. Keywords: `adw_plan_iso`, `adw_sdlc_iso`, `adw_sdlc_zte_iso`
3. Optional `model_set heavy` for complex tasks
4. Workflow spawned as background process
5. Webhook signature verified

---

#### US-019: Workflow Resumption

> **As a** developer
> **I want to** resume interrupted workflows
> **So that** I don't lose progress after failures

**Acceptance Criteria:**
1. ADW ID passed to resume workflow
2. State loaded from existing state file
3. Completed phases skipped
4. Current phase resumed from last checkpoint
5. Worktree reused if still valid

---

### 3.9 Epic: State Management

#### US-020: Persistent State

> **As a** developer
> **I want to** have workflow state persisted
> **So that** I can track progress and debug issues

**Acceptance Criteria:**
1. State saved to `artifacts/{id}/adw_state.json`
2. State updated after each significant action
3. Fields: adw_id, issue_number, branch_name, plan_file, etc.
4. State loadable by ADW ID
5. State posted to issue for visibility

---

#### US-021: Artifact Organization

> **As a** developer
> **I want to** have all artifacts organized by workflow
> **So that** I can find outputs easily

**Acceptance Criteria:**
1. Directory structure: `artifacts/{org}/{repo}/{adw_id}/`
2. Agent outputs in named subdirectories
3. Prompts saved with timestamps
4. Raw JSONL output preserved
5. Screenshots organized by phase

---

### 3.10 Epic: Configuration

#### US-022: Project Configuration

> **As a** developer
> **I want to** configure ADW for my project
> **So that** it works with my project structure

**Acceptance Criteria:**
1. Configuration in `.adw.yaml`
2. Required: project_id
3. Optional: artifacts_dir, ports, source_root, commands
4. App-specific: backend_dir, frontend_dir, test_command
5. Validation on load

---

#### US-023: Environment Configuration

> **As a** developer
> **I want to** configure secrets via environment variables
> **So that** credentials are not committed to code

**Acceptance Criteria:**
1. `.env` file loaded via python-dotenv
2. Required: ANTHROPIC_API_KEY
3. Optional: GITHUB_PAT (falls back to gh auth)
4. Safe environment filtering for subprocesses

---

---

## 4. Feature Specifications

### 4.1 Feature: SDLC Pipeline

| Attribute            | Value                                                   |
| :------------------- | :------------------------------------------------------ |
| **Feature ID**       | F-001                                                   |
| **Priority**         | P0 (Critical)                                           |
| **User Stories**     | US-001 through US-016                                   |
| **Description**      | Complete automated SDLC from issue to merged PR         |

**Workflow:**
1. **Plan**: Issue -> Classification -> Branch -> Worktree -> Plan File -> PR
2. **Build**: Plan File -> Implementation -> Commit -> Push
3. **Test**: Run Tests -> Resolve Failures -> Retry -> Report
4. **Review**: Validate Spec -> Capture Screenshots -> Report Issues
5. **Document**: Generate Docs -> Update Index
6. **Ship** (ZTE only): Approve -> Merge

**Success Metrics:**
- Issue-to-PR time < 30 minutes for typical features
- Test pass rate > 90% after resolution attempts
- Review accuracy > 95% (issues correctly identified)

---

### 4.2 Feature: Isolated Worktrees

| Attribute            | Value                                                   |
| :------------------- | :------------------------------------------------------ |
| **Feature ID**       | F-002                                                   |
| **Priority**         | P0 (Critical)                                           |
| **User Stories**     | US-004, US-005, US-006                                  |
| **Description**      | Parallel execution in isolated git worktrees            |

**Capabilities:**
- Create worktree with dedicated branch
- Allocate unique backend/frontend ports
- Setup complete development environment
- Cleanup worktree after completion

**Success Metrics:**
- Support 15 concurrent workflows (port range)
- Zero cross-workflow conflicts
- Worktree creation < 30 seconds

---

### 4.3 Feature: Test Resolution

| Attribute            | Value                                                   |
| :------------------- | :------------------------------------------------------ |
| **Feature ID**       | F-003                                                   |
| **Priority**         | P1 (High)                                               |
| **User Stories**     | US-010, US-011                                          |
| **Description**      | Automatic identification and resolution of test failures |

**Algorithm:**
1. Run test suite
2. Parse failures into structured format
3. For each failure:
   a. Analyze root cause
   b. Attempt fix via agent
   c. Mark as resolved or unresolved
4. Re-run tests if any resolved
5. Repeat up to max attempts

**Success Metrics:**
- Resolve > 70% of initial failures
- Max 4 retry loops for unit tests
- Max 2 retry loops for E2E tests

---

### 4.4 Feature: Visual Review

| Attribute            | Value                                                   |
| :------------------- | :------------------------------------------------------ |
| **Feature ID**       | F-004                                                   |
| **Priority**         | P1 (High)                                               |
| **User Stories**     | US-012, US-013, US-014                                  |
| **Description**      | Visual validation of implemented features               |

**Capabilities:**
- Start application with correct ports
- Navigate to feature locations
- Capture screenshots of critical paths
- Compare against spec requirements
- Identify visual and functional issues

**Success Metrics:**
- 1-5 screenshots per review (focused)
- Screenshot capture success > 95%
- Issue severity correctly categorized

---

### 4.5 Feature: Multi-Trigger Support

| Attribute            | Value                                                   |
| :------------------- | :------------------------------------------------------ |
| **Feature ID**       | F-005                                                   |
| **Priority**         | P1 (High)                                               |
| **User Stories**     | US-017, US-018, US-019                                  |
| **Description**      | Invoke workflows via CLI, webhooks, or cron             |

**Trigger Types:**
| Trigger   | Use Case                          | Authentication          |
| :-------- | :-------------------------------- | :---------------------- |
| CLI       | Local development                 | Local env vars          |
| Webhook   | GitHub integration                | Webhook secret + PAT    |
| Cron      | Scheduled processing              | Server env vars         |

**Success Metrics:**
- CLI response time < 1 second
- Webhook processing < 5 seconds
- Cron polling configurable interval

---

## 5. Success Metrics

### 5.1 Primary KPIs

| Metric                        | Target           | Measurement                          |
| :---------------------------- | :--------------- | :----------------------------------- |
| Issue-to-PR Time              | < 30 minutes     | Timestamp diff: issue created to PR  |
| SDLC Success Rate             | > 85%            | Workflows completing all phases      |
| Test Resolution Rate          | > 70%            | Failures resolved / total failures   |
| Review Accuracy               | > 95%            | Correct issue identification         |
| Zero-Touch Merge Rate         | > 60%            | ZTE workflows merged without manual  |

### 5.2 Secondary KPIs

| Metric                        | Target           | Measurement                          |
| :---------------------------- | :--------------- | :----------------------------------- |
| Agent Cost per Workflow       | < $2.00          | JSONL cost extraction                |
| Parallel Workflow Capacity    | 15 concurrent    | Port range utilization               |
| State Recovery Rate           | 100%             | Successful workflow resumptions      |
| Documentation Coverage        | > 80%            | Features with generated docs         |

---

## 6. Non-Functional Requirements

### 6.1 Performance

| Requirement                   | Target           |
| :---------------------------- | :--------------- |
| Classification Latency        | < 5 seconds      |
| Plan Generation               | < 3 minutes      |
| Implementation (typical)      | < 10 minutes     |
| Test Execution                | < 5 minutes      |
| Review Execution              | < 5 minutes      |
| Documentation Generation      | < 2 minutes      |

### 6.2 Reliability

| Requirement                   | Target           |
| :---------------------------- | :--------------- |
| State Persistence             | 100% (no data loss) |
| Crash Recovery                | Resume from last save |
| Git Operation Success         | > 99%            |
| Agent Execution Success       | > 95%            |

### 6.3 Scalability

| Requirement                   | Target           |
| :---------------------------- | :--------------- |
| Concurrent Workflows          | 15 per project   |
| State File Size               | < 1 MB           |
| Artifact Storage              | < 100 MB per workflow |
| Log Retention                 | 30 days          |

### 6.4 Security

| Requirement                   | Implementation   |
| :---------------------------- | :--------------- |
| Secret Management             | .env files, filtered subprocess env |
| Webhook Authentication        | HMAC signature verification |
| Repository Access             | gh auth or GITHUB_PAT |
| Agent Sandboxing              | Worktree isolation |

---

## 7. Roadmap

### 7.1 Current State (v0.1.0)

**Completed:**
- Core SDLC pipeline (plan -> build -> test -> review -> document)
- Isolated worktree execution
- CLI and webhook triggers
- State persistence and recovery
- Test resolution with retry logic
- Visual review with screenshots
- Documentation generation

**Known Limitations:**
- Single project per ADW instance
- No parallel phase execution within workflow
- Manual worktree cleanup required
- Limited to Python/TypeScript projects

### 7.2 Near-Term (v0.2.0)

**Planned:**
- Automatic worktree cleanup
- Multi-project support
- Enhanced model selection (per-command override)
- Improved E2E test reliability
- Webhook dashboard for monitoring

### 7.3 Medium-Term (v0.3.0)

**Planned:**
- Parallel phase execution (test + review)
- Custom workflow definitions
- Plugin system for triggers
- Cost tracking and budgeting
- Team collaboration features

### 7.4 Long-Term (v1.0.0)

**Vision:**
- Multi-repository orchestration
- AI-assisted code review (beyond spec validation)
- Self-healing pipelines
- Learning from historical workflows
- Enterprise SSO integration

---

## 8. Glossary

| Term                    | Definition                                              |
| :---------------------- | :------------------------------------------------------ |
| **ADW**                 | AI Developer Workflow - the framework name              |
| **ADW ID**              | 8-character unique identifier for a workflow instance   |
| **Worktree**            | Isolated git working directory for parallel execution   |
| **Phase**               | Single step in SDLC (plan, build, test, review, etc.)   |
| **Pipeline**            | Complete sequence of phases for issue processing        |
| **ZTE**                 | Zero-Touch Execution - fully automated merge            |
| **Slash Command**       | Template-based agent instruction (e.g., `/implement`)   |
| **State**               | Persistent JSON tracking workflow progress              |
| **Artifact**            | Output file from workflow (logs, screenshots, etc.)     |
| **Model Set**           | Agent model selection (base=Sonnet, heavy=Opus)         |

---

## 9. Appendix

### A. Command Reference

| Command             | Description                           | Model  |
| :------------------ | :------------------------------------ | :----- |
| `/feature`          | Create feature implementation plan    | opus   |
| `/bug`              | Create bug fix plan                   | opus   |
| `/chore`            | Create maintenance plan               | opus   |
| `/patch`            | Create focused patch plan             | opus   |
| `/implement`        | Execute plan                          | opus   |
| `/test`             | Run test suite                        | sonnet |
| `/test_e2e`         | Run E2E tests                         | sonnet |
| `/resolve_failed_test` | Fix failing test                   | sonnet |
| `/review`           | Validate against spec                 | sonnet |
| `/document`         | Generate documentation                | opus   |
| `/classify_issue`   | Classify issue type                   | haiku  |
| `/classify_and_branch` | Classify + generate branch         | haiku  |

### B. Webhook Keywords

| Keyword                 | Workflow                              |
| :---------------------- | :------------------------------------ |
| `adw_plan_iso`          | Plan phase only                       |
| `adw_build_iso`         | Build phase only                      |
| `adw_test_iso`          | Test phase only                       |
| `adw_review_iso`        | Review phase only                     |
| `adw_document_iso`      | Document phase only                   |
| `adw_ship_iso`          | Ship phase only                       |
| `adw_sdlc_iso`          | Full SDLC (no auto-merge)             |
| `adw_sdlc_zte_iso`      | Full SDLC with auto-merge             |
| `model_set heavy`       | Use Opus for all agents               |

### C. State Schema

```json
{
  "adw_id": "abc12345",
  "issue_number": "42",
  "branch_name": "feat-issue-42-adw-abc12345-add-auth",
  "plan_file": "specs/issue-42-adw-abc12345-add-auth.md",
  "issue_class": "/feature",
  "worktree_path": "/path/to/trees/abc12345",
  "backend_port": 9100,
  "frontend_port": 9200,
  "model_set": "base",
  "adw_workflow_history": ["adw_plan_iso", "adw_build_iso", "adw_test_iso"]
}
```

---

*End of Product Requirements Document*
