# ADW Framework

> **AI Developer Workflow** - Autonomous agents for GitHub-driven SDLC

---

## 🚀 COMPLETE SETUP GUIDE

### Step 1: Add the Package

```bash
cd /path/to/your-project

# Add as dependency (use absolute or relative path)
uv add /Users/dev3/code4b/adw-framework
# OR
uv add ../adw-framework
```

This adds to your `pyproject.toml`:
```toml
[project]
dependencies = ["adw-framework"]

[tool.uv.sources]
adw-framework = { path = "/Users/dev3/code4b/adw-framework" }
```

### Step 2: Create `.adw.yaml` (REQUIRED)

Create this file in your **project root** by copying the template:

```bash
cp /Users/dev3/code4b/adw-framework/templates/adw.yaml .adw.yaml
# Edit project_id in .adw.yaml (org/repo)
```

### Step 3: Create `.env` (REQUIRED)

Copy from `.env.example` and fill in your values:

```bash
cp /Users/dev3/code4b/adw-framework/.env.example .env
```

**Required variables:**
```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx      # Your Anthropic API key
GITHUB_PAT=ghp_xxxxx                 # GitHub PAT with repo scope
CLAUDE_CODE_PATH=/usr/local/bin/claude  # Path to claude CLI
GITHUB_REPO_URL=https://github.com/you/repo.git
```

### Step 4: Sync and Verify

```bash
uv sync
uv run adw --help
```

You should see:
```
usage: adw [-h] {plan,build,test,review,document,ship,patch,sdlc,zte,monitor,webhook} ...

AI Developer Workflow (ADW) CLI
```

---

## ✅ VERIFICATION CHECKLIST

```bash
# 1. CLI works
uv run adw --help

# 2. Config loads correctly
uv run python -c "from adw.core.config import ADWConfig; c = ADWConfig.load(); print(f'project_id: {c.project_id}')"

# 3. State saves to correct location
uv run python -c "from adw.core.state import ADWState; s = ADWState('test123'); print(f'State path: {s.get_state_path()}')"
# Should show: artifacts/your-org/your-repo/test123/adw_state.json

# 4. GitHub connection
uv run python -c "from adw.integrations.github import get_repo_url; print(get_repo_url())"
```

---

## 📖 USAGE

### Basic Commands

```bash
# Process a single issue
uv run adw plan 42       # Create implementation plan for issue #42
uv run adw build 42      # Build the implementation
uv run adw test 42       # Run tests
uv run adw review 42     # Review the changes
uv run adw sdlc 42       # Full lifecycle (plan→build→test→review→document→ship)
uv run adw zte 42        # Zero Touch Execution (SDLC + auto-merge) ⚠️

# Triggers (continuous processing)
uv run adw monitor       # Poll GitHub every 20s for new issues
uv run adw webhook       # Start webhook server for real-time events
```

### SDLC + ZTE: with and without GitHub comments

**Run manually (no comment triggers):**
```bash
uv run adw sdlc <issue-number>
uv run adw zte <issue-number>   # ZTE merges to main on success
```
Requires a valid `origin` remote and `gh auth` (or `GITHUB_PAT`) to read the issue.

**Run via issue comments (webhook/monitor):**
1. Start a trigger: `uv run adw webhook` or `uv run adw monitor`
2. Comment on the issue:
   - `adw_sdlc_iso` or `adw_sdlc_zte_iso`
   - Optional: `model_set heavy`

**Disable posting comments (still reads issues via gh):**
```bash
export ADW_DISABLE_GITHUB_COMMENTS=1
# or add to .env: ADW_DISABLE_GITHUB_COMMENTS=1
```
This suppresses ADW status updates on the issue while workflows run.

### Full SDLC Example

```bash
# Create a GitHub issue, then:
uv run adw sdlc 123

# This will:
# 1. Create isolated worktree: artifacts/{project_id}/trees/adw-{id}
# 2. Plan implementation
# 3. Build feature
# 4. Run tests
# 5. Review changes
# 6. Document
# 7. Create PR
```

---

## 📁 What Gets Created

After running ADW:

```
your-project/
├── .adw.yaml           # Config (you create)
├── .env                # Secrets (you create)
├── pyproject.toml      # Dependencies
└── artifacts/          # Auto-created by ADW
    └── your-org/
        └── your-repo/
            ├── {adw-id}/
            │   └── adw_state.json
            └── trees/
                └── {adw-id}/   # Isolated worktree
```

---

## 🔧 Troubleshooting

**"No .adw.yaml found"**: Create the config file in project root

**"ANTHROPIC_API_KEY not set"**: Create `.env` with your API key

**State saving to wrong location**: Check `artifacts_dir` in `.adw.yaml`

**Import errors**: Run `uv sync --reinstall` to refresh packages

---

## 📚 Documentation

- `THIS_IS_A_PACKAGE.FYI` - Why this directory is installable
- `docs/REFACTOR_REPORT.md` - Full extraction/refactor history
