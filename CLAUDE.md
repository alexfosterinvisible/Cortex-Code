# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ADW (AI Developer Workflow) is an orchestration framework that automates software development using Claude Code agents in isolated git worktrees. It processes GitHub issues through a complete SDLC pipeline: plan → build → test → review → document → ship.

## Build & Development Commands

```bash
# Install dependencies
uv sync

# Run all tests
uv run pytest

# Run specific test categories
uv run pytest -m unit                    # Fast unit tests only
uv run pytest -m integration             # Integration tests
uv run pytest tests/unit/test_cli.py    # Single test file
uv run pytest -k "test_config"           # Tests matching pattern

# Linting
uv run ruff check adw/
uv run ruff check --fix adw/             # Auto-fix

# Coverage
uv run pytest --cov=adw --cov-report=term-missing

# CLI usage
uv run adw --help
uv run adw sdlc <issue-number>           # Full SDLC pipeline
uv run adw plan <issue-number>           # Plan phase only
uv run adw zte <issue-number>            # Zero Touch Execution (auto-merge)
```

## Architecture

### Package Structure

```
adw/
├── cli.py                    # Entry point - routes CLI commands to workflows
├── core/
│   ├── config.py             # ADWConfig - loads .adw.yaml, manages paths
│   ├── state.py              # ADWState - persistent JSON state per workflow
│   ├── agent.py              # Claude Code execution - prompts, retry logic
│   ├── data_types.py         # Pydantic models, Literals, enums
│   └── utils.py              # Logging, env vars, ID generation
├── integrations/
│   ├── github.py             # GitHub API via gh CLI
│   ├── git_ops.py            # Git operations (commits, branches)
│   ├── workflow_ops.py       # Shared ADW operations (classify, plan, build)
│   └── worktree_ops.py       # Git worktree and port management
├── workflows/
│   ├── wt/                   # Worktree-isolated workflows (primary)
│   │   ├── plan_iso.py       # Planning: fetch issue → classify → worktree → plan → PR
│   │   ├── build_iso.py      # Execute /implement with plan file
│   │   ├── test_iso.py       # Run tests, auto-fix failures (3 retries)
│   │   ├── review_iso.py     # Validate against spec, screenshots
│   │   ├── document_iso.py   # Generate feature docs
│   │   ├── ship_iso.py       # Approve + merge PR
│   │   └── sdlc_iso.py       # Chains: plan → build → test → review → document
│   └── reg/                  # Regular workflows (non-isolated, deprecated)
└── triggers/
    ├── trigger_webhook.py    # FastAPI webhook for GitHub events
    └── trigger_cron.py       # Polling-based trigger
```

### Key Concepts

**ADW ID**: 8-character unique identifier per workflow instance (e.g., `abc12345`). Used for:
- State file location: `artifacts/{project_id}/{adw-id}/adw_state.json`
- Worktree path: `artifacts/{project_id}/trees/{adw-id}/`
- Port allocation

**Isolated Worktrees**: Each workflow runs in its own git worktree for parallel execution without interference.

**Port Allocation**: Deterministic port assignment from ADW ID hash:
- Backend: 9100-9114
- Frontend: 9200-9214

**Model Selection**: Commands use `base` (Sonnet) or `heavy` (Opus) based on `model_set` in state:
- Heavy: `/implement`, `/document`, `/feature`, `/bug`, `/chore`, `/patch`
- Base: Everything else

**State Persistence**: `ADWState` tracks workflow progress:
```python
{
  "adw_id": "abc12345",
  "issue_number": "42",
  "branch_name": "feature-issue-42-adw-abc12345-add-auth",
  "plan_file": "specs/issue-42-adw-abc12345-add-auth.md",
  "worktree_path": "/path/to/artifacts/org/repo/trees/abc12345",
  "model_set": "base"
}
```

### Command Templates

Commands in `commands/` are markdown templates with `$ARGUMENTS` placeholder. Key commands:
- `/feature`, `/bug`, `/chore`: Issue classification + planning
- `/implement`: Execute plan file
- `/review`: Validate implementation
- `/classify_issue`: Determine issue type
- `/generate_branch_name`: Create standardized branch name

### Data Flow

1. GitHub issue triggers workflow (CLI, webhook, or cron)
2. `workflow_ops.ensure_adw_id()` creates/loads state
3. `worktree_ops.create_worktree()` creates isolated environment
4. `agent.execute_template()` runs Claude Code with slash commands
5. Results flow through state, git operations, and GitHub API

### Testing Patterns

Tests use fixtures from `tests/conftest.py`:
- `tmp_project_dir`: Full project structure with `.adw.yaml` and `.env`
- `mock_adw_config`: Mocked ADWConfig
- `mock_subprocess_run`: For git/gh/claude CLI mocking
- `mock_claude_success`: Simulates successful agent responses

Test markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.requires_api`

## Configuration

**`.adw.yaml`** (required in consuming projects):
```yaml
project_id: "org/repo"
artifacts_dir: "./artifacts"
source_root: "./src"
ports:
  backend_start: 9100
  frontend_start: 9200
commands:
  - "${ADW_FRAMEWORK}/commands"
  - ".claude/commands"
```

**`.env`** (required):
```bash
ANTHROPIC_API_KEY=sk-ant-xxx   # Required
GITHUB_PAT=ghp_xxx             # Optional (uses gh auth if not set)
CLAUDE_CODE_PATH=claude        # Optional
```

## GitHub Webhook Triggers

Comment on issue to trigger workflow:
- `adw_plan_iso`: Plan only
- `adw_sdlc_iso`: Full SDLC
- `adw_sdlc_zte_iso`: SDLC + auto-merge
- `model_set heavy`: Use Opus for complex tasks

## Artifact Locations

```
artifacts/{org}/{repo}/
├── {adw-id}/
│   ├── adw_state.json
│   ├── ops/prompts/           # Saved prompts
│   ├── sdlc_planner/raw_output.jsonl
│   ├── sdlc_implementor/
│   ├── tester/
│   └── reviewer/
└── trees/{adw-id}/            # Isolated git worktree
```

---

## User-Specific Instructions (Verbatim)

PURPOSEFUL BRITTLENESS DURING LLM DEV

- dont use defaults
- don't do exception handling
- don't mock apis
- don't add fallbacks
- etc
- this is important

VIRTUAL ENVIRONMENT CONVENTIONS

- use .venv instead of venv for virtual environments

SECURITY AND CONFIGURATION

- always put keys etc in .env file and access via dotenv
- config params should be stored globally either in CFG singleton in run.py or run_config.py

DEVELOPMENT WORKFLOW

- commit regularly during operations for easy save points <feat> <fix> tags etc. use sub-tasks (parllel) for this to prevent blocking the main claude code thread.
- always update claude.md using subtasks to not block the main claude code thread.
- always run scripts and existing tests to prevent regression errors.
- after completing tasks, suggest short list of regression tests to add to ./tests to prevent regression errors going forward. Each suggestion should be a single line "if [function] does/doesn't x then broken" for readability ease. When then writing those tests, those single line descriptions should be added to that tests success/fail print.
- Always run scripts after editing to check they work
