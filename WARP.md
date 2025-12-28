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

# Run tests
uv run pytest tests/

# Run a single test file
uv run pytest tests/test_agents.py -v

# Run a specific test
uv run pytest tests/test_agents.py::test_function_name -v

# Type checking (uses Pydantic for validation)
# No explicit typecheck command - validation is runtime via Pydantic models
```

## CLI Usage

```bash
# Full SDLC workflow
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

# Triggers
uv run adw monitor   # Poll GitHub every 20s for new issues
uv run adw webhook   # Start webhook server for real-time events
```

## Architecture

### Package Structure
- `adw/` - Main Python package (entry point: `adw/cli.py`)
- `adw/workflows/` - SDLC workflow implementations (plan.py, build.py, test.py, review.py, etc.)
- `adw/triggers/` - Event triggers (cron polling, webhook server)
- `commands/` - Claude Code slash command templates (.md files)

### Core Modules
- `cli.py` - Argparse CLI, routes to workflow modules via `importlib.import_module()`
- `config.py` - Loads `.adw.yaml` configuration, manages artifact/worktree paths
- `state.py` - `ADWState` class for persistent JSON state in `artifacts/{project_id}/{adw-id}/`
- `agent.py` - Executes Claude Code CLI in programmatic mode, handles JSONL output parsing
- `worktree_ops.py` - Git worktree creation/cleanup, port allocation
- `workflow_ops.py` - Shared operations: issue classification, plan building, PR creation
- `github.py` - GitHub API interactions via `gh` CLI

### Data Flow
1. `cli.py` parses args → calls `run_workflow()` which imports `adw/workflows/{command}.py`
2. Workflow creates `ADWState(adw_id)`, loads config via `ADWConfig.load()`
3. Workflow creates isolated worktree via `worktree_ops.create_worktree()`
4. Workflow executes Claude Code via `agent.execute_template()` with slash commands
5. State persists to `artifacts/{project_id}/{adw-id}/adw_state.json`

### Key Data Types (adw/data_types.py)
- `AgentTemplateRequest` - Request to execute a slash command
- `AgentPromptResponse` - Response from Claude Code execution
- `ADWStateData` - Pydantic model for persistent state
- `GitHubIssue` - Pydantic model for GitHub issue data
- `SlashCommand` - Literal type of all valid slash commands

## Configuration

Projects using this framework require:
1. `.adw.yaml` in project root (project_id, artifacts_dir, ports, app config)
2. `.env` with `ANTHROPIC_API_KEY`, optionally `GITHUB_PAT`, `CLAUDE_CODE_PATH`

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

## Model Selection

The framework uses a model mapping in `agent.py`:
- `"base"` model set: Uses Sonnet for all commands
- `"heavy"` model set: Uses Opus for complex operations (/implement, /bug, /feature, /document)

Model set is determined by ADW state's `model_set` field, typically extracted from issue comments.

## Worktree Isolation

Each ADW workflow runs in an isolated git worktree:
- Location: `artifacts/{project_id}/trees/{adw-id}/`
- Unique ports allocated from ranges (backend: 9100-9114, frontend: 9200-9214)
- Feature branch: `{type}-issue-{num}-adw-{id}-{slug}`
