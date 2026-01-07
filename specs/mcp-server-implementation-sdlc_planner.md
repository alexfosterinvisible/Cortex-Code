# Feature: MCP Server Implementation

## Metadata
issue_number: `N/A`
cxc_id: `mcp-server-2026`
issue_json: `{"title": "Convert CxC Framework to MCP Server", "body": "Boss wants this as an MCP server"}`

## Feature Description
Expose the CxC Framework's full CLI functionality via the Model Context Protocol (MCP), enabling Claude Desktop and other MCP clients to interact with the complete SDLC automation pipeline. This includes all workflow orchestration tools (plan, build, test, review, document, ship, sdlc, zte), GitHub operations, git operations, and workflow state management.

## User Story
As a Claude Desktop user
I want to access CxC Framework functionality through MCP tools
So that I can orchestrate issue-to-PR workflows directly from my AI assistant

## Problem Statement
The CxC Framework provides powerful SDLC automation capabilities through a CLI interface, but this requires manual terminal interaction. Users want to leverage these capabilities directly from Claude Desktop or other MCP-compatible clients without switching contexts or running terminal commands manually.

## Solution Statement
Create an MCP server that wraps all CLI commands and integration functions as MCP tools using FastMCP. The server exposes 24 tools organized into four categories: SDLC orchestration (9 tools), GitHub operations (5 tools), Git operations (7 tools), and workflow state management (3 tools). The server uses stdio transport for Claude Desktop integration.

## Relevant Files
Use these files to implement the feature:

- `cxc/cli.py` - CLI entry point showing all available commands and their argument structures
- `cxc/core/config.py` - Configuration management patterns
- `cxc/core/state.py` - CxCState class for workflow state persistence
- `cxc/core/data_types.py` - Pydantic models for structured data
- `cxc/integrations/github.py` - GitHub operations (fetch_issue, make_comment, etc.)
- `cxc/integrations/git_ops.py` - Git operations (branch, commit, push, PR management)
- `cxc/integrations/workflow_ops.py` - Workflow orchestration functions
- `cxc/integrations/worktree_ops.py` - Worktree isolation for parallel workflows
- `cxc/workflows/wt/*.py` - Isolated workflow implementations

### New Files
- `cxc/mcp_server.py` - Main MCP server with FastMCP tool definitions
- `docs/MCP_SERVER.md` - Comprehensive documentation for installation and usage
- `tests/test_mcp_server.py` - Unit tests for MCP server functionality

## Implementation Plan
### Phase 1: Foundation
- Install MCP dependency (`mcp>=1.0.0`)
- Create `mcp_server.py` with FastMCP initialization
- Set up logging to stderr (critical - stdout reserved for MCP protocol)
- Import all required CxC modules

### Phase 2: Core Implementation
- Implement `_run_workflow()` helper to execute CLI workflows via importlib
- Define SDLC orchestration tools: `cxc_plan`, `cxc_build`, `cxc_test`, `cxc_review`, `cxc_document`, `cxc_ship`, `cxc_sdlc`, `cxc_zte`, `cxc_patch`
- Define GitHub operation tools: `fetch_github_issue`, `post_issue_comment`, `list_open_issues`, `get_repository_url`, `close_github_issue`
- Define Git operation tools: `get_current_branch`, `create_git_branch`, `commit_changes`, `push_branch`, `check_pr_exists`, `merge_pull_request`, `approve_pull_request`
- Define state management tools: `load_cxc_state`, `get_cxc_state_value`, `list_available_workflows`

### Phase 3: Integration
- Add `cxc-mcp` entry point to `pyproject.toml`
- Create comprehensive documentation with installation, config, and troubleshooting
- Write unit tests covering imports, tool registration, signatures, and functionality
- Verify Claude Desktop integration works with provided config JSON

## Step by Step Tasks

### Task 1: Add MCP Dependency
- Add `mcp>=1.0.0` to `pyproject.toml` dependencies
- Run `uv sync` to install the package
- Verify import works: `from mcp.server.fastmcp import FastMCP`

### Task 2: Create MCP Server Foundation
- Create `cxc/mcp_server.py` with:
  - FastMCP initialization: `mcp = FastMCP("cxc")`
  - Logging configured to stderr
  - All required imports from CxC modules
  - Placeholder comments for tool categories

### Task 3: Implement Workflow Runner Helper
- Create `_run_workflow(module_name, args)` function
- Use `importlib.import_module()` to load workflow modules
- Patch `sys.argv` before calling `module.main()`
- Return success/error messages

