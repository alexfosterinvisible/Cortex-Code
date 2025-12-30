# ADW Framework - Product Requirements Document (Claude)

**Version**: 1.0.0
**Date**: 2025-12-30
**Purpose**: Complete product definition for rebuilding the ADW Framework from scratch

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Statement](#problem-statement)
3. [Solution Overview](#solution-overview)
4. [User Personas](#user-personas)
5. [User Workflows](#user-workflows)
6. [Feature Specifications](#feature-specifications)
7. [CLI Reference](#cli-reference)
8. [Configuration Reference](#configuration-reference)
9. [Slash Command Reference](#slash-command-reference)
10. [Integration Points](#integration-points)
11. [Success Criteria](#success-criteria)
12. [Non-Functional Requirements](#non-functional-requirements)
13. [Glossary](#glossary)

---

## Executive Summary

**ADW (AI Developer Workflow)** is an orchestration framework that automates software development using Claude Code agents in isolated git worktrees. It transforms GitHub issues into working, tested, reviewed, and documented code through a complete Software Development Life Cycle (SDLC) pipeline.

**Key Value Proposition**: Developers can create a GitHub issue describing a feature, bug fix, or chore, then run a single command to have an AI agent plan, implement, test, review, and document the change - all in an isolated environment that doesn't interfere with other work.

**Target Users**: Development teams using GitHub for issue tracking who want to accelerate development with AI assistance while maintaining quality through automated testing and review.

---

## Problem Statement

### Current Pain Points

1. **Manual Development Overhead**: Developers spend significant time on routine tasks:
   - Reading issue requirements and planning implementation
   - Writing boilerplate code and tests
   - Running tests and fixing failures
   - Conducting code reviews
   - Writing documentation

2. **Context Switching**: Moving between issues requires:
   - Stashing or committing work-in-progress
   - Switching branches
   - Waiting for environment setup
   - Risk of cross-contamination between tasks

3. **Inconsistent Quality**: Without structured process:
   - Tests may be skipped under time pressure
   - Documentation often neglected
   - Review quality varies

4. **Lack of Visibility**: When automation runs:
   - Progress is opaque
   - Failures are hard to diagnose
   - No audit trail of decisions

### Problem Scope

ADW addresses these problems for:
- **Feature development**: New functionality from issue description
- **Bug fixes**: Debugging and fixing reported issues
- **Chores**: Maintenance tasks, refactoring, dependency updates

ADW does NOT address:
- Architectural decisions (requires human judgment)
- Security-critical code (requires human review)
- Performance optimization (requires benchmarking)
- Large-scale refactoring (exceeds single-issue scope)

---

## Solution Overview

### Core Concept

ADW orchestrates Claude Code agents through a structured SDLC pipeline:

```
GitHub Issue → Plan → Build → Test → Review → Document → PR Ready
```

Each phase runs in an **isolated git worktree** with dedicated ports, enabling parallel execution without interference.

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **Automated Planning** | AI reads issue, classifies type, generates implementation plan |
| **Isolated Execution** | Each workflow runs in separate git worktree |
| **Self-Healing Tests** | Failed tests trigger automatic resolution attempts |
| **Visual Review** | Screenshots captured and uploaded for verification |
| **Progress Visibility** | All steps posted to GitHub issue as comments |
| **Resumable Workflows** | State persisted for resumption after failures |

### Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                     ADW Framework                            │
├─────────────────────────────────────────────────────────────┤
│  CLI → Workflows → Agent Execution → Integrations           │
├─────────────────────────────────────────────────────────────┤
│  State Management │ Git Worktrees │ Port Allocation         │
└─────────────────────────────────────────────────────────────┘
```

---

## User Personas

### Primary Persona: Development Team Lead

**Name**: Alex (they/them)
**Role**: Engineering Lead at a SaaS company
**Goals**:
- Accelerate feature development without sacrificing quality
- Maintain consistent development practices across team
- Reduce time spent on routine code reviews
- Keep documentation up-to-date

**Frustrations**:
- Team spends too much time on boilerplate
- Junior developers' PRs need extensive review
- Documentation always lags behind features
- Context switching slows everyone down

**Use of ADW**:
- Configures ADW for team's repositories
- Runs `adw sdlc` for new issues
- Reviews AI-generated PRs
- Uses output as teaching material for juniors

### Secondary Persona: Solo Developer

**Name**: Sam (he/him)
**Role**: Indie developer / Freelancer
**Goals**:
- Ship features quickly as a one-person team
- Maintain quality despite time pressure
- Avoid getting stuck on implementation details
- Keep clients informed of progress

**Frustrations**:
- Can't afford to spend hours on each feature
- Often skips tests due to time constraints
- Documentation is an afterthought
- Debugging alone is time-consuming

**Use of ADW**:
- Runs `adw zte` for zero-touch execution
- Lets AI handle implementation while focusing on design
- Uses GitHub issue comments to show clients progress
- Reviews PRs before merging

### Tertiary Persona: DevOps Engineer

**Name**: Jordan (she/her)
**Role**: Platform Engineer
**Goals**:
- Automate repetitive infrastructure tasks
- Standardize development workflows
- Enable self-service for development teams
- Reduce support requests

**Frustrations**:
- Developers ask for help with routine changes
- Configuration drift across repositories
- Inconsistent CI/CD across projects

**Use of ADW**:
- Sets up webhook triggers for automatic execution
- Configures ADW across multiple repositories
- Uses cron trigger for maintenance tasks
- Monitors workflow execution via GitHub

---

## User Workflows

### Workflow 1: Full SDLC from Issue

**Trigger**: Developer creates GitHub issue describing feature/bug/chore

**Steps**:

1. **Create Issue**
   ```markdown
   Title: Add dark mode toggle to settings page

   ## Description
   Users should be able to toggle between light and dark mode
   from the settings page.

   ## Requirements
   - Toggle switch in settings
   - Preference persisted to localStorage
   - Theme applied immediately without page refresh
   ```

2. **Run ADW SDLC**
   ```bash
   uv run adw sdlc 42
   ```

3. **Monitor Progress** (automated)
   - ADW posts comments to issue #42 showing each phase
   - Plan appears as collapsible block
   - Test results summarized
   - Screenshots uploaded for review

4. **Review PR**
   - PR created with implementation
   - PR body contains review summary
   - Screenshots embedded
   - All tests passing

5. **Merge or Request Changes**
   - If approved: merge PR
   - If changes needed: comment on PR, re-run affected phases

**Expected Duration**: 10-30 minutes depending on complexity

### Workflow 2: Zero-Touch Execution

**Trigger**: High-confidence issue with clear requirements

**Steps**:

1. **Create Issue** (same as Workflow 1)

2. **Run ZTE**
   ```bash
   uv run adw zte 42
   ```

3. **Await Completion**
   - ADW runs full SDLC
   - On success, automatically approves and merges PR
   - Issue receives completion notification

4. **Verify** (optional)
   - Review merged code
   - Check deployed changes

**Expected Duration**: 15-45 minutes

### Workflow 3: Iterative Development

**Trigger**: Complex issue requiring multiple iterations

**Steps**:

1. **Plan Only**
   ```bash
   uv run adw plan 42
   ```
   - Review plan in PR
   - Modify plan if needed (manual edit)

2. **Build**
   ```bash
   uv run adw build 42 abc12345
   ```
   - Implementation based on approved plan

3. **Test**
   ```bash
   uv run adw test 42 abc12345 --skip-e2e
   ```
   - Run unit tests only initially

4. **Review**
   ```bash
   uv run adw review 42 abc12345 --skip-resolution
   ```
   - Manual review of blockers

5. **Iterate** (as needed)
   - Run specific phases with same ADW ID
   - State persists between runs

### Workflow 4: Quick Patch

**Trigger**: Small, urgent fix needed

**Steps**:

1. **Create Issue** (brief description)
   ```markdown
   Title: Fix typo in login page

   The word "pasword" should be "password"
   ```

2. **Run Patch**
   ```bash
   uv run adw patch 43
   ```
   - Lightweight workflow
   - Skips extensive planning
   - Direct implementation

3. **Review and Merge**
   - Quick PR for small change

**Expected Duration**: 5-10 minutes

### Workflow 5: Webhook Automation

**Trigger**: GitHub issue comment containing trigger phrase

**Steps**:

1. **Configure Webhook**
   - Deploy `trigger_webhook.py` FastAPI app
   - Configure GitHub webhook to POST to endpoint

2. **Trigger via Comment**
   ```markdown
   adw_sdlc_iso
   ```

3. **Automatic Execution**
   - Webhook receives event
   - Extracts issue number and command
   - Runs appropriate workflow

4. **Monitor via GitHub**
   - All progress on issue
   - No terminal access needed

---

## Feature Specifications

### F001: Issue Classification

**Description**: Automatically classify GitHub issues as feature, bug, or chore.

**Input**: GitHub issue with title and body

**Output**: SlashCommand (`/feature`, `/bug`, `/chore`)

**Behavior**:
1. Fetch issue details via gh CLI
2. Call `/classify_and_branch` agent command
3. Parse response for classification
4. Store in state as `issue_class`

**Classification Criteria**:
- **Feature**: New functionality, enhancements, user-facing additions
- **Bug**: Defects, errors, unexpected behavior, regressions
- **Chore**: Maintenance, refactoring, dependency updates, cleanup

### F002: Branch Name Generation

**Description**: Generate standardized branch names for issues.

**Format**: `{type}-issue-{number}-adw-{adw_id}-{description}`

**Examples**:
- `feature-issue-42-adw-abc12345-add-dark-mode-toggle`
- `fix-issue-43-adw-def67890-typo-in-login-page`
- `chore-issue-44-adw-ghi11111-update-dependencies`

**Constraints**:
- Lowercase
- Kebab-case
- Description max 50 chars
- Total max 100 chars

### F003: Git Worktree Creation

**Description**: Create isolated git worktree for workflow execution.

**Location**: `artifacts/{project_id}/trees/{adw_id}/`

**Process**:
1. Calculate target path
2. Run `git worktree add {path} -b {branch}` (or checkout existing branch)
3. Verify worktree created
4. Store path in state

**Cleanup**: `git worktree remove {path}` via cleanup command

### F004: Port Allocation

**Description**: Assign unique ports for services in isolated environments.

**Ranges**:
- Backend: 9100-9114 (15 ports)
- Frontend: 9200-9214 (15 ports)

**Algorithm**:
```python
hash_val = hash(adw_id) % 15
backend_port = 9100 + hash_val
frontend_port = 9200 + hash_val
```

**Fallback**: If ports in use, scan for next available pair.

### F005: Implementation Planning

**Description**: Generate detailed implementation plan from issue.

**Output**: Markdown file at `specs/issue-{number}-adw-{adw_id}-{description}.md`

**Contents**:
- Issue summary
- Technical approach
- Files to create/modify
- Step-by-step implementation guide
- Testing considerations
- Edge cases

**Commands Used**: `/feature`, `/bug`, or `/chore` based on classification

### F006: Plan Implementation

**Description**: Execute implementation according to plan.

**Input**: Plan file path from state

**Process**:
1. Read plan file
2. Execute `/implement` agent command with plan
3. Agent creates/modifies files
4. Capture implementation report

**Output**: Modified source files in worktree

### F007: Test Execution with Resolution

**Description**: Run tests and automatically fix failures.

**Unit Tests**:
- Command: `/test`
- Max retries: 4 (MAX_TEST_RETRY_ATTEMPTS)
- Resolution: `/resolve_failed_test`

**E2E Tests** (optional):
- Command: `/test_e2e`
- Max retries: 2 (MAX_E2E_TEST_RETRY_ATTEMPTS)
- Resolution: `/resolve_failed_e2e_test`
- Skip flag: `--skip-e2e`

**Resolution Loop**:
```
Run tests → Parse results → If failures:
  → Call resolution command
  → Commit fix
  → Re-run tests
  → Repeat until success or max retries
```

### F008: Implementation Review

**Description**: Review implementation against issue requirements.

**Process**:
1. Execute `/review` with original issue
2. Capture result as ReviewResult
3. Identify blocker issues
4. Capture screenshots
5. Upload screenshots to R2
6. Update PR body with summary

**Resolution** (optional):
- Max retries: 3 (MAX_REVIEW_RETRY_ATTEMPTS)
- Command: `/resolve_review_blocker`
- Skip flag: `--skip-resolution`

**Review Categories**:
- **Blockers**: Must be fixed before merge
- **Suggestions**: Optional improvements
- **Approved**: No issues found

### F009: Documentation Generation

**Description**: Generate documentation for implemented features.

**Process**:
1. Execute `/document` command
2. Agent generates appropriate documentation
3. Commit documentation to branch

**Documentation Types**:
- README updates
- API documentation
- Usage examples
- Changelog entries

### F010: PR Management

**Description**: Create and manage pull requests.

**Creation**:
- Title from commit message
- Body with issue reference
- Base branch: main/master

**Updates**:
- Review summary added
- Test results appended
- Screenshots embedded

**Merge** (ship/zte):
- Approve via `gh pr review --approve`
- Merge via `gh pr merge --merge`

### F011: State Persistence

**Description**: Persist workflow state across phases.

**Location**: `artifacts/{project_id}/{adw_id}/adw_state.json`

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| adw_id | string | Unique workflow identifier |
| issue_number | string | GitHub issue number |
| branch_name | string | Git branch name |
| plan_file | string | Path to plan file |
| issue_class | string | /feature, /bug, /chore |
| worktree_path | string | Absolute path to worktree |
| backend_port | int | Allocated backend port |
| frontend_port | int | Allocated frontend port |
| model_set | string | "base" or "heavy" |
| all_adws | list | Workflow execution history |

### F012: Progress Reporting

**Description**: Report workflow progress to GitHub issue.

**Comment Format**:
```markdown
**[ADW: {adw_id}]** [{agent}] {emoji} {message}
```

**Examples**:
```markdown
**[ADW: abc12345]** [ops] ✅ Starting isolated planning phase
**[ADW: abc12345]** [planner] ✅ Implementation plan created
**[ADW: abc12345]** [tester] ⚠️ Tests failed, attempting resolution...
```

**Artifacts Posted**:
- Plans (collapsible)
- Implementation reports (collapsible)
- Test summaries
- Review results
- State snapshots

---

## CLI Reference

### Global Options

| Option | Description |
|--------|-------------|
| `--help` | Show help message |
| `--version` | Show version |

### Commands

#### `adw sdlc <issue-number> [adw-id] [--skip-e2e] [--skip-resolution]`

Run complete SDLC pipeline.

| Argument | Required | Description |
|----------|----------|-------------|
| issue-number | Yes | GitHub issue number |
| adw-id | No | Existing ADW ID to resume |
| --skip-e2e | No | Skip E2E tests |
| --skip-resolution | No | Skip automatic blocker resolution |

**Example**:
```bash
uv run adw sdlc 42
uv run adw sdlc 42 abc12345 --skip-e2e
```

#### `adw plan <issue-number> [adw-id]`

Run planning phase only.

**Example**:
```bash
uv run adw plan 42
```

#### `adw build <issue-number> <adw-id>`

Run build phase (requires prior plan).

**Example**:
```bash
uv run adw build 42 abc12345
```

#### `adw test <issue-number> <adw-id> [--skip-e2e]`

Run test phase.

**Example**:
```bash
uv run adw test 42 abc12345 --skip-e2e
```

#### `adw review <issue-number> <adw-id> [--skip-resolution]`

Run review phase.

**Example**:
```bash
uv run adw review 42 abc12345
```

#### `adw document <issue-number> <adw-id>`

Run documentation phase.

**Example**:
```bash
uv run adw document 42 abc12345
```

#### `adw ship <issue-number> <adw-id>`

Approve and merge PR.

**Example**:
```bash
uv run adw ship 42 abc12345
```

#### `adw zte <issue-number> [adw-id]`

Zero-touch execution (SDLC + auto-merge).

**Example**:
```bash
uv run adw zte 42
```

#### `adw patch <issue-number> [adw-id]`

Lightweight patch workflow.

**Example**:
```bash
uv run adw patch 43
```

#### `adw cleanup <adw-id>`

Remove worktree and optionally artifacts.

**Example**:
```bash
uv run adw cleanup abc12345
```

---

## Configuration Reference

### .adw.yaml

Project configuration file at repository root.

```yaml
# Project identifier (auto-detected from git remote if omitted)
project_id: "org/repo"

# Where artifacts and worktrees are stored
artifacts_dir: "./artifacts"

# Source code root (for agent context)
source_root: "./src"

# Port allocation ranges
ports:
  backend_start: 9100
  frontend_start: 9200

# Command template directories (in priority order)
commands:
  - "${ADW_FRAMEWORK}/commands"    # Framework defaults
  - ".claude/commands"             # Project overrides
```

### .env

Environment variables (gitignored).

```bash
# Required: Anthropic API key for Claude Code
ANTHROPIC_API_KEY=sk-ant-xxx

# Optional: GitHub token (uses gh auth if not set)
GITHUB_PAT=ghp_xxx

# Optional: Path to Claude Code CLI
CLAUDE_CODE_PATH=claude
```

### Directory Structure

```
project/
├── .adw.yaml                      # ADW configuration
├── .env                           # Credentials (gitignored)
├── .claude/
│   └── commands/                  # Project-specific commands
├── artifacts/
│   └── {org}/{repo}/
│       ├── {adw-id}/
│       │   ├── adw_state.json     # Workflow state
│       │   ├── {agent}/
│       │   │   ├── prompts/       # Saved prompts
│       │   │   └── raw_output.jsonl
│       │   └── ...
│       └── trees/
│           └── {adw-id}/          # Git worktree
├── specs/
│   └── issue-{num}-adw-{id}-*.md  # Implementation plans
└── src/                           # Source code
```

---

## Slash Command Reference

### Planning Commands

| Command | Model | Description |
|---------|-------|-------------|
| `/feature` | heavy | Generate feature implementation plan |
| `/bug` | heavy | Generate bug fix plan |
| `/chore` | heavy | Generate maintenance task plan |

### Classification Commands

| Command | Model | Description |
|---------|-------|-------------|
| `/classify_issue` | base | Classify issue as feature/bug/chore |
| `/generate_branch_name` | base | Generate branch name from issue |
| `/classify_and_branch` | base | Combined classify + branch name |

### Implementation Commands

| Command | Model | Description |
|---------|-------|-------------|
| `/implement` | heavy | Execute implementation from plan |
| `/patch` | heavy | Quick implementation for small changes |

### Testing Commands

| Command | Model | Description |
|---------|-------|-------------|
| `/test` | base | Run unit tests |
| `/test_e2e` | base | Run end-to-end tests |
| `/resolve_failed_test` | base | Fix failed unit test |
| `/resolve_failed_e2e_test` | base | Fix failed E2E test |

### Review Commands

| Command | Model | Description |
|---------|-------|-------------|
| `/review` | base | Review implementation against spec |
| `/resolve_review_blocker` | base | Fix blocker issue |

### Documentation Commands

| Command | Model | Description |
|---------|-------|-------------|
| `/document` | heavy | Generate feature documentation |

### Git Commands

| Command | Model | Description |
|---------|-------|-------------|
| `/commit` | base | Generate commit message |
| `/pull_request` | base | Create/update PR |

### Worktree Commands

| Command | Model | Description |
|---------|-------|-------------|
| `/install_worktree` | base | Set up worktree environment |
| `/cleanup_worktrees` | base | Remove specified worktrees |

---

## Integration Points

### GitHub Integration

**Authentication**:
- Uses `gh auth` (preferred)
- Falls back to `GITHUB_PAT` environment variable

**APIs Used** (via gh CLI):
- `gh issue view` - Fetch issue details
- `gh issue comment` - Post progress comments
- `gh pr create` - Create pull requests
- `gh pr edit` - Update PR body
- `gh pr review` - Approve PRs
- `gh pr merge` - Merge PRs

### Git Integration

**Commands Used**:
- `git remote get-url origin` - Get repository URL
- `git worktree add` - Create worktree
- `git worktree remove` - Remove worktree
- `git checkout` - Switch branches
- `git add -A` - Stage all changes
- `git commit -m` - Create commits
- `git push` - Push to remote

### Claude Code Integration

**Execution**:
```bash
claude --yes-to-all --model {model} --prompt "{prompt}"
```

**Models**:
- `claude-sonnet-4` (base)
- `claude-opus-4` (heavy)

**Working Directory**: Set via subprocess `cwd` parameter

### Cloudflare R2 Integration

**Purpose**: Store screenshots from review phase

**Usage**: Screenshots uploaded during `/review` execution

**URLs**: Embedded in PR body and issue comments

---

## Success Criteria

### Primary Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Issue-to-PR Time | < 30 min | Time from `adw sdlc` to PR created |
| Test Pass Rate | > 90% | PRs passing all tests on first try |
| Review Pass Rate | > 80% | PRs with no blocker issues |
| Documentation Coverage | 100% | All features documented |

### Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| PR Acceptance Rate | > 70% | PRs merged without manual changes |
| Resolution Success | > 60% | Failed tests/reviews auto-resolved |
| State Resumption | 100% | Interrupted workflows resumable |

### Operational Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Concurrent Workflows | 15 | Port range capacity |
| Worktree Isolation | 100% | No cross-contamination |
| Progress Visibility | 100% | All steps posted to GitHub |

---

## Non-Functional Requirements

### Performance

| Requirement | Specification |
|-------------|---------------|
| Plan Phase | < 5 minutes |
| Build Phase | < 10 minutes |
| Test Phase | < 10 minutes (unit) |
| Review Phase | < 5 minutes |
| Document Phase | < 3 minutes |

### Reliability

| Requirement | Specification |
|-------------|---------------|
| State Durability | No data loss on crash |
| Resumability | Workflow resumable from any phase |
| Idempotency | Safe to re-run phases |

### Scalability

| Requirement | Specification |
|-------------|---------------|
| Concurrent Workflows | Up to 15 (port range) |
| Repository Size | No explicit limit |
| Issue Complexity | Single-issue scope |

### Security

| Requirement | Specification |
|-------------|---------------|
| Credential Storage | .env file only (gitignored) |
| Environment Isolation | Filtered subprocess env |
| Code Execution | Relies on Claude Code safety |

### Usability

| Requirement | Specification |
|-------------|---------------|
| Installation | Single `uv add` command |
| Configuration | Optional (sensible defaults) |
| Learning Curve | < 1 hour to first workflow |

---

## Glossary

| Term | Definition |
|------|------------|
| **ADW** | AI Developer Workflow - the framework name |
| **ADW ID** | 8-character unique identifier for workflow instance |
| **Agent** | Claude Code instance executing a command |
| **Artifact** | Generated files (prompts, outputs, state) |
| **Base Model** | Claude Sonnet - used for simpler tasks |
| **Blocker** | Review issue that must be fixed before merge |
| **Command** | Slash command template (e.g., `/feature`) |
| **Heavy Model** | Claude Opus - used for complex tasks |
| **Issue Class** | Category: /feature, /bug, /chore |
| **Model Set** | "base" or "heavy" - determines model selection |
| **Phase** | SDLC stage: plan, build, test, review, document |
| **Plan** | Markdown file with implementation instructions |
| **Resolution Loop** | Automatic retry with fix attempts |
| **SDLC** | Software Development Life Cycle |
| **State** | Persisted workflow data (JSON) |
| **Worktree** | Isolated git working directory |
| **ZTE** | Zero-Touch Execution - full automation including merge |

---

## Appendix A: Example Issue Format

### Feature Issue

```markdown
Title: Add user avatar upload functionality

## Description
Users should be able to upload a custom avatar image to their profile.

## Requirements
- Support JPEG and PNG formats
- Max file size: 5MB
- Image cropped to square
- Displayed in header and profile page

## Technical Notes
- Store in S3 bucket
- Use existing image processing library
- Update User model with avatar_url field

## Acceptance Criteria
- [ ] Upload form in profile settings
- [ ] Image validation (format, size)
- [ ] Automatic crop to square
- [ ] Display in header (32x32)
- [ ] Display in profile (128x128)
```

### Bug Issue

```markdown
Title: Login fails with special characters in password

## Description
Users with passwords containing special characters (e.g., @#$%) cannot log in.

## Steps to Reproduce
1. Create account with password "Test@123#"
2. Log out
3. Attempt to log in with same password
4. Observe "Invalid credentials" error

## Expected Behavior
Login should succeed with correct password regardless of special characters.

## Environment
- Browser: Chrome 120
- OS: macOS 14.1
- Environment: Production
```

### Chore Issue

```markdown
Title: Update React to version 18.3

## Description
Update React and related dependencies to latest stable version.

## Tasks
- Update react and react-dom to 18.3
- Update @types/react and @types/react-dom
- Run tests and fix any breaking changes
- Update documentation if needed

## Notes
- Check React 18.3 release notes for breaking changes
- May need to update testing-library
```

---

## Appendix B: Troubleshooting Guide

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "No state found for ADW ID" | build/test/review run without prior plan | Run `adw plan` first |
| "Worktree validation failed" | Worktree deleted or corrupted | Run `adw plan` to recreate |
| "Port in use" | Concurrent workflow using ports | Will auto-find alternative ports |
| "gh: not authenticated" | gh CLI not configured | Run `gh auth login` |
| "Claude command not found" | Claude CLI not installed | Install Claude Code CLI |
| "Plan file does not exist" | Plan deleted after planning | Re-run `adw plan` |

### Debug Information

**Log Location**: `logs/{adw_id}/{workflow}.log`

**State Location**: `artifacts/{project_id}/{adw_id}/adw_state.json`

**Prompt History**: `artifacts/{project_id}/{adw_id}/{agent}/prompts/`

---

*End of Product Requirements Document*
