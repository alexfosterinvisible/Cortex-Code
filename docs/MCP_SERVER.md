# CxC MCP Server Documentation (Claude)

## 1. Overview

The CxC MCP (Model Context Protocol) server exposes the CxC Framework's functionality as MCP tools, enabling Claude Desktop and other MCP clients to interact with the full SDLC automation pipeline.

### What the MCP Server Exposes

The server provides 24 tools organized into four categories:

1. **SDLC Orchestration (9 tools)** - Complete software development lifecycle automation
2. **GitHub Operations (5 tools)** - Issue management and repository interaction
3. **Git Operations (7 tools)** - Branch management, commits, and pull requests
4. **Workflow State (3 tools)** - State persistence and workflow metadata

### Tool Categories

| Category | Tools | Purpose |
|----------|-------|---------|
| SDLC Orchestration | `cxc_plan`, `cxc_build`, `cxc_test`, `cxc_review`, `cxc_document`, `cxc_ship`, `cxc_sdlc`, `cxc_zte`, `cxc_patch` | Full lifecycle automation from issue to production |
| GitHub Operations | `fetch_github_issue`, `post_issue_comment`, `list_open_issues`, `get_repository_url`, `close_github_issue` | GitHub API interactions |
| Git Operations | `get_current_branch`, `create_git_branch`, `commit_changes`, `push_branch`, `check_pr_exists`, `merge_pull_request`, `approve_pull_request` | Git repository management |
| Workflow State | `load_cxc_state`, `get_cxc_state_value`, `list_available_workflows` | Workflow tracking and state management |

---

## 2. Installation

### Prerequisites

| Requirement | Minimum Version | Installation |
|-------------|-----------------|--------------|
| Python | 3.10+ | `brew install python@3.10` |
| uv package manager | Latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| GitHub CLI | Latest | `brew install gh` |
| Git | 2.x+ | `brew install git` |

### Authenticate GitHub CLI

```bash
gh auth login
```

Follow the prompts to authenticate with your GitHub account.

### Install CxC Framework

```bash
cd /Users/dev3/code4b/cxc-framework
uv sync  # Installs all dependencies and the cxc package
```

Alternatively, if you're installing in development mode:

```bash
uv pip install -e .
```

---

## 3. Running the Server

### Verify Installation

Check that the MCP server command is available:

```bash
uv run cxc-mcp --help
```

### Direct Execution

Activate the virtual environment and run the server:

```bash
source .venv/bin/activate
cxc-mcp
```

The server will run in stdio mode, waiting for MCP protocol messages on stdin.

### With uv (Recommended)

Run without activating the virtual environment:

```bash
uv run cxc-mcp
```

This automatically uses the correct Python environment.

### Test with MCP Inspector

The MCP Inspector is a development tool for testing MCP servers:

```bash
npm install -g @modelcontextprotocol/inspector
mcp dev cxc/mcp_server.py
```

This opens a web interface at `http://localhost:5173` where you can:
- List all available tools
- Test tool execution with parameters
- View server logs in real-time

---

## 4. Claude Code Integration (CLI)

The recommended way to use the CxC MCP server with Claude Code CLI.

### Automatic Setup (Recommended)

Run the setup script from your target project:

```bash
cd ~/code/your-project
python ../cxc-framework/setup_cxc_example.py
```

This creates `.mcp.json` in your project with the correct relative path.

### Manual Setup

Create `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "cxc": {
      "command": "uv",
      "args": [
        "--directory",
        "../cxc-framework",
        "run",
        "cxc-mcp"
      ]
    }
  }
}
```

**Note**: Adjust `../cxc-framework` to match your relative path to the cxc-framework directory.

### Verify MCP is Loaded

```bash
claude mcp list
# Should show: cxc (project)
```

Or start Claude Code and type `/mcp` to see available servers.

---

## 5. Claude Desktop Integration

For Claude Desktop (the macOS app), use the global config file.

### Configuration File Location

The Claude Desktop configuration file is located at:

```
~/Library/Application Support/Claude/claude_desktop_config.json
```

### Add CxC Server Configuration

Edit the configuration file to add the CxC MCP server:

