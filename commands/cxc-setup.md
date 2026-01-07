# CxC Framework Setup & Orchestrator Reference

Complete reference for setting up and running CxC (Cortex Code) in any repository.

---

## Quick Setup (New Repo)

### 1. Add CxC as Dependency

```bash
cd /path/to/your-project

# For active development (recommended - changes in CxC source reflect immediately):
uv add --editable /Users/dev3/code4b/cxc-framework

# OR for dev-only usage:
uv add --dev --editable /Users/dev3/code4b/cxc-framework

# OR for stable production use (copies files, no live updates):
uv add /Users/dev3/code4b/cxc-framework

uv sync
```

### 2. Create [.env] (REQUIRED)

```bash
# Copy template and fill in your values
cp /Users/dev3/code4b/cxc-framework/env.example .env

# Edit .env with required values:
#   ANTHROPIC_API_KEY=sk-ant-xxxxx
#   GITHUB_PAT=ghp_xxxxx
#   GITHUB_REPO_URL=https://github.com/your-org/your-repo.git
#   CLAUDE_CODE_PATH=/usr/local/bin/claude
```

### 3. Create [.cxc.yaml] (REQUIRED)

```bash
cp /Users/dev3/code4b/cxc-framework/templates/cxc.yaml .cxc.yaml
# Edit project_id in .cxc.yaml (org/repo)
```

### 4. (Optional) Customize Commands

**Note:** CxC automatically uses framework commands. Only copy if you need to customize.

```bash
# Copy only specific commands you want to override:
mkdir -p .claude/commands
cp /Users/dev3/code4b/cxc-framework/commands/feature.md .claude/commands/
# Edit feature.md to match your project structure

# Add to .cxc.yaml:
# commands:
#   - "${CxC_FRAMEWORK}/commands"
#   - ".claude/commands"
```

### 5. Verify Setup

```bash
uv run cxc --help
# Should show: plan, build, test, review, document, ship, sdlc, zte, etc.

# Test config loading
uv run python -c "from cxc.core.config import CxCConfig; c = CxCConfig.load(); print(f'project_id: {c.project_id}')"
```

---

## Core Commands

### Individual Phases

| Command                      | Purpose                                        | Creates CxC ID? |
|------------------------------|------------------------------------------------|-----------------|
| cxc plan <issue>             | Classify → Branch → Worktree → Plan spec       | ✅ Yes          |
| cxc build <issue> <id>       | Implement plan in worktree                     | ❌ No           |
| cxc test <issue> <id>        | Run tests, auto-fix (3 retries)                | ❌ No           |
| cxc review <issue> <id>      | Validate against spec                          | ❌ No           |
| cxc document <issue> <id>    | Generate docs                                  | ❌ No           |
| cxc ship <issue> <id>        | Approve + squash merge PR                      | ❌ No           |

### Composite Workflows

| Command                          | Phases                                    | Auto-Merge?     |
|-----------------------------------|-------------------------------------------|-----------------|
| cxc sdlc <issue> [--skip-e2e]     | plan→build→test→review→document           | ❌ Manual       |
| cxc zte <issue>                   | plan→build→test→review→document→ship      | ✅ Auto ⚠️      |


### Utility Commands

```bash
cxc monitor           # Poll GitHub every 20s for new issues
cxc webhook           # Real-time GitHub webhook listener
cxc cleanup <id>      # Remove worktree and clean state
```

---

## Issue Classification Flow

CxC uses `/classify_issue` to route issues:

```
GitHub Issue → classify_issue → Command Selected
                    │
    ┌───────────────┼───────────────┬───────────────┐
    ▼               ▼               ▼               ▼
 /chore          /bug          /feature          0 (stop)
    │               │               │
    ▼               ▼               ▼
 chore.md        bug.md        feature.md
 (simple)       (surgical)    (extensible)
```

### Classification Triggers

| Classification | Triggered By |
|---------------|--------------|
| `/chore` | Maintenance, docs, refactoring, cleanup |
| `/bug` | Something broken, error, regression |
| `/feature` | New functionality, enhancement |
| `/patch` | Quick targeted fix |
| `0` | Unrecognized → workflow stops |

