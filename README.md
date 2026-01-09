# CxC Framework

> **Cortex Code** - Autonomous agents for GitHub-driven SDLC

---

## 🚀 QUICK START (3 Steps)

### 1️⃣ Clone Adjacent to Your Project

```bash
# Clone CxC framework next to your project
cd ~/code                              # or wherever your projects live
git clone https://github.com/your-org/cxc-framework.git

# Your structure should look like:
# ~/code/
# ├── cxc-framework/    ← this repo
# └── your-project/     ← your consuming project
```

### 2️⃣ Add as Dependency

```bash
cd ~/code/your-project

# Use relative path (recommended)
uv add ../cxc-framework

# Or absolute path
uv add /path/to/cxc-framework
```

### 3️⃣ Run Setup Script with Cursor/Claude

**This is the easiest way** - let the AI configure everything:

```bash
cd ~/code/your-project

# Tell Cursor Agent or Claude Code to run:
python ../cxc-framework/setup_cxc_example.py
```

The script automatically:
- ✅ Creates `.cxc.yaml` (detects `project_id` from git remote)
- ✅ Creates `.env` (pulls `GITHUB_PAT` from `gh auth token`)
- ✅ Copies slash commands to `.claude/commands/`
- ✅ Creates `.mcp.json` for Claude Code MCP integration
- ✅ Runs `uv sync`
- ✅ Verifies `cxc --help` works

### ✅ Done! Try It:

```bash
uv run cxc --help
uv run cxc sdlc 1    # Process GitHub issue #1
```

---

## 📋 Manual Setup (Alternative)

If you prefer manual configuration:

### Create `.cxc.yaml`

```bash
cp ../cxc-framework/templates/cxc.yaml .cxc.yaml
# Edit project_id to match your GitHub repo (e.g., "myorg/myrepo")
```

### Create `.env`

```bash
cp ../cxc-framework/.env.example .env
```

**Required variables:**
```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx           # Your Anthropic API key
GITHUB_PAT=ghp_xxxxx                      # GitHub PAT (or use `gh auth login`)
CLAUDE_CODE_PATH=/usr/local/bin/claude   # Path to claude CLI
```

### Sync and Verify

```bash
uv sync
uv run cxc --help
```

You should see:
```
usage: cxc [-h] {plan,build,test,review,document,ship,patch,sdlc,zte,monitor,webhook} ...

Cortex Code (CxC) CLI
```

---

## ✅ VERIFICATION CHECKLIST

```bash
# 1. CLI works
uv run cxc --help

# 2. Config loads correctly
uv run python -c "from cxc.core.config import CxCConfig; c = CxCConfig.load(); print(f'project_id: {c.project_id}')"

# 3. State saves to correct location
uv run python -c "from cxc.core.state import CxCState; s = CxCState('test123'); print(f'State path: {s.get_state_path()}')"
# Should show: artifacts/your-org/your-repo/test123/cxc_state.json

# 4. GitHub connection
uv run python -c "from cxc.integrations.github import get_repo_url; print(get_repo_url())"
```

---

## 📖 USAGE

### Basic Commands

```bash
# Process a single issue
uv run cxc plan 42       # Create implementation plan for issue #42
uv run cxc build 42      # Build the implementation
uv run cxc test 42       # Run tests
uv run cxc review 42     # Review the changes
uv run cxc sdlc 42       # Full lifecycle (plan→build→test→review→document→ship)
uv run cxc zte 42        # Zero Touch Execution (SDLC + auto-merge) ⚠️

# Triggers (continuous processing)
uv run cxc monitor       # Poll GitHub every 20s for new issues
uv run cxc webhook       # Start webhook server for real-time events
```

### SDLC + ZTE: with and without GitHub comments

**Run manually (no comment triggers):**
```bash
uv run cxc sdlc <issue-number>
uv run cxc zte <issue-number>   # ZTE merges to main on success
```
Requires a valid `origin` remote and `gh auth` (or `GITHUB_PAT`) to read the issue.

**Run via issue comments (webhook/monitor):**
1. Start a trigger: `uv run cxc webhook` or `uv run cxc monitor`
2. Comment on the issue:
   - `cxc_sdlc_iso` or `cxc_sdlc_zte_iso`
   - Optional: `model_set heavy`

**Disable posting comments (still reads issues via gh):**
```bash
export CxC_DISABLE_GITHUB_COMMENTS=1
# or add to .env: CxC_DISABLE_GITHUB_COMMENTS=1
```
This suppresses CxC status updates on the issue while workflows run.

### Full SDLC Example

```bash
# Create a GitHub issue, then:
uv run cxc sdlc 123

# This will:
# 1. Create isolated worktree: artifacts/{project_id}/trees/cxc-{id}
# 2. Plan implementation
# 3. Build feature
# 4. Run tests
# 5. Review changes
# 6. Document
# 7. Create PR
```

---

## 📁 What Gets Created

After running CxC:

```
your-project/
├── .cxc.yaml           # Config (you create)
├── .env                # Secrets (you create)
├── pyproject.toml      # Dependencies
└── artifacts/          # Auto-created by CxC
    └── your-org/
        └── your-repo/
            ├── {cxc-id}/
            │   └── cxc_state.json
            └── trees/
                └── {cxc-id}/   # Isolated worktree
```

---

## 🔧 Troubleshooting

**"No .cxc.yaml found"**: Create the config file in project root

**"ANTHROPIC_API_KEY not set"**: Create `.env` with your API key

**State saving to wrong location**: Check `artifacts_dir` in `.cxc.yaml`

**Import errors**: Run `uv sync --reinstall` to refresh packages

---

## 🎨 IDE Configuration

### Cursor
Team rules are shared via `.cursor/rules/` (committed to repo). All devs who clone inherit:
- `.cursor/rules/cxc-commands.mdc` - Documents available slash commands (Cursor also inherits Claude Code commands)

> **Note:** Cursor doesn't have a `.cursor.team` equivalent like Claude. The `.cursor/rules/` directory serves as the team config.

### Claude Code
- `.claude/commands/` - Slash commands for Claude Code CLI
- `CLAUDE.md` - Project context, architecture and instructions

---

## 🔌 MCP Server (Claude Code / Claude Desktop)

CxC exposes its SDLC tools via MCP (Model Context Protocol), allowing Claude to use them directly.

### Claude Code (CLI) - Automatic

The setup script creates `.mcp.json` in your project. Verify with:
```bash
claude mcp list
# Should show: cxc (project)
```

### Claude Code (CLI) - Manual

Create `.mcp.json` in your project root:
```json
{
  "mcpServers": {
    "cxc": {
      "command": "uv",
      "args": ["--directory", "../cxc-framework", "run", "cxc-mcp"]
    }
  }
}
```

### Claude Desktop

See `docs/MCP_SERVER.md` for Claude Desktop configuration (requires absolute paths).

---

## 📚 Documentation

- `THIS_IS_A_PACKAGE.FYI` - Why this directory is installable
- `docs/MCP_SERVER.md` - MCP server setup and tool reference
- `docs/REFACTOR_REPORT.md` - Last large refactor: redunadant.
- `docs/ORCHESTRATOR_GUIDE.md` - Complete workflow guide for AI orchestrators