```json
{
  "mcpServers": {
    "cxc": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/cxc-framework",
        "run",
        "cxc-mcp"
      ]
    }
  }
}
```

### Important Notes

- **Absolute Path Required**: Claude Desktop requires absolute paths (unlike Claude Code which supports relative paths in `.mcp.json`)
- **Restart Claude Desktop**: After editing the config, completely quit Claude Desktop (Cmd+Q), not just close the window
- **Verify Server Running**: Look for the "CxC" indicator in Claude Desktop's toolbar

### Troubleshooting Configuration

If the server doesn't appear in Claude Desktop:

1. Check the config file syntax with a JSON validator
2. Verify the path to cxc-framework is correct
3. Ensure uv is in your PATH: `which uv`
4. Check Claude Desktop logs: `~/Library/Logs/Claude/mcp*.log`

---

## 6. Tool Reference

### SDLC Orchestration Tools

#### `cxc_plan`

Plan implementation for a GitHub issue. This is the first step in the SDLC workflow.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_number` | string | Yes | GitHub issue number to plan |
| `cxc_id` | string | No | CxC workflow ID (auto-generated if omitted) |

**Returns**: Status message with plan file location

**Example**:
```json
{
  "issue_number": "42",
  "cxc_id": "cxc-20260106-123456"
}
```

---

#### `cxc_build`

Build implementation from an existing plan. Executes the implementation plan created by `cxc_plan`.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_number` | string | Yes | GitHub issue number |
| `cxc_id` | string | Yes | CxC workflow ID from planning phase |

**Returns**: Status message with implementation results

**Example**:
```json
{
  "issue_number": "42",
  "cxc_id": "cxc-20260106-123456"
}
```

---

#### `cxc_test`

Run tests for the implementation. Executes the test suite to validate the implementation.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_number` | string | Yes | GitHub issue number |
| `cxc_id` | string | Yes | CxC workflow ID |
| `skip_e2e` | boolean | No | Skip end-to-end tests (default: false) |

**Returns**: Test results summary

**Example**:
```json
{
  "issue_number": "42",
  "cxc_id": "cxc-20260106-123456",
  "skip_e2e": false
}
```

---

#### `cxc_review`

Review implementation against the specification. Validates that the implementation matches plan requirements.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_number` | string | Yes | GitHub issue number |
| `cxc_id` | string | Yes | CxC workflow ID |
| `skip_resolution` | boolean | No | Skip auto-resolution of issues (default: false) |

**Returns**: Review results summary

**Example**:
```json
{
  "issue_number": "42",
  "cxc_id": "cxc-20260106-123456",
  "skip_resolution": false
}
```

---

#### `cxc_document`

Generate documentation for the implementation. Creates or updates documentation based on changes made.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_number` | string | Yes | GitHub issue number |
| `cxc_id` | string | Yes | CxC workflow ID |

**Returns**: Documentation generation status

**Example**:
```json
{
  "issue_number": "42",
  "cxc_id": "cxc-20260106-123456"
}
```

---

#### `cxc_ship`

Ship changes by merging the pull request. Approves and merges the PR after validation.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_number` | string | Yes | GitHub issue number |
| `cxc_id` | string | Yes | CxC workflow ID |

**Returns**: Ship status with PR merge result

**Example**:
```json
{
  "issue_number": "42",
  "cxc_id": "cxc-20260106-123456"
}
```

---

#### `cxc_sdlc`

Run complete SDLC workflow for an issue. Executes: Plan → Build → Test → Review → Document

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_number` | string | Yes | GitHub issue number to process |
| `cxc_id` | string | No | CxC workflow ID (auto-generated if omitted) |
| `skip_e2e` | boolean | No | Skip end-to-end tests (default: false) |
| `skip_resolution` | boolean | No | Skip auto-resolution of review issues (default: false) |

**Returns**: Complete SDLC execution summary

**Example**:
```json
{
  "issue_number": "42",
  "skip_e2e": false,
  "skip_resolution": false
}
```

---

#### `cxc_zte`

Zero Touch Execution - Full SDLC with automatic ship. Runs complete SDLC AND automatically merges the PR. This is the fully autonomous issue-to-production pipeline.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_number` | string | Yes | GitHub issue number to process |
| `cxc_id` | string | No | CxC workflow ID (auto-generated if omitted) |
| `skip_e2e` | boolean | No | Skip end-to-end tests (default: false) |
| `skip_resolution` | boolean | No | Skip auto-resolution of review issues (default: false) |

