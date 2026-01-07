# Project Map

## Tech Stack

### Core
- **Language**: Python 3.10+
- **Package Manager**: uv
- **Build System**: Hatchling
- **Validation**: Pydantic 2.0+
- **Config**: PyYAML, python-dotenv

### Server Components
- **Framework**: FastAPI (for webhook server)
- **Server**: Uvicorn
- **Database**: aiosqlite (optional)

### Development
- **Testing**: pytest, pytest-cov, pytest-mock
- **Linting**: Ruff
- **Hooks**: pre-commit

## Project Structure

```
cxc-framework/
|-- cxc/                    # Main package
|   |-- cli.py              # Entry point - routes CLI commands
|   |-- core/               # Core modules
|   |   |-- config.py       # CxCConfig - loads .cxc.yaml
|   |   |-- state.py        # CxCState - persistent JSON state
|   |   |-- agent.py        # Claude Code execution, retry logic
|   |   |-- data_types.py   # Pydantic models, Literals, enums
|   |   |-- utils.py        # Logging, env vars, ID generation
|   |-- integrations/       # External service integrations
|   |   |-- github.py       # GitHub API via gh CLI
|   |   |-- git_ops.py      # Git operations (commits, branches)
|   |   |-- workflow_ops.py # Shared CxC operations
|   |   |-- worktree_ops.py # Git worktree and port management
|   |-- workflows/          # Workflow modules
|   |   |-- wt/             # Worktree-isolated workflows (primary)
|   |   |   |-- plan_iso.py
|   |   |   |-- build_iso.py
|   |   |   |-- test_iso.py
|   |   |   |-- review_iso.py
|   |   |   |-- document_iso.py
|   |   |   |-- ship_iso.py
|   |   |   |-- sdlc_iso.py
|   |   |-- reg/            # Regular workflows (deprecated)
|   |-- triggers/           # Event triggers
|       |-- trigger_webhook.py
|       |-- trigger_cron.py
|-- commands/               # Slash command templates (markdown)
|   |-- feature.md, bug.md, chore.md    # Planning commands
|   |-- implement.md        # Build command
|   |-- review.md           # Review command
|   |-- examples/           # App-specific command examples
|-- templates/              # Config templates
|   |-- cxc.yaml            # Template for .cxc.yaml
|-- tests/                  # Test suite
|   |-- unit/               # Unit tests
|   |-- integration/        # Integration tests
|   |-- regression/         # Regression tests
|   |-- conftest.py         # Pytest fixtures
|-- docs/                   # Documentation
|   |-- ORCHESTRATOR_GUIDE.md  # Primary orchestrator reference
|-- artifacts/              # Runtime artifacts (gitignored)
```

## Key Components

### CLI Entry Point (`cxc/cli.py`)
- Routes `uv run cxc <command>` to workflow modules
- Commands: plan, build, test, review, document, ship, sdlc, zte

### Configuration (`cxc/core/config.py`)
- `CxCConfig` dataclass loads `.cxc.yaml`
- Manages paths: project_root, artifacts_dir, source_root
- Port configuration: backend_start/count, frontend_start/count
- Model mapping: slash command -> model selection

### State Management (`cxc/core/state.py`)
- `CxCState` class with file persistence
- Tracks: cxc_id, issue_number, branch_name, plan_file, worktree_path, ports, model_set
- Location: `artifacts/{project_id}/{cxc-id}/cxc_state.json`

### Agent Execution (`cxc/core/agent.py`)
- `execute_template()` - runs slash commands via Claude Code CLI
- Model selection based on command + model_set
- Retry logic for transient failures
- JSONL output parsing

### Worktree Isolation (`cxc/integrations/worktree_ops.py`)
- Creates git worktrees under `artifacts/{project_id}/trees/{cxc-id}/`
- Allocates deterministic ports from CxC ID hash
- Port ranges: backend 9100-9114, frontend 9200-9214

## Development Workflow

### Running Locally
```bash
# Install dependencies
uv sync

# Run CLI
uv run cxc --help
uv run cxc sdlc <issue-number>
```

### Running Tests
```bash
# All tests
uv run pytest

# Specific categories
uv run pytest -m unit
uv run pytest -m integration
uv run pytest tests/unit/test_cli.py
```

### Linting
```bash
uv run ruff check cxc/
uv run ruff check --fix cxc/
```

## Current Features
- Full SDLC pipeline (plan -> build -> test -> review -> document -> ship)
- Worktree-isolated execution
- GitHub issue/PR integration
- Webhook and cron triggers
- Dynamic model selection
- Auto-retry and self-healing loops

## Known Limitations
- GitHub-only (no GitLab, Bitbucket)
- Requires Claude Code CLI
- No database persistence (file-based state)
- reg/ workflows deprecated in favor of wt/

---
*This file is maintained by the project-architect agent. Updated during sprints.*
