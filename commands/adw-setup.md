# ADW Framework Setup & Orchestrator Reference

Complete reference for setting up and running ADW (AI Developer Workflow) in any repository.

---

## Quick Setup (New Repo)

### 1. Add ADW as Dependency

```bash
cd /path/to/your-project

# For active development (recommended - changes in ADW source reflect immediately):
uv add --editable /Users/dev3/code4b/adw-framework

# OR for dev-only usage:
uv add --dev --editable /Users/dev3/code4b/adw-framework

# OR for stable production use (copies files, no live updates):
uv add /Users/dev3/code4b/adw-framework

uv sync
```

### 2. Create [.env] (REQUIRED)

```bash
# Copy template and fill in your values
cp /Users/dev3/code4b/adw-framework/env.example .env

# Edit .env with required values:
#   ANTHROPIC_API_KEY=sk-ant-xxxxx
#   GITHUB_PAT=ghp_xxxxx
#   GITHUB_REPO_URL=https://github.com/your-org/your-repo.git
#   CLAUDE_CODE_PATH=/usr/local/bin/claude
```

### 3. Create [.adw.yaml] (REQUIRED)

```bash
cp /Users/dev3/code4b/adw-framework/templates/adw.yaml .adw.yaml
# Edit project_id in .adw.yaml (org/repo)
```

### 4. (Optional) Customize Commands

**Note:** ADW automatically uses framework commands. Only copy if you need to customize.

```bash
# Copy only specific commands you want to override:
mkdir -p .claude/commands
cp /Users/dev3/code4b/adw-framework/commands/feature.md .claude/commands/
# Edit feature.md to match your project structure

# Add to .adw.yaml:
# commands:
#   - "${ADW_FRAMEWORK}/commands"
#   - ".claude/commands"
```

### 5. Verify Setup

```bash
uv run adw --help
# Should show: plan, build, test, review, document, ship, sdlc, zte, etc.

# Test config loading
uv run python -c "from adw.core.config import ADWConfig; c = ADWConfig.load(); print(f'project_id: {c.project_id}')"
```

---

## Core Commands

### Individual Phases

| Command                      | Purpose                                        | Creates ADW ID? |
|------------------------------|------------------------------------------------|-----------------|
| adw plan <issue>             | Classify → Branch → Worktree → Plan spec       | ✅ Yes          |
| adw build <issue> <id>       | Implement plan in worktree                     | ❌ No           |
| adw test <issue> <id>        | Run tests, auto-fix (3 retries)                | ❌ No           |
| adw review <issue> <id>      | Validate against spec                          | ❌ No           |
| adw document <issue> <id>    | Generate docs                                  | ❌ No           |
| adw ship <issue> <id>        | Approve + squash merge PR                      | ❌ No           |

### Composite Workflows

| Command                          | Phases                                    | Auto-Merge?     |
|-----------------------------------|-------------------------------------------|-----------------|
| adw sdlc <issue> [--skip-e2e]     | plan→build→test→review→document           | ❌ Manual       |
| adw zte <issue>                   | plan→build→test→review→document→ship      | ✅ Auto ⚠️      |


### Utility Commands

```bash
adw monitor           # Poll GitHub every 20s for new issues
adw webhook           # Real-time GitHub webhook listener
adw cleanup <id>      # Remove worktree and clean state
```

---

## Issue Classification Flow

ADW uses `/classify_issue` to route issues:

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
        ├── {adw_id}/                    # ADW state directory
        │   ├── adw_state.json           # Persistent state
        │   ├── ops/                     # Orchestrator logs
        │   ├── issue_classifier/        # Classifier logs
        │   ├── sdlc_planner/            # Planning logs
        │   ├── sdlc_implementor/        # Build logs
        │   ├── tester/                  # Test logs
        │   ├── reviewer/                # Review logs
        │   │   └── review_img/          # Screenshots
        │   └── documenter/              # Documentation logs
        └── trees/
            └── {adw_id}/                # Isolated git worktree
                ├── .ports.env           # Port assignments
                └── specs/               # Generated plan files
```

### State File ([adw_state.json])

```json
{
  "adw_id": "8035e781",
  "issue_number": "5",
  "branch_name": "feat-issue-5-adw-8035e781-add-version-info-cli",
  "plan_file": "specs/issue-5-adw-8035e781-sdlc_planner-add-version-info-cli.md",
  "issue_class": "/feature",
  "worktree_path": "/path/to/artifacts/.../trees/8035e781",
  "backend_port": 9101,
  "frontend_port": 9201,
  "model_set": "base",
  "all_adws": ["adw_plan_iso", "adw_build_iso", "adw_test_iso"]
}
```

### Reading Logs

```bash
# Latest agent output (JSONL format)
cat artifacts/{org}/{repo}/{adw_id}/sdlc_planner/raw_output.jsonl | tail -20