---

## State & Logs

### Directory Structure

```
artifacts/
└── {github-owner}/
    └── {repo-name}/
        ├── {cxc_id}/                    # CxC state directory
        │   ├── cxc_state.json           # Persistent state
        │   ├── ops/                     # Orchestrator logs
        │   ├── issue_classifier/        # Classifier logs
        │   ├── sdlc_planner/            # Planning logs
        │   ├── sdlc_implementor/        # Build logs
        │   ├── tester/                  # Test logs
        │   ├── reviewer/                # Review logs
        │   │   └── review_img/          # Screenshots
        │   └── documenter/              # Documentation logs
        └── trees/
            └── {cxc_id}/                # Isolated git worktree
                ├── .ports.env           # Port assignments
                └── specs/               # Generated plan files
```

### State File ([cxc_state.json])

```json
{
  "cxc_id": "8035e781",
  "issue_number": "5",
  "branch_name": "feat-issue-5-cxc-8035e781-add-version-info-cli",
  "plan_file": "specs/issue-5-cxc-8035e781-sdlc_planner-add-version-info-cli.md",
  "issue_class": "/feature",
  "worktree_path": "/path/to/artifacts/.../trees/8035e781",
  "backend_port": 9101,
  "frontend_port": 9201,
  "model_set": "base",
  "all_cxcs": ["cxc_plan_iso", "cxc_build_iso", "cxc_test_iso"]
}
```

### Reading Logs

```bash
# Latest agent output (JSONL format)
cat artifacts/{org}/{repo}/{cxc_id}/sdlc_planner/raw_output.jsonl | tail -20

# Planning output as JSON
cat artifacts/{org}/{repo}/{cxc_id}/sdlc_planner/raw_output.json | jq .

# Full state
cat artifacts/{org}/{repo}/{cxc_id}/cxc_state.json | jq .

# Review screenshots
ls artifacts/{org}/{repo}/{cxc_id}/reviewer/review_img/
```

---

## Orchestrator Workflow

### Starting a New Issue

```bash
# 1. Create GitHub issue
gh issue create --title "[Feature] Add X" --body "## Goal\n..."

# 2. Run full SDLC (recommended)
uv run cxc sdlc <issue_number> --skip-e2e

# Or run phases individually:
uv run cxc plan <issue_number>
# Note the CxC ID from output
uv run cxc build <issue_number> <cxc_id>
uv run cxc test <issue_number> <cxc_id>
uv run cxc review <issue_number> <cxc_id>
```

### Resuming a Workflow

```bash
# Find existing CxC state
ls artifacts/*/*/cxc_state.json

# Resume with existing ID
uv run cxc build <issue_number> <existing_cxc_id>
```

### Checking Progress

```bash
# View PR status
gh pr view <pr_number>

# View issue comments (CxC posts progress)
gh issue view <issue_number> --comments

# Check worktree state
cd artifacts/{org}/{repo}/trees/<cxc_id>
git status
git log --oneline -5
```

### Cleanup

```bash
# Remove specific worktree
git worktree remove artifacts/{org}/{repo}/trees/<cxc_id>

# Or use CxC cleanup (if implemented)
uv run cxc cleanup <cxc_id>
```

---

## Orchestrator Decision Tree

```
┌─────────────────────────────────────────────────────────────┐
│                   New Task Arrives                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│           Is there a GitHub Issue for this?                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              ▼ NO                      ▼ YES
     ┌────────────────┐        ┌────────────────┐
     │ Create issue   │        │ Get issue #    │
     │ with gh cli    │        └───────┬────────┘
     └───────┬────────┘                │
             │                         │
             └────────────┬────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Run: uv run cxc sdlc <issue>                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Monitor Progress                           │
│  • Check gh issue view <n> --comments                        │
│  • Check gh pr view <n>                                      │
│  • Review worktree: cd artifacts/.../trees/<id>              │
└──────────────────────────┬──────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              ▼ FAILED                  ▼ SUCCESS
     ┌────────────────┐        ┌────────────────┐
     │ Check logs     │        │ Review PR      │
     │ Resume phase   │        │ Merge if OK    │
     │ with cxc_id    │        │ Clean up       │
     └────────────────┘        └────────────────┘
```