**Returns**: Complete ZTE execution summary including merge status

**Example**:
```json
{
  "issue_number": "42"
}
```

---

#### `cxc_patch`

Create and implement a patch for an issue. Generates a patch plan and implements it directly. Useful for quick fixes and small changes.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_number` | string | Yes | GitHub issue number |
| `cxc_id` | string | No | CxC workflow ID (auto-generated if omitted) |

**Returns**: Patch implementation status

**Example**:
```json
{
  "issue_number": "42"
}
```

---

### GitHub Operations Tools

#### `fetch_github_issue`

Fetch a GitHub issue with full details. Retrieves issue data including title, body, labels, comments, and metadata.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_number` | string | Yes | GitHub issue number to fetch |

**Returns**: Dictionary containing issue data (title, body, state, labels, comments, etc.)

**Example**:
```json
{
  "issue_number": "42"
}
```

**Response Structure**:
```json
{
  "number": 42,
  "title": "Add user authentication",
  "body": "Implement JWT-based authentication...",
  "state": "open",
  "labels": ["feature", "backend"],
  "comments": [...]
}
```

---

#### `post_issue_comment`

Post a comment to a GitHub issue.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_number` | string | Yes | GitHub issue number |
| `comment` | string | Yes | Comment text to post |

**Returns**: Success message

**Example**:
```json
{
  "issue_number": "42",
  "comment": "Implementation plan has been created. Review at: /cxc-state/..."
}
```

---

#### `list_open_issues`

List all open issues in the repository.

**Parameters**: None

**Returns**: List of open issues with number, title, body, and labels

**Example Response**:
```json
[
  {
    "number": 42,
    "title": "Add user authentication",
    "body": "...",
    "labels": ["feature"]
  },
  {
    "number": 43,
    "title": "Fix login bug",
    "body": "...",
    "labels": ["bug"]
  }
]
```

---

#### `get_repository_url`

Get the GitHub repository URL from git remote origin.

**Parameters**: None

**Returns**: Repository URL string

**Example Response**:
```
https://github.com/username/repo-name.git
```

---

#### `close_github_issue`

Close a GitHub issue.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_number` | string | Yes | GitHub issue number to close |

**Returns**: Success or error message

**Example**:
```json
{
  "issue_number": "42"
}
```

---

### Git Operations Tools

#### `get_current_branch`

Get the current git branch name.

**Parameters**: None

**Returns**: Current branch name string

**Example Response**:
```
feature/issue-42-auth
```

---

#### `create_git_branch`

Create and checkout a new git branch.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `branch_name` | string | Yes | Name for the new branch |

**Returns**: Success or error message

**Example**:
```json
{
  "branch_name": "feature/issue-42-auth"
}
```

---

#### `commit_changes`

Stage all changes and create a commit.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message` | string | Yes | Commit message |

**Returns**: Success or error message

**Example**:
```json
{
  "message": "feat: implement JWT authentication"
}
```

---

#### `push_branch`

Push a branch to the remote repository.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `branch_name` | string | Yes | Branch name to push |

**Returns**: Success or error message

**Example**:
```json
{
  "branch_name": "feature/issue-42-auth"
}
```

---

#### `check_pr_exists`

Check if a pull request exists for a branch.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `branch_name` | string | Yes | Branch name to check |

**Returns**: PR URL if exists, or message indicating no PR

**Example**:
```json
{
  "branch_name": "feature/issue-42-auth"
}
```

---

#### `merge_pull_request`

Merge a pull request.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pr_number` | string | Yes | PR number to merge |
| `method` | string | No | Merge method: 'merge', 'squash', or 'rebase' (default: 'squash') |

**Returns**: Success or error message

**Example**:
```json
{
  "pr_number": "123",
  "method": "squash"
}
```

---

#### `approve_pull_request`

