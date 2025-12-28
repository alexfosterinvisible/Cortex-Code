# ADW Architecture Specification

## Overview

This document describes the high-level architecture of the `adw` package.

## Package Structure

```
__init__.py  # utilities
cli.py  # utilities
core/
  __init__.py  # utilities
  aea_data_types.py  # AEAMessage, AEAAgent, AEAPromptRequest, AEAPromptResponse, AEANewAgentResponse, AEAServerStatus, AEAEndAgentRequest
  agent.py  # utilities
  config.py  # PortConfig, ADWConfig
  data_types.py  # RetryCode, GitHubUser, GitHubLabel, GitHubMilestone, GitHubComment, GitHubIssueListItem, GitHubIssue, AgentPromptRequest, AgentPromptResponse, AgentTemplateRequest, ClaudeCodeResultMessage, TestResult, E2ETestResult, ADWStateData, ReviewIssue, ReviewResult, DocumentationResult, ADWExtractionResult
  state.py  # ADWState
  utils.py  # utilities
integrations/
  __init__.py  # utilities
  git_ops.py  # utilities
  github.py  # utilities
  r2_uploader.py  # R2Uploader
  workflow_ops.py  # utilities
  worktree_ops.py  # utilities
triggers/
  __init__.py  # utilities
  adw_trigger_aea_server.py  # utilities
  trigger_cron.py  # utilities
  trigger_webhook.py  # utilities
workflows/
  __init__.py  # utilities
  build.py  # utilities
  document.py  # utilities
  patch.py  # utilities
  plan.py  # utilities
  plan_build.py  # utilities
  plan_build_document.py  # utilities
  plan_build_review.py  # utilities
  plan_build_test.py  # utilities
  plan_build_test_review.py  # utilities
  review.py  # utilities
  sdlc.py  # utilities
  sdlc_zte.py  # utilities
  ship.py  # utilities
  test.py  # utilities
```

## Core Components

### `AEAMessage` (adw.core.aea_data_types)

Single message in an agent conversation
- **Inherits**: BaseModel

### `AEAAgent` (adw.core.aea_data_types)

Agent model representing a Claude Code session
- **Inherits**: BaseModel

### `AEAPromptRequest` (adw.core.aea_data_types)

Request to send a prompt to an agent
- **Inherits**: BaseModel

### `AEAPromptResponse` (adw.core.aea_data_types)

Response after sending prompt to agent
- **Inherits**: BaseModel

### `AEANewAgentResponse` (adw.core.aea_data_types)

Response when creating a new agent
- **Inherits**: BaseModel

### `AEAServerStatus` (adw.core.aea_data_types)

Server health check response
- **Inherits**: BaseModel

### `AEAEndAgentRequest` (adw.core.aea_data_types)

Request to archive/end an agent session
- **Inherits**: BaseModel

### `PortConfig` (adw.core.config)

- **Decorators**: dataclass

### `ADWConfig` (adw.core.config)

- **Decorators**: dataclass
- **Key Methods**:
  - `load()`: Load configuration from .adw.yaml in project root.
  - `get_project_artifacts_dir()`: Get the artifacts directory for this specific project.
  - `get_agents_dir()`: Get directory for agent state and logs.
  - `get_trees_dir()`: Get base directory for worktrees.

### `RetryCode` (adw.core.data_types)

Codes indicating different types of errors that may be retryable.
- **Inherits**: str, Enum

### `GitHubUser` (adw.core.data_types)

GitHub user model.
- **Inherits**: BaseModel

### `GitHubLabel` (adw.core.data_types)

GitHub label model.
- **Inherits**: BaseModel

### `GitHubMilestone` (adw.core.data_types)

GitHub milestone model.
- **Inherits**: BaseModel

### `GitHubComment` (adw.core.data_types)

GitHub comment model.
- **Inherits**: BaseModel

### `GitHubIssueListItem` (adw.core.data_types)

GitHub issue model for list responses (simplified).
- **Inherits**: BaseModel

### `GitHubIssue` (adw.core.data_types)

GitHub issue model.
- **Inherits**: BaseModel

### `AgentPromptRequest` (adw.core.data_types)

Claude Code agent prompt configuration.
- **Inherits**: BaseModel

### `AgentPromptResponse` (adw.core.data_types)

Claude Code agent response.
- **Inherits**: BaseModel

### `AgentTemplateRequest` (adw.core.data_types)

Claude Code agent template execution request.
- **Inherits**: BaseModel

### `ClaudeCodeResultMessage` (adw.core.data_types)

Claude Code JSONL result message (last line).
- **Inherits**: BaseModel

### `TestResult` (adw.core.data_types)

Individual test result from test suite execution.
- **Inherits**: BaseModel

### `E2ETestResult` (adw.core.data_types)

