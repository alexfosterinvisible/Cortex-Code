# ADW Framework - Product Requirements Document (Claude)

## Document Information

| Field           | Value                          |
|-----------------|--------------------------------|
| Version         | 1.0                            |
| Date            | 2025-12-30                     |
| Status          | Complete                       |
| Author          | Claude Code Agent              |

---

## 1. Product Vision

### 1.1 Vision Statement

ADW (AI Developer Workflow) transforms GitHub issues into shipped, production-ready code through a fully autonomous pipeline of AI agents operating in isolated development environments.

### 1.2 Problem Statement

Modern software development teams face several challenges:
1. **Context switching**: Developers spend significant time translating issue requirements into implementation plans
2. **Manual overhead**: Each feature requires repetitive steps: branch, implement, test, review, document, merge
3. **Quality variance**: Rushed implementations may skip testing or documentation
4. **Bottlenecks**: Code review and testing phases create queues
5. **Knowledge loss**: Implementation decisions and context are not consistently documented

### 1.3 Solution

ADW provides a complete Software Development Life Cycle (SDLC) automation framework that:
- Accepts a GitHub issue as input
- Produces merged, documented code as output
- Uses Claude Code agents for intelligent automation
- Operates in isolated git worktrees for parallel execution
- Maintains full transparency through GitHub comments

### 1.4 Value Proposition

| For                    | Who Need                                        | ADW Is                                                    | That                                               |
|------------------------|-------------------------------------------------|-----------------------------------------------------------|----------------------------------------------------|
| Solo developers        | To ship features faster without sacrificing quality | An autonomous development pipeline                         | Handles the entire SDLC from issue to merged PR    |
| Small teams            | To parallelize development without conflicts    | An isolated worktree-based execution system               | Enables multiple features in progress simultaneously |
| Engineering leaders    | To ensure consistent quality and documentation  | A structured workflow with mandatory phases               | Guarantees tests, reviews, and docs for every feature |
| Open source maintainers| To handle contribution volume efficiently       | An issue-to-PR automation framework                       | Converts issues into review-ready pull requests    |

---

## 2. User Personas

### 2.1 Persona: Solo Developer Sarah

**Background**: Full-stack developer working on a SaaS product solo

**Goals**:
- Ship features without getting bogged down in repetitive tasks
- Maintain high code quality despite time constraints
- Keep documentation up-to-date

**Pain Points**:
- Spends 40% of time on non-coding activities (branching, PRs, docs)
- Forgets to write tests when under pressure
- Documentation falls behind

**How ADW Helps**:
- `adw sdlc 42` processes feature request while Sarah works on something else
- Automated tests and documentation included
- Can review AI-generated PR and merge if satisfied

**Usage Pattern**:
```bash
# Create issue on GitHub describing feature
# Run ADW from terminal
uv run adw sdlc 42

# Review generated PR
# Approve and merge (or iterate)
```

### 2.2 Persona: Team Lead Tom

**Background**: Leads a team of 5 developers, manages sprint planning

**Goals**:
- Parallelize development across team members
- Ensure consistent code quality
- Reduce review bottlenecks

**Pain Points**:
- Developers step on each other's toes with conflicting changes
- Code reviews are a bottleneck
- Quality varies by developer experience

**How ADW Helps**:
- Each ADW instance operates in isolated worktree
- Standardized workflow ensures consistent quality
- Pre-reviewed code reduces human review burden

**Usage Pattern**:
```bash
# Set up webhook for team repository
uv run adw webhook

# Team comments "adw_sdlc_iso" on issues
# ADW processes in parallel, creates PRs
# Team reviews ADW-generated PRs
```

### 2.3 Persona: Open Source Owner Olivia

**Background**: Maintains popular open source library, receives many issues

**Goals**:
- Triage and implement feature requests efficiently
- Maintain contributor experience
- Keep documentation current

**Pain Points**:
- Hundreds of issues, limited time
- Contributors need guidance on implementation
- Stale PRs and issues accumulate

**How ADW Helps**:
- Convert clear issues into implementation PRs automatically
- Generated specs serve as contributor guidance
- Documentation stays synchronized

**Usage Pattern**:
```bash
# Set up cron trigger for continuous processing
uv run adw monitor

# ADW picks up issues with "adw" comment
# Creates spec and implementation PR
# Olivia reviews and merges (or requests changes)
```

### 2.4 Persona: Enterprise Engineering Manager Emma

