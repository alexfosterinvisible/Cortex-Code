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

Create this file in your **project root**:

```yaml
# .adw.yaml - ADW Framework Configuration

# REQUIRED: Used for artifact namespacing (usually matches your GitHub repo)
project_id: "your-github-username/your-repo-name"

# REQUIRED: Where ADW stores state, logs, worktrees
artifacts_dir: "./artifacts"

# Source root: base path for writing apps/features (e.g., ./src/<appname> or ./apps/<appname>)
source_root: "./src"  # or "./apps", "./packages", etc.

# Port ranges for isolated worktrees (15 concurrent agents max)
ports:
  backend_start: 9100
  backend_count: 15
  frontend_start: 9200
  frontend_count: 15

# Claude command paths (framework commands + your overrides)
commands:
  - "${ADW_FRAMEWORK}/commands"
  - ".claude/commands"

# App-specific settings (customize for your project)
app:
  backend_dir: "app/server"
  frontend_dir: "app/client"
  start_script: "scripts/start.sh"
  test_command: "uv run pytest"
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
uv run python -c "from adw.config import ADWConfig; c = ADWConfig.load(); print(f'project_id: {c.project_id}')"

# 3. State saves to correct location
uv run python -c "from adw.state import ADWState; s = ADWState('test123'); print(f'State path: {s.get_state_path()}')"
# Should show: artifacts/your-org/your-repo/test123/adw_state.json

# 4. GitHub connection
uv run python -c "from adw.github import get_repo_url; print(get_repo_url())"
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

# Triggers (continuous processing)
uv run adw monitor       # Poll GitHub every 20s for new issues
uv run adw webhook       # Start webhook server for real-time events
```

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