Approve a pull request.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pr_number` | string | Yes | PR number to approve |

**Returns**: Success or error message

**Example**:
```json
{
  "pr_number": "123"
}
```

---

### Workflow State Tools

#### `load_cxc_state`

Load CxC workflow state. Retrieves the persisted state for a workflow, including issue number, branch name, plan file, and other workflow data.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cxc_id` | string | Yes | CxC workflow ID |

**Returns**: Dictionary containing workflow state, or error message

**Example**:
```json
{
  "cxc_id": "cxc-20260106-123456"
}
```

**Response Structure**:
```json
{
  "issue_number": "42",
  "branch_name": "feature/issue-42-auth",
  "plan_file": "/path/to/plan.md",
  "cxc_id": "cxc-20260106-123456",
  "created_at": "2026-01-06T12:34:56Z"
}
```

---

#### `get_cxc_state_value`

Get a specific value from CxC workflow state.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cxc_id` | string | Yes | CxC workflow ID |
| `key` | string | Yes | State key to retrieve (e.g., 'issue_number', 'branch_name', 'plan_file') |

**Returns**: The value for the key, or error message

**Example**:
```json
{
  "cxc_id": "cxc-20260106-123456",
  "key": "branch_name"
}
```

**Common State Keys**:
- `issue_number` - GitHub issue number
- `branch_name` - Git branch name
- `plan_file` - Path to plan file
- `cxc_id` - Workflow identifier
- `created_at` - Workflow creation timestamp

---

#### `list_available_workflows`

List all available CxC workflows.

**Parameters**: None

**Returns**: List of workflow names and descriptions

**Example Response**:
```json
[
  {
    "name": "wt.plan_iso",
    "description": "Create implementation plan"
  },
  {
    "name": "wt.build_iso",
    "description": "Build from plan"
  },
  ...
]
```

---

## 7. Example Workflows

### Workflow 1: Zero Touch Execution (ZTE)

**Use Case**: Fully automated issue-to-production pipeline

```
1. Call cxc_zte
   Parameters: {"issue_number": "42"}

   Expected Result:
   - Creates plan
   - Implements code
   - Runs tests
   - Performs review
   - Generates documentation
   - Creates PR
   - Merges PR automatically
```

**When to Use**: For well-defined issues where full automation is desired

---

### Workflow 2: Manual SDLC with Review Checkpoints

**Use Case**: Run SDLC but review before merging

```
1. Call cxc_sdlc
   Parameters: {"issue_number": "42"}

   Expected Result:
   - Completes Plan → Build → Test → Review → Document
   - Creates PR but does NOT merge

2. Review the PR manually in GitHub

3. If approved, call cxc_ship
   Parameters: {"issue_number": "42", "cxc_id": "cxc-20260106-123456"}

   Expected Result:
   - PR is approved and merged
```

**When to Use**: For critical changes requiring human review before merge

---

### Workflow 3: Step-by-Step SDLC

**Use Case**: Maximum control over each phase

```
1. Call cxc_plan
   Parameters: {"issue_number": "42"}
   Result: Returns cxc_id (e.g., "cxc-20260106-123456")

2. Review the plan file

3. Call cxc_build
   Parameters: {"issue_number": "42", "cxc_id": "cxc-20260106-123456"}
   Result: Implementation complete

4. Call cxc_test
   Parameters: {"issue_number": "42", "cxc_id": "cxc-20260106-123456"}
   Result: Test results

5. Call cxc_review
   Parameters: {"issue_number": "42", "cxc_id": "cxc-20260106-123456"}
   Result: Review findings

6. Call cxc_document
   Parameters: {"issue_number": "42", "cxc_id": "cxc-20260106-123456"}
   Result: Documentation updated

7. Call cxc_ship
   Parameters: {"issue_number": "42", "cxc_id": "cxc-20260106-123456"}
   Result: PR merged
```

**When to Use**: For learning, debugging, or complex issues requiring manual intervention

---

### Workflow 4: Quick Patch

**Use Case**: Small bug fix or minor change

```
1. Call cxc_patch
   Parameters: {"issue_number": "42"}

   Expected Result:
   - Creates lightweight patch plan
   - Implements fix directly
   - Creates commit