**Background**: Manages multiple teams, needs governance and auditability

**Goals**:
- Ensure compliance with development standards
- Track productivity metrics
- Reduce time-to-production

**Pain Points**:
- Inconsistent processes across teams
- Difficult to measure AI-assisted development ROI
- Change tracking and auditing needs

**How ADW Helps**:
- Standardized phases ensure compliance
- State files provide audit trail
- GitHub comments document all decisions

**Usage Pattern**:
```bash
# Configure ADW with organization standards
# Teams use via webhook integration
# Track via state files and GitHub history
```

---

## 3. User Stories

### 3.1 Core Workflow Stories

#### US-001: Process Single Issue
**As a** developer
**I want to** run the full SDLC on a GitHub issue
**So that** I get a merge-ready PR without manual intervention

**Acceptance Criteria**:
- [ ] CLI accepts issue number as argument
- [ ] Creates isolated worktree for development
- [ ] Generates implementation plan from issue
- [ ] Implements plan using Claude agent
- [ ] Runs and fixes tests automatically
- [ ] Reviews implementation against spec
- [ ] Documents the feature
- [ ] Creates PR with comprehensive summary
- [ ] Posts progress updates to GitHub issue

**Example**:
```bash
uv run adw sdlc 42
# Output: PR #100 created and ready for review
```

---

#### US-002: Run Specific Phase
**As a** developer
**I want to** run individual workflow phases
**So that** I can iterate on specific parts of development

**Acceptance Criteria**:
- [ ] `adw plan` creates spec without implementing
- [ ] `adw build` implements existing spec
- [ ] `adw test` runs tests with auto-resolution
- [ ] `adw review` validates against spec
- [ ] `adw document` generates feature docs
- [ ] `adw ship` merges completed work
- [ ] Each phase requires appropriate prior phases

**Example**:
```bash
uv run adw plan 42         # Just planning
uv run adw build 42 abc123 # Implement existing plan
uv run adw test 42 abc123  # Run tests
```

---

#### US-003: Resume Interrupted Workflow
**As a** developer
**I want to** resume a workflow from where it stopped
**So that** I don't lose progress on interrupted work

**Acceptance Criteria**:
- [ ] State persists to JSON file after each phase
- [ ] Providing ADW ID resumes existing workflow
- [ ] All prior state (branch, ports, paths) preserved
- [ ] Can skip phases that already completed

**Example**:
```bash
# Original run gets interrupted
uv run adw sdlc 42
# Ctrl+C during build phase

# Resume with same ADW ID
uv run adw build 42 abc12345
```

---

#### US-004: Zero Touch Execution
**As a** team lead
**I want to** enable fully automatic issue-to-production
**So that** straightforward features ship without human intervention

**Acceptance Criteria**:
- [ ] ZTE mode runs full SDLC plus ship
- [ ] Stops on any test failure (stricter than SDLC)
- [ ] Stops on any review blocker
- [ ] Automatically merges on success
- [ ] Posts clear status messages

**Example**:
```bash
uv run adw zte 42
# Automatically merges to main if all checks pass
```

---

### 3.2 Configuration Stories

#### US-010: Configure Project
**As a** developer
**I want to** configure ADW for my project
**So that** it understands my project structure

**Acceptance Criteria**:
- [ ] Configuration via `.adw.yaml` in project root
- [ ] Supports project_id, artifacts_dir, source_root
- [ ] Supports port range configuration
- [ ] Supports custom command directories
- [ ] Supports app-specific settings (backend_dir, etc.)

**Example**:
```yaml
# .adw.yaml
project_id: "myorg/myrepo"
artifacts_dir: "./artifacts"
ports:
  backend_start: 9100
  frontend_start: 9200
app:
  backend_dir: "api"
  frontend_dir: "web"
```

---

#### US-011: Run Setup Script
**As a** new user
**I want to** quickly set up ADW in my project
**So that** I can start using it immediately

**Acceptance Criteria**:
- [ ] Setup script auto-detects project_id from git
- [ ] Creates .adw.yaml with sensible defaults
- [ ] Creates .env with required variables
- [ ] Copies slash commands to project
- [ ] Runs uv sync for dependencies
- [ ] Verifies installation works

**Example**:
```bash
python ../adw-framework/setup_adw_example.py
# Creates all required files and verifies setup
```

---

### 3.3 Trigger Stories

#### US-020: Webhook Trigger
**As a** team
**I want to** trigger ADW via GitHub comments
**So that** we can automate without leaving GitHub