Individual E2E test result from browser automation.
- **Inherits**: BaseModel
- **Key Methods**:
  - `passed()`: Check if test passed.

### `ADWStateData` (adw.core.data_types)

Minimal persistent state for ADW workflow.
- **Inherits**: BaseModel

### `ReviewIssue` (adw.core.data_types)

Individual review issue found during spec verification.
- **Inherits**: BaseModel

### `ReviewResult` (adw.core.data_types)

Result from reviewing implementation against specification.
- **Inherits**: BaseModel

### `DocumentationResult` (adw.core.data_types)

Result from documentation generation workflow.
- **Inherits**: BaseModel

### `ADWExtractionResult` (adw.core.data_types)

Result from extracting ADW information from text.
- **Inherits**: BaseModel
- **Key Methods**:
  - `has_workflow()`: Check if a workflow command was extracted.

### `ADWState` (adw.core.state)

Container for ADW workflow state with file persistence.
- **Key Methods**:
  - `update()`: Update state with new key-value pairs.
  - `get()`: Get value from state by key.
  - `append_adw_id()`: Append an ADW ID to the all_adws list if not already present.
  - `get_working_directory()`: Get the working directory for this ADW instance.
  - `get_state_path()`: Get path to state file.

### `R2Uploader` (adw.integrations.r2_uploader)

Handle uploads to Cloudflare R2 public bucket.
- **Key Methods**:
  - `upload_file()`: Upload a file to R2 and return the public URL.
  - `upload_screenshots()`: Upload multiple screenshots and return mapping of local paths to public URLs.

## Module Documentation

### adw.core.__init__

ADW Core modules.

### adw.core.aea_data_types

AEA (Agent Embedded Application) Data Types
Data models for the AEA system using Pydantic

### adw.core.agent

Claude Code agent module for executing prompts programmatically.

### adw.core.config

Configuration management for ADW Framework.

### adw.core.data_types

Data types for GitHub API responses and Claude Code agent.

### adw.core.state

State management for ADW composable architecture.

### adw.core.utils

Utility functions for ADW system.

### adw.integrations.__init__

ADW Integration modules for external services.

### adw.integrations.git_ops

Git operations for ADW composable architecture.

### adw.integrations.github

GitHub Operations Module - AI Developer Workflow (ADW)

### adw.integrations.r2_uploader

Cloudflare R2 uploader for ADW screenshots.

### adw.integrations.workflow_ops

Shared AI Developer Workflow (ADW) operations.

### adw.integrations.worktree_ops

Worktree and port management operations for isolated ADW workflows.

### adw.triggers.adw_trigger_aea_server

AEA (Agent Embedded Application) Server
FastAPI server for managing AI agent sessions

### adw.triggers.trigger_cron

Cron-based ADW trigger system that monitors GitHub issues and automatically processes them.

### adw.triggers.trigger_webhook

GitHub Webhook Trigger - AI Developer Workflow (ADW)

### adw.workflows.build

ADW Build Iso - AI Developer Workflow for agentic building in isolated worktrees

### adw.workflows.document

ADW Document Iso - AI Developer Workflow for documentation generation in isolated worktrees

### adw.workflows.patch

ADW Patch Isolated - AI Developer Workflow for single-issue patches with worktree isolation

### adw.workflows.plan

ADW Plan Iso - AI Developer Workflow for agentic planning in isolated worktrees

### adw.workflows.plan_build

ADW Plan Build Iso - Compositional workflow for isolated planning and building

### adw.workflows.plan_build_document

ADW Plan Build Document Iso - Compositional workflow for isolated planning, building, and documentation

### adw.workflows.plan_build_review

ADW Plan Build Review Iso - Compositional workflow for isolated planning, building, and reviewing

### adw.workflows.plan_build_test

ADW Plan Build Test Iso - Compositional workflow for isolated planning, building, and testing

### adw.workflows.plan_build_test_review

ADW Plan Build Test Review Iso - Compositional workflow for isolated planning, building, testing, and reviewing

### adw.workflows.review

ADW Review Iso - AI Developer Workflow for agentic review in isolated worktrees

### adw.workflows.sdlc

ADW SDLC Iso - Complete Software Development Life Cycle workflow with isolation

### adw.workflows.sdlc_zte

ADW SDLC ZTE Iso - Zero Touch Execution: Complete SDLC with automatic shipping

### adw.workflows.ship

ADW Ship Iso - AI Developer Workflow for shipping (merging) to main

### adw.workflows.test

ADW Test Iso - AI Developer Workflow for agentic testing in isolated worktrees

## Diagrams

See accompanying diagram files:
- `module_structure.mmd` - Package/module hierarchy
- `class_diagram.mmd` - Class relationships
- `dependencies.mmd` - Internal import dependencies
- `dependency_graph.svg` - Visual dependency graph (pydeps)