# Planning output as JSON
cat artifacts/{org}/{repo}/{adw_id}/sdlc_planner/raw_output.json | jq .

# Full state
cat artifacts/{org}/{repo}/{adw_id}/adw_state.json | jq .

# Review screenshots
ls artifacts/{org}/{repo}/{adw_id}/reviewer/review_img/
```

---

## Orchestrator Workflow

### Starting a New Issue

```bash
# 1. Create GitHub issue
gh issue create --title "[Feature] Add X" --body "## Goal\n..."

# 2. Run full SDLC (recommended)
uv run adw sdlc <issue_number> --skip-e2e

# Or run phases individually:
uv run adw plan <issue_number>
# Note the ADW ID from output
uv run adw build <issue_number> <adw_id>
uv run adw test <issue_number> <adw_id>
uv run adw review <issue_number> <adw_id>
```

### Resuming a Workflow

```bash
# Find existing ADW state
ls artifacts/*/*/adw_state.json

# Resume with existing ID
uv run adw build <issue_number> <existing_adw_id>
```

### Checking Progress

```bash
# View PR status
gh pr view <pr_number>

# View issue comments (ADW posts progress)
gh issue view <issue_number> --comments

# Check worktree state
cd artifacts/{org}/{repo}/trees/<adw_id>
git status
git log --oneline -5
```

### Cleanup

```bash
# Remove specific worktree
git worktree remove artifacts/{org}/{repo}/trees/<adw_id>

# Or use ADW cleanup (if implemented)
uv run adw cleanup <adw_id>
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
│              Run: uv run adw sdlc <issue>                    │
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
     │ with adw_id    │        │ Clean up       │
     └────────────────┘        └────────────────┘
```

---

## Common Issues

### "Invalid command selected"
**Cause:** `classify_issue` returned empty or unexpected output  
**Fix:** Check issue title/body has clear intent (feature/bug/chore)

### "ModuleNotFoundError: adw"
**Cause:** ADW not installed  
**Fix:** `uv add --editable /Users/dev3/code4b/adw-framework`

### "No .adw.yaml found"
**Cause:** Missing config file  
**Fix:** Create [.adw.yaml] in project root (see Quick Setup)

### "ANTHROPIC_API_KEY not set"
**Cause:** Missing or incomplete [.env] file  
**Fix:** Copy [env.example] to [.env] and fill in all required values

### Network errors posting comments
**Cause:** Transient GitHub API failures  
**Fix:** Re-run with existing ADW ID: `uv run adw <phase> <issue> <adw_id>`

### Worktree already exists
**Cause:** Previous run left worktree  
**Fix:** `git worktree remove artifacts/{org}/{repo}/trees/<adw_id>` then retry

### Port conflicts
**Cause:** Allocated ports in use  
**Fix:** ADW auto-finds alternatives, or change `backend_start`/`frontend_start` in [.adw.yaml]

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
uv add --editable /Users/dev3/code4b/adw-framework
uv sync

# Create .env with your API keys
cp /Users/dev3/code4b/adw-framework/env.example .env
# Edit .env with your values

# Create .adw.yaml
cp /Users/dev3/code4b/adw-framework/templates/adw.yaml .adw.yaml
# Edit project_id in .adw.yaml (org/repo)

# 2. Create issue
gh issue create \
  --title "[Feature] Add dark mode support" \
  --body "## Goal\nAdd dark mode toggle...\n\n## Acceptance Criteria\n- Toggle in settings\n- Persists preference"

# 3. Run SDLC
uv run adw sdlc 7 --skip-e2e

# 4. Review & merge
gh pr view 8
gh pr merge 8 --squash

# 5. Cleanup
git worktree remove artifacts/your-org/your-repo/trees/<adw_id>
```

---

## Model Selection

ADW supports two model sets controlled via issue/comment text:

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

ADW supports up to 15 concurrent workflows:

```bash
# Process multiple issues in parallel
uv run adw sdlc 101 &
uv run adw sdlc 102 &
uv run adw sdlc 103 &

# Each gets isolated:
# - Unique worktree: artifacts/.../trees/{adw-id}/
# - Unique ports: Deterministically assigned from ID hash
# - Unique branch: {type}-issue-{n}-adw-{id}-{slug}
```

---

**ADW ID Format:** 8-character hex (e.g., `8035e781`)  
**Branch Format:** `{type}-issue-{n}-adw-{id}-{description}`  
**Plan Format:** [specs/issue-{n}-adw-{id}-sdlc_planner-{description}.md]