```

**When to Use**: For hotfixes and minor changes that don't require full SDLC

---

### Workflow 5: Issue Triage and Planning

**Use Case**: Review and plan multiple issues

```
1. Call list_open_issues
   Result: List of all open issues

2. For each interesting issue, call fetch_github_issue
   Parameters: {"issue_number": "42"}
   Result: Full issue details with comments

3. Call cxc_plan to create implementation plan
   Parameters: {"issue_number": "42"}

4. Call post_issue_comment to add planning notes
   Parameters: {
     "issue_number": "42",
     "comment": "Implementation plan created at /cxc-state/..."
   }
```

**When to Use**: For backlog grooming and sprint planning

---

### Workflow 6: State Recovery

**Use Case**: Resume interrupted workflow

```
1. Call load_cxc_state
   Parameters: {"cxc_id": "cxc-20260106-123456"}
   Result: Full workflow state

2. Check which phase was completed

3. Continue from the next phase:
   - If plan exists but no build → call cxc_build
   - If build exists but no tests → call cxc_test
   - etc.
```

**When to Use**: When workflows are interrupted or need to be resumed later

---

## 8. Troubleshooting

### Common Issues and Solutions

| Issue | Symptoms | Solution |
|-------|----------|----------|
| **gh: command not found** | Tool calls fail with "gh not found" | Install GitHub CLI: `brew install gh && gh auth login` |
| **No git remote** | "Could not determine repository URL" | Ensure you're in a git repo with remote: `git remote -v` |
| **Server hangs** | Claude Desktop shows "thinking" indefinitely | Check server stderr for errors. Ensure nothing prints to stdout (reserved for MCP protocol) |
| **Permission denied** | Git operations fail with permission errors | Check GitHub authentication: `gh auth status` |
| **Invalid JSON config** | Server doesn't appear in Claude Desktop | Validate JSON at jsonlint.com |
| **Wrong Python version** | Import errors or syntax errors | Verify Python 3.10+: `python --version` |
| **uv not found** | Cannot start server | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **Workflow state not found** | "No state found for CxC ID" | Verify the cxc_id is correct. Check `/cxc-state/` directory |

---

### Debug Mode

Enable debug logging by setting the log level:

```python
# In cxc/mcp_server.py, change:
logging.basicConfig(level=logging.DEBUG, ...)
```

Then restart the server and check stderr output.

---

### Verify Server Health

Test the server manually:

```bash
# Start the server
uv run cxc-mcp

# In another terminal, send test input
echo '{"jsonrpc":"2.0","method":"initialize","id":1}' | uv run cxc-mcp
```

You should see valid JSON-RPC responses.

---

### Check Claude Desktop Logs

If the server doesn't appear in Claude Desktop:

```bash
# View MCP server logs
cat ~/Library/Logs/Claude/mcp*.log

# Watch logs in real-time
tail -f ~/Library/Logs/Claude/mcp*.log
```

Look for errors related to server startup or tool registration.

---

### Common Configuration Mistakes

1. **Relative paths in config** - Always use absolute paths
2. **Wrong command** - Must be `uv`, not `python` or `cxc-mcp`
3. **Missing args** - Need both `--directory` and `run` args
4. **Typos in server name** - Must match exactly in prompts
5. **Not restarting Claude Desktop** - Config changes require full restart (Cmd+Q)

---

### Getting Help

- **Framework Issues**: Check `/Users/dev3/code4b/cxc-framework/docs/`
- **MCP Protocol**: https://modelcontextprotocol.io/
- **GitHub CLI**: `gh --help` or https://cli.github.com/
- **Server Logs**: Check stderr output when running `uv run cxc-mcp`

---

## Appendix: MCP Protocol Notes

### stdio Transport

The CxC MCP server uses stdio transport, meaning:
- **stdin** receives JSON-RPC requests
- **stdout** sends JSON-RPC responses
- **stderr** is for logging (doesn't interfere with protocol)

### Tool Discovery

Claude Desktop automatically discovers all tools decorated with `@mcp.tool()`. No manual registration needed.

### Error Handling

All tools return either:
- Success strings/dicts
- Error messages prefixed with "Error:" or "Failed to"

This allows Claude to understand what went wrong and retry or adjust.
