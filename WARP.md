# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

**ADW Framework** (AI Developer Workflow) is a Python package that automates GitHub-driven software development using Claude Code agents. It processes GitHub issues through a full SDLC pipeline (plan → build → test → review → document → ship) using isolated git worktrees for parallel execution.

## Development Commands

```bash
# Install dependencies
uv sync

# Run CLI
uv run adw --help

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_agents.py -v

# Run a specific test by name
uv run pytest tests/test_agents.py::test_function_name -v

# Run tests by marker (unit, integration, slow, requires_api)
uv run pytest -m unit
uv run pytest -m "not slow and not requires_api"

# Run with coverage
uv run pytest --cov=adw --cov-report=term-missing

# Linting
uv run ruff check adw/

# Auto-fix lint issues
uv run ruff check --fix adw/
```

## CLI Commands

```bash
# Full SDLC workflow (plan→build→test→review→document)
uv run adw sdlc <issue-number> [adw-id] [--skip-e2e] [--skip-resolution]

# Zero Touch Execution (SDLC + auto-merge) - USE WITH CAUTION
uv run adw zte <issue-number> [adw-id]

# Individual workflow phases
uv run adw plan <issue-number> [adw-id]      # Creates worktree + plan
uv run adw build <issue-number> <adw-id>     # Implements plan
uv run adw test <issue-number> <adw-id>      # Runs tests
uv run adw review <issue-number> <adw-id>    # Reviews changes
uv run adw document <issue-number> <adw-id>  # Generates docs
uv run adw ship <issue-number> <adw-id>      # Approves + merges PR
uv run adw patch <issue-number> [adw-id]     # Direct patch from issue

# Triggers (continuous processing)
uv run adw monitor   # Poll GitHub every 20s for new issues
uv run adw webhook   # Start webhook server for real-time events
```

## Architecture

### Package Structure
```
adw-framework/
├── adw/                    # Main Python package
│   ├── cli.py              # Entry point - argparse CLI, routes via importlib
│   ├── core/               # Core modules
│   │   ├── agent.py        # Executes Claude Code CLI, handles JSONL parsing
│   │   ├── config.py       # Loads .adw.yaml, model mapping, path management
│   │   ├── state.py        # ADWState - persistent JSON state per workflow
│   │   ├── data_types.py   # Pydantic models (GitHubIssue, AgentPromptRequest, etc.)
│   │   └── utils.py        # Environment and subprocess utilities
│   ├── integrations/       # External service integrations
│   │   ├── github.py       # GitHub API via gh CLI
│   │   ├── worktree_ops.py # Git worktree creation/cleanup, port allocation
│   │   └── workflow_ops.py # Shared ops: classification, plan building, PR creation
│   ├── workflows/          # SDLC workflow implementations
│   │   ├── wt/             # Isolated worktree workflows (production)
│   │   │   ├── sdlc_iso.py # Complete SDLC orchestrator
│   │   │   ├── plan_iso.py, build_iso.py, test_iso.py, etc.
│   │   └── reg/            # Regular (non-isolated) workflows (legacy)
│   └── triggers/           # Event triggers
│       ├── trigger_cron.py # Polling-based trigger
│       └── trigger_webhook.py # Webhook server
├── commands/               # Claude Code slash command templates (.md files)
│   ├── feature.md, bug.md, chore.md  # Issue type handlers
│   ├── implement.md, review.md, document.md  # Phase commands
│   └── _command_index.yaml # Command metadata
└── templates/
    └── adw.yaml            # Template for .adw.yaml config
```

### Data Flow
1. `cli.py` parses args → calls `run_workflow()` which imports `adw/workflows/wt/{command}_iso.py`
2. Workflow creates `ADWState(adw_id)`, loads config via `ADWConfig.load()`
3. Workflow creates isolated worktree via `worktree_ops.create_worktree()`
4. Workflow executes Claude Code via `agent.execute_template()` with slash commands from `commands/`
5. State persists to `artifacts/{project_id}/{adw-id}/adw_state.json`

### Model Selection
The framework uses a model mapping in `config.py` (`SLASH_COMMAND_MODEL_MAP`):
- `"base"` model set: Uses Sonnet for all commands
- `"heavy"` model set: Uses Opus for complex operations (/implement, /bug, /feature, /document, /patch)

Model set is determined by ADW state's `model_set` field, typically extracted from issue comments.

### Worktree Isolation
Each ADW workflow runs in an isolated git worktree:
- Location: `artifacts/{project_id}/trees/{adw-id}/`
- Unique ports allocated from ranges (backend: 9100-9114, frontend: 9200-9214)
- Feature branch: `{type}-issue-{num}-adw-{id}-{slug}`

## Configuration

Projects using this framework require:

1. **`.adw.yaml`** in project root:
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

2. **`.env`** with required variables:
```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx     # Required
GITHUB_PAT=ghp_xxxxx               # Optional (uses gh auth if not set)
CLAUDE_CODE_PATH=claude            # Optional (path to claude CLI)
ADW_DISABLE_GITHUB_COMMENTS=1      # Optional (suppress issue comments)
```

## Key Data Types

Located in `adw/core/data_types.py`:
- `AgentTemplateRequest` - Request to execute a slash command
- `AgentPromptResponse` - Response from Claude Code execution (includes retry_code)
- `ADWStateData` - Pydantic model for persistent state
- `GitHubIssue` - Pydantic model for GitHub issue data
- `SlashCommand` - Literal type of all valid slash commands
- `RetryCode` - Enum for retryable error types

## Artifacts Directory Structure

```
artifacts/{org}/{repo}/
├── {adw-id}/
│   ├── adw_state.json          # Workflow state
│   ├── ops/                    # Orchestrator logs
│   ├── sdlc_planner/           # Planning agent output
│   ├── sdlc_implementor/       # Build agent output
│   └── ...
└── trees/
    └── {adw-id}/               # Isolated git worktree
```

## Testing Markers

Tests use pytest markers defined in `pytest.ini`:
- `unit`: Fast, no external dependencies
- `integration`: Mocked external services  
- `slow`: Tests > 10 seconds
- `requires_api`: Needs real API access (Anthropic, GitHub)
- `requires_network`: Needs network access

## Adding New Slash Commands

1. Create `.md` file in `commands/` with frontmatter and instructions
2. Add command to `SlashCommand` literal in `adw/core/data_types.py`
3. Add model mapping to `SLASH_COMMAND_MODEL_MAP` in `adw/core/config.py`
4. Update `_command_index.yaml` if needed
