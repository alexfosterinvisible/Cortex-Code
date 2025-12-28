# ADW Verification Setup Guide (Claude)

This guide documents how to replicate the ADW SDLC workflow test to validate the framework's functionality.

## Context

We tested the ADW SDLC workflow in `/Users/dev3/code4b/adw-temp-verification` to verify the end-to-end developer workflow automation.

## Key Steps to Replicate

### 1. Create Target Project Directory

```bash
mkdir -p /path/to/new-project
cd /path/to/new-project
git init
```

### 2. Create a Simple Python Project

For testing, we used a simple `mathcalc` project with a `Calculator` class. Any simple Python project will work for verification purposes.

### 3. Add adw-framework Dependency

```bash
uv add /path/to/adw-framework
```

### 4. CRITICAL: Set Up .env File BEFORE Running Setup or Workflow

⚠️ **This must be done BEFORE running any ADW commands.**

Copy from a working project or create a new `.env` file with these required keys:

```bash
ANTHROPIC_API_KEY=your_key_here
GITHUB_PAT=your_pat_here  # Optional if using gh auth
CLAUDE_CODE_PATH=/path/to/.claude/local/claude
```

**IMPORTANT:** Never delete or modify the `.env` during workflow execution. The workflow relies on these credentials throughout its lifecycle.

### 5. CRITICAL: Add .gitignore BEFORE Running Workflow

⚠️ **This prevents GitHub push protection from blocking pushes with secrets.**

Create `.gitignore` with:

```
.env
.venv/
__pycache__/
*.pyc
artifacts/
agents/
```

### 6. Create GitHub Repo and Push

```bash
gh repo create projectname --public --source=.
git push -u origin main
```

### 7. Run ADW Setup Script

```bash
uv run python /path/to/adw-framework/setup_adw_example.py
```

This script sets up the necessary ADW configuration files and example commands.

### 8. Create a GitHub Issue

Create a GitHub issue for the workflow to process. This issue should describe a feature or bug fix that can be implemented.

### 9. Run SDLC Workflow

```bash
uv run adw sdlc <issue-number> --skip-e2e
```

The workflow will:
- Create a worktree for the issue
- Analyze the issue and create a plan
- Implement the changes
- Run tests
- Create a pull request
- (Optionally) Review and ship

## Quirks and Gotchas

### 1. Package Reinstallation

After modifying `adw-framework` source code, you **MUST** reinstall it in the target project:

```bash
uv add --reinstall /path/to/adw-framework
```

Without this, changes to the framework won't be reflected in the target project.

### 2. Worktree Location

Currently creates worktrees inside `.venv/lib/python3.11/trees/` which is unusual and may cause confusion.

**Future improvement:** Consider fixing this to use project root `trees/` directory instead.

### 3. Module Execution Pattern

`sdlc.py` now uses `python -m adw.workflows.{module}` instead of direct file paths. This was a fix we implemented to ensure proper module resolution.

Example:
```python
# Old (broken)
subprocess.run([python, str(plan_file), ...])

# New (working)
subprocess.run([python, "-m", "adw.workflows.plan", ...])
```

### 4. State Persistence

ADW state is stored in the `artifacts/` directory, keyed by repo and ADW ID. This directory contains:
- Workflow state
- Generated artifacts
- Command history
- Agent outputs

Make sure to `.gitignore` this directory to avoid committing temporary state.

## Hypotheses Not Yet Validated

The following aspects of the ADW workflow have not been fully tested:

1. **Ship phase with automatic PR approval** - Haven't reached this phase yet in testing
2. **Close issue functionality after merge** - Not tested in the verification run
3. **`--skip-resolution` flag behavior in review phase** - Flag exists but behavior not validated
4. **Multiple concurrent SDLC runs on same repo** - Unclear if state management supports this
5. **Recovery after interrupted workflow** - What happens if workflow crashes mid-execution?

These should be tested in future verification runs.

## Files Changed in adw-framework

During the verification process, we made the following fixes to `adw-framework`:

### 1. `adw/workflows/sdlc.py`
- Changed to module execution pattern (`python -m adw.workflows.plan` instead of direct file paths)
- Ensures proper Python module resolution

### 2. `adw/workflows/sdlc_zte.py`
- Applied same module execution fix as `sdlc.py`

### 3. `adw/workflows/ship.py`
- Fixed path calculation for proper module imports
- Added PR approval functionality
- Added issue close functionality after successful merge

### 4. `adw/github.py`
- Added `approve_pr()` function for automatic PR approval
- Added `close_issue()` function to close issues after merge

### 5. `setup_adw_example.py`
- Fixed to properly copy `examples/` subdirectory commands
- Ensures example commands are available in target projects

## Troubleshooting

### Workflow fails with import errors
- Ensure you've reinstalled adw-framework after making changes
- Check that all `__init__.py` files exist in the package hierarchy

### GitHub push rejected due to secrets
- Verify `.gitignore` includes `.env` before first commit
- If already committed, you'll need to remove from git history

### Workflow can't find Claude Code
- Verify `CLAUDE_CODE_PATH` in `.env` points to the correct location
- Default is typically `/Users/username/.claude/local/claude`

### State persistence issues
- Check that `artifacts/` directory has proper write permissions
- Verify the ADW ID is consistent across workflow runs

## Next Steps

After successful verification:

1. Run a complete workflow without `--skip-e2e` to test end-to-end testing
2. Test the ship phase with PR approval
3. Validate issue closure after merge
4. Test concurrent SDLC runs
5. Test workflow recovery after interruption