**Acceptance Criteria**:
- [ ] Webhook server listens for GitHub events
- [ ] Recognizes `adw_sdlc_iso` command in comments
- [ ] Extracts ADW ID if provided for resumption
- [ ] Extracts model_set preference
- [ ] Ignores ADW bot comments (no loops)
- [ ] Returns 200 immediately (async processing)

**Example**:
Comment on issue: `adw_sdlc_iso model_set heavy`
Result: ADW processes issue using Opus model

---

#### US-021: Cron Trigger
**As a** automation engineer
**I want to** poll for new issues automatically
**So that** ADW processes issues without explicit triggers

**Acceptance Criteria**:
- [ ] Polls GitHub every 20 seconds
- [ ] Identifies new issues without ADW comments
- [ ] Identifies issues with pending ADW commands
- [ ] Prevents duplicate processing
- [ ] Handles graceful shutdown

**Example**:
```bash
uv run adw monitor
# Continuously processes qualifying issues
```

---

### 3.4 Testing Stories

#### US-030: Run Tests with Resolution
**As a** developer
**I want to** have failing tests automatically fixed
**So that** the workflow continues without manual intervention

**Acceptance Criteria**:
- [ ] Runs project test suite via configured command
- [ ] Parses test results as structured JSON
- [ ] Attempts to resolve each failing test
- [ ] Retries up to 4 times for unit tests
- [ ] Retries up to 2 times for E2E tests
- [ ] Posts comprehensive summary to issue

**Example**:
Test output shows 2 failing tests
ADW attempts resolution
Re-runs tests, now passing
Continues to review phase

---

#### US-031: Skip E2E Tests
**As a** developer
**I want to** skip E2E tests when not relevant
**So that** I can speed up the workflow

**Acceptance Criteria**:
- [ ] `--skip-e2e` flag recognized by CLI
- [ ] Flag passed through SDLC orchestration
- [ ] E2E phase completely skipped
- [ ] Summary indicates E2E was skipped

**Example**:
```bash
uv run adw sdlc 42 --skip-e2e
# Runs unit tests only
```

---

### 3.5 Review Stories

#### US-040: Review with Screenshots
**As a** reviewer
**I want to** see visual proof of working features
**So that** I can verify UI implementation

**Acceptance Criteria**:
- [ ] Review agent captures critical path screenshots
- [ ] Screenshots saved with descriptive names
- [ ] Uploaded to R2 if configured (else local paths)
- [ ] Included in review summary
- [ ] Number of screenshots kept reasonable (1-5)

**Example**:
Review produces:
- 01_login_form.png
- 02_dashboard_after_login.png
- 03_feature_modal.png

---

#### US-041: Auto-resolve Blockers
**As a** developer
**I want to** have blocking issues fixed automatically
**So that** the workflow continues without manual intervention

**Acceptance Criteria**:
- [ ] Review identifies issues as blocker/tech_debt/skippable
- [ ] Blockers trigger patch plan creation
- [ ] Patch is implemented automatically
- [ ] Review retries after patch (max 3 times)
- [ ] `--skip-resolution` disables this behavior

**Example**:
Review finds button color wrong (blocker)
ADW creates patch plan
Implements color fix
Re-runs review, now passing

---

### 3.6 Documentation Stories

#### US-050: Generate Feature Documentation
**As a** developer
**I want to** have documentation generated automatically
**So that** users know how to use new features

**Acceptance Criteria**:
- [ ] Analyzes git diff against main
- [ ] References original spec file
- [ ] Creates markdown doc in app_docs/
- [ ] Includes screenshots if available
- [ ] Updates conditional_docs.md index
- [ ] Never fails the workflow (non-blocking)

**Example**:
Creates: `app_docs/feature-abc12345-user-auth.md`
Contains: Overview, usage, configuration sections

---

### 3.7 Health Check Stories

#### US-060: Verify Environment
**As a** developer
**I want to** check if my environment is ready for ADW
**So that** I can fix issues before running workflows

**Acceptance Criteria**:
- [ ] Checks required environment variables
- [ ] Checks git repository configuration
- [ ] Checks GitHub CLI authentication
- [ ] Checks Claude Code CLI functionality
- [ ] Returns comprehensive status report

**Example**:
```python
from adw.core.health import run_health_check
result = run_health_check()
print(result.success)  # True if all checks pass
```

---

## 4. Feature Catalog