---

## Common Issues

### "Invalid command selected"
**Cause:** `classify_issue` returned empty or unexpected output  
**Fix:** Check issue title/body has clear intent (feature/bug/chore)

### "ModuleNotFoundError: cxc"
**Cause:** CxC not installed  
**Fix:** `uv add --editable /Users/dev3/code4b/cxc-framework`

### "No .cxc.yaml found"
**Cause:** Missing config file  
**Fix:** Create [.cxc.yaml] in project root (see Quick Setup)

### "ANTHROPIC_API_KEY not set"
**Cause:** Missing or incomplete [.env] file  
**Fix:** Copy [env.example] to [.env] and fill in all required values

### Network errors posting comments
**Cause:** Transient GitHub API failures  
**Fix:** Re-run with existing CxC ID: `uv run cxc <phase> <issue> <cxc_id>`

### Worktree already exists
**Cause:** Previous run left worktree  
**Fix:** `git worktree remove artifacts/{org}/{repo}/trees/<cxc_id>` then retry

### Port conflicts
**Cause:** Allocated ports in use  
**Fix:** CxC auto-finds alternatives, or change `backend_start`/`frontend_start` in [.cxc.yaml]

---

## Environment Requirements

- **`uv`** - Python package manager ([install](https://docs.astral.sh/uv/))
- **`gh`** - GitHub CLI ([install](https://cli.github.com/)) with authentication (`gh auth login`)
- **`git`** - Git with worktree support (2.5+)
- **Claude Code CLI** - For agent execution ([setup](https://docs.anthropic.com/en/docs/claude-code))
- **[.env]** - Environment variables (see Quick Setup)

---

## Example: Full Workflow

```bash
# 1. Setup (one-time)
cd /path/to/your-project
uv add --editable /Users/dev3/code4b/cxc-framework
uv sync

# Create .env with your API keys
cp /Users/dev3/code4b/cxc-framework/env.example .env
# Edit .env with your values

# Create .cxc.yaml
cp /Users/dev3/code4b/cxc-framework/templates/cxc.yaml .cxc.yaml
# Edit project_id in .cxc.yaml (org/repo)

# 2. Create issue
gh issue create \
  --title "[Feature] Add dark mode support" \
  --body "## Goal\nAdd dark mode toggle...\n\n## Acceptance Criteria\n- Toggle in settings\n- Persists preference"

# 3. Run SDLC
uv run cxc sdlc 7 --skip-e2e

# 4. Review & merge
gh pr view 8
gh pr merge 8 --squash

# 5. Cleanup
git worktree remove artifacts/your-org/your-repo/trees/<cxc_id>
```

---

## Model Selection

CxC supports two model sets controlled via issue/comment text:

```
model_set base   → Uses Sonnet for all commands (default)
model_set heavy  → Uses Opus for complex tasks
```

### Heavy Mode Commands (Opus)
- `/implement` - Complex implementations
- `/document` - Documentation generation
- `/resolve_failed_test` - Test debugging
- `/chore`, `/bug`, `/feature`, `/patch` - Planning tasks

Add to issue body or comment: `model_set heavy`

---

## Advanced: Parallel Execution

CxC supports up to 15 concurrent workflows:

```bash
# Process multiple issues in parallel
uv run cxc sdlc 101 &
uv run cxc sdlc 102 &
uv run cxc sdlc 103 &

# Each gets isolated:
# - Unique worktree: artifacts/.../trees/{cxc-id}/
# - Unique ports: Deterministically assigned from ID hash
# - Unique branch: {type}-issue-{n}-cxc-{id}-{slug}
```

---

**CxC ID Format:** 8-character hex (e.g., `8035e781`)  
**Branch Format:** `{type}-issue-{n}-cxc-{id}-{description}`  
**Plan Format:** [specs/issue-{n}-cxc-{id}-sdlc_planner-{description}.md]