### Task 4: Implement SDLC Tools
- `cxc_plan(issue_number, cxc_id=None)` - Plan implementation
- `cxc_build(issue_number, cxc_id)` - Build from plan
- `cxc_test(issue_number, cxc_id, skip_e2e=False)` - Run tests
- `cxc_review(issue_number, cxc_id, skip_resolution=False)` - Review
- `cxc_document(issue_number, cxc_id)` - Generate docs
- `cxc_ship(issue_number, cxc_id)` - Merge PR
- `cxc_sdlc(issue_number, cxc_id=None, skip_e2e=False, skip_resolution=False)` - Full SDLC
- `cxc_zte(...)` - Zero Touch Execution
- `cxc_patch(issue_number, cxc_id=None)` - Quick patch

### Task 5: Implement GitHub Tools
- `fetch_github_issue(issue_number)` - Returns dict with issue data
- `post_issue_comment(issue_number, comment)` - Posts comment
- `list_open_issues()` - Returns list of open issues
- `get_repository_url()` - Returns repo URL
- `close_github_issue(issue_number)` - Closes issue

### Task 6: Implement Git Tools
- `get_current_branch()` - Returns branch name
- `create_git_branch(branch_name)` - Creates and checks out branch
- `commit_changes(message)` - Stages and commits
- `push_branch(branch_name)` - Pushes to remote
- `check_pr_exists(branch_name)` - Returns PR URL or message
- `merge_pull_request(pr_number, method="squash")` - Merges PR
- `approve_pull_request(pr_number)` - Approves PR

### Task 7: Implement State Tools
- `load_cxc_state(cxc_id)` - Returns state dict or error
- `get_cxc_state_value(cxc_id, key)` - Returns specific value
- `list_available_workflows()` - Returns workflow list

### Task 8: Add Entry Point
- Add to `pyproject.toml`: `cxc-mcp = "cxc.mcp_server:main"`
- Verify entry point: `which cxc-mcp`

### Task 9: Create Documentation
- Create `docs/MCP_SERVER.md` with:
  - Installation prerequisites and steps
  - Running the server (direct, uv, inspector)
  - Claude Desktop integration config
  - Complete tool reference with params and examples
  - Example workflows (ZTE, step-by-step, patch, etc.)
  - Troubleshooting guide

### Task 10: Create Tests
- Create `tests/test_mcp_server.py` with:
  - Import and initialization tests
  - Tool registration tests (all 24 tools)
  - Tool signature tests (docstrings, params)
  - Entry point tests
  - Basic functionality tests (mocked)

### Task 11: Run Validation Commands
- Verify server imports without errors
- Run pytest on new tests
- Verify tool count is 24

## Testing Strategy
### Unit Tests
- Test MCP server module imports correctly
- Test FastMCP instance has name "cxc"
- Test all 24 tools are registered
- Test each tool has correct signature and docstring
- Test `main()` entry point exists
- Test mocked tool functionality (git, github, state operations)

### Edge Cases
- Invalid CxC ID returns error dict
- Missing state key returns error message
- Git/GitHub failures return error messages
- Workflow import errors return error messages

## Acceptance Criteria
- [ ] MCP server imports without errors
- [ ] FastMCP instance named "cxc" is created
- [ ] 24 tools are registered (9 SDLC + 5 GitHub + 7 Git + 3 State)
- [ ] Each tool has type hints and docstrings
- [ ] `cxc-mcp` entry point is available
- [ ] All 42 unit tests pass
- [ ] Documentation covers installation, config, and usage
- [ ] Claude Desktop config JSON is provided

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `source .venv/bin/activate && python -c "from cxc.mcp_server import mcp; print(f'Tools: {len(mcp._tool_manager._tools)}')"` - Verify 24 tools registered
- `source .venv/bin/activate && which cxc-mcp` - Verify entry point exists
- `source .venv/bin/activate && python -m pytest tests/test_mcp_server.py -v` - Run all tests with zero failures
- `source .venv/bin/activate && python -c "from cxc.mcp_server import main; print('Entry point OK')"` - Verify main() exists

## Notes
- MCP servers using stdio transport MUST NOT print to stdout (reserved for JSON-RPC)
- All logging must go to stderr
- Claude Desktop requires absolute paths in config
- After config changes, Claude Desktop needs full restart (Cmd+Q)
- FastMCP automatically generates JSON Schema from type hints
- Tools can be sync or async (we used sync for simplicity)