### 4.1 Core Features

#### F-001: Unified CLI

**Description**: Single command-line interface for all ADW operations

**Capabilities**:
- Process issues: `plan`, `build`, `test`, `review`, `document`, `ship`
- Orchestrated workflows: `sdlc`, `zte`
- Triggers: `monitor`, `webhook`
- Patches: `patch`

**User Value**: One tool for entire development automation

---

#### F-002: Isolated Worktrees

**Description**: Each workflow runs in dedicated git worktree

**Capabilities**:
- Creates worktree under artifacts directory
- Allocates deterministic ports from ADW ID
- Writes .ports.env for server configuration
- Supports 15 concurrent workflows

**User Value**: Parallel development without conflicts

---

#### F-003: State Persistence

**Description**: Workflow state saved to JSON for resumption

**Capabilities**:
- Auto-save after each phase
- Load existing state by ADW ID
- Track all workflow metadata
- Support stdin/stdout piping

**User Value**: Never lose progress, resume anytime

---

#### F-004: Agent Execution

**Description**: Execute Claude Code with templated prompts

**Capabilities**:
- Load markdown templates from commands/
- Variable substitution ($ARGUMENTS, $1, $2)
- Model selection (base/heavy)
- Structured output parsing

**User Value**: Consistent, intelligent automation

---

#### F-005: GitHub Integration

**Description**: Full integration with GitHub via CLI

**Capabilities**:
- Fetch issues with all metadata
- Post progress comments
- Create and update PRs
- Approve and merge PRs

**User Value**: Complete GitHub workflow automation

---

#### F-006: Test Resolution

**Description**: Automatic fixing of failing tests

**Capabilities**:
- Parse test results as JSON
- Generate resolution for each failure
- Retry until passing or max attempts
- Support both unit and E2E tests

**User Value**: Self-healing test pipeline

---

#### F-007: Visual Review

**Description**: Screenshot-based verification of UI features

**Capabilities**:
- Capture critical functionality paths
- Upload to cloud storage (R2)
- Include in review summary
- Categorize issues by severity

**User Value**: Visual proof of implementation quality

---

#### F-008: Auto Documentation

**Description**: Generate feature documentation automatically

**Capabilities**:
- Analyze changes via git diff
- Create structured markdown docs
- Include screenshots
- Update documentation index

**User Value**: Documentation that never falls behind

---

### 4.2 Trigger Features

#### F-010: Webhook Server

**Description**: FastAPI server for GitHub webhook events

**Capabilities**:
- Accept POST at /gh-webhook
- Parse issue and comment events
- Extract ADW commands from text
- Launch workflows asynchronously

**User Value**: Trigger from GitHub UI

---

#### F-011: Polling Trigger

**Description**: Continuous polling for new work

**Capabilities**:
- Poll every 20 seconds
- Detect qualifying issues
- Prevent duplicate processing
- Graceful shutdown

**User Value**: Continuous automation without setup

---

### 4.3 Configuration Features

#### F-020: YAML Configuration

**Description**: Project configuration via .adw.yaml

**Capabilities**:
- Project identification
- Artifact and source paths
- Port allocation settings
- Command directory hierarchy
- App-specific settings

**User Value**: Zero-code project customization

---

#### F-021: Environment Secrets

**Description**: Secure credential management via .env

**Capabilities**:
- Anthropic API key
- GitHub PAT (optional)
- Claude Code path
- R2 credentials (optional)

**User Value**: Standard security practices

---

### 4.4 Command Features

#### F-030: Planning Commands

**Description**: Templates for creating implementation plans

**Commands**:
- `/feature` - Feature implementation plan
- `/bug` - Bug fix plan with root cause analysis
- `/chore` - Maintenance task plan
- `/patch` - Targeted fix for review issues

**User Value**: Structured, consistent planning

---

#### F-031: Implementation Commands

**Description**: Templates for code generation

**Commands**:
- `/implement` - Execute implementation plan

**User Value**: Intelligent code generation

---

#### F-032: Testing Commands

**Description**: Templates for test execution and resolution

**Commands**:
- `/test` - Run test suite
- `/test_e2e` - Run E2E tests
- `/resolve_failed_test` - Fix failing test
- `/resolve_failed_e2e_test` - Fix failing E2E test

**User Value**: Comprehensive testing with self-healing

---

#### F-033: Review Commands

**Description**: Templates for implementation validation

**Commands**:
- `/review` - Validate against specification

**User Value**: Automated quality assurance

---

#### F-034: Documentation Commands

**Description**: Templates for documentation generation

**Commands**:
- `/document` - Generate feature documentation

**User Value**: Automatic documentation

---

#### F-035: Git Commands

**Description**: Templates for git operations

**Commands**:
- `/commit` - Generate commit message
- `/pull_request` - Create GitHub PR

**User Value**: Consistent git workflows

---

#### F-036: Classification Commands

**Description**: Templates for issue analysis

**Commands**:
- `/classify_issue` - Determine issue type
- `/classify_and_branch` - Combined classification and branch naming
- `/generate_branch_name` - Create standardized name

**User Value**: Intelligent issue understanding

---

## 5. Success Metrics

### 5.1 Efficiency Metrics

| Metric                        | Target                | Measurement                           |
|-------------------------------|----------------------|---------------------------------------|
| Time from issue to PR         | < 30 minutes         | Timestamp difference                  |
| Human intervention rate       | < 20% of workflows   | Workflows requiring manual steps      |
| Test auto-resolution rate     | > 80%                | Tests fixed without human help        |
| Review blocker resolution rate| > 70%                | Blockers fixed automatically          |

### 5.2 Quality Metrics

| Metric                        | Target                | Measurement                           |
|-------------------------------|------------------------|---------------------------------------|
| PR approval rate              | > 90%                  | PRs approved without changes          |
| Test coverage maintained      | No decrease            | Coverage delta on PRs                 |
| Documentation completeness    | 100% features documented| Features with app_docs entries       |
| Review screenshot coverage    | > 80% visual features  | Features with visual proof            |

### 5.3 Reliability Metrics

| Metric                        | Target                | Measurement                           |
|-------------------------------|----------------------|---------------------------------------|
| Workflow completion rate      | > 95%                 | Workflows reaching completion         |
| State recovery success        | 100%                  | Resumed workflows completing          |
| Worktree isolation            | 0 conflicts           | Cross-workflow interference           |
| Webhook response time         | < 10 seconds          | Time to 200 response                  |

### 5.4 Adoption Metrics

| Metric                        | Target                | Measurement                           |
|-------------------------------|----------------------|---------------------------------------|
| Active projects               | Growth month-over-month| Projects with recent ADW activity     |
| Issues processed              | Growth month-over-month| Total ADW workflow completions        |
| ZTE adoption                  | > 30% of workflows    | ZTE vs standard SDLC usage            |
| Webhook integration           | > 50% of teams        | Teams using webhook triggers          |

---

## 6. Release Plan

### 6.1 MVP Features (v1.0)

**Must Have**:
- CLI with all core commands
- Full SDLC workflow (plan-build-test-review-document)
- State persistence and resumption
- GitHub integration (issues, PRs, comments)
- Worktree isolation
- Basic test resolution

**Should Have**:
- ZTE mode
- Webhook trigger
- E2E test support
- Screenshot capture

### 6.2 Future Enhancements (v2.0+)

**Planned**:
- Multi-repository support
- Custom workflow definitions
- Metrics dashboard
- Slack/Discord notifications
- PR review automation
- Dependency update workflows

---

## 7. Appendices

### 7.1 Glossary

| Term                | Definition                                                         |
|---------------------|---------------------------------------------------------------------|
| ADW                 | AI Developer Workflow - the framework                               |
| ADW ID              | 8-character unique identifier for workflow instance                 |
| SDLC                | Software Development Life Cycle                                     |
| ZTE                 | Zero Touch Execution - fully automated SDLC with auto-merge         |
| Worktree            | Git feature for multiple working directories from single repository |
| Slash Command       | Markdown template invoked via /name syntax                          |
| Model Set           | Selection between base (Sonnet) and heavy (Opus) models             |
| Spec File           | Implementation plan generated during planning phase                 |

### 7.2 References

| Resource                     | Location                              |
|------------------------------|---------------------------------------|
| Framework Repository         | https://github.com/your-org/adw-framework |
| Claude Code Documentation    | https://docs.anthropic.com/claude-code |
| GitHub CLI Documentation     | https://cli.github.com/manual        |
| Git Worktree Documentation   | https://git-scm.com/docs/git-worktree |

### 7.3 Version History

| Version | Date       | Author              | Changes                            |
|---------|------------|---------------------|------------------------------------|
| 1.0     | 2025-12-30 | Claude Code Agent   | Initial comprehensive PRD          |
