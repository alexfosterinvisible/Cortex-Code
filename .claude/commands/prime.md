
READ this **essential reading list** for an agent to understand the ADW Framework:

---

## 📚 Core Documentation (Priority Order)

### 1. **`docs/ORCHESTRATOR_GUIDE.md`** ⭐ MOST IMPORTANT
This is the single most comprehensive document. It explains:
- Complete workflow lifecycle (plan→build→test→review→document→ship)
- CLI commands and their usage
- State & logs locations
- Decision tree for error handling
- Parallel execution support
- GitHub integration patterns

### 2. **`README.md`**
Setup and configuration essentials:
- Package installation
- `.adw.yaml` configuration schema
- `.env` required variables
- Verification checklist
- Basic CLI usage examples

### 3. **`commands/examples/README.md`**
Understanding the command system:
- What app-specific vs framework commands are
- How to customize templates
- Why commands use `[bracketed]` placeholders

---

## 🔧 Key Source Files (Architecture Understanding)

| File | Purpose |
|------|---------|
| `adw/cli.py` | Entry point - maps CLI commands to workflow modules |
| `adw/core/config.py` | `ADWConfig` dataclass - loads `.adw.yaml`, handles paths |
| `adw/core/state.py` | `ADWState` class - persistent JSON state per workflow |
| `adw/core/agent.py` | Claude Code execution - prompts, retry logic, model selection |
| `adw/workflows/sdlc.py` | Main orchestration - chains all phases together |
| `adw/workflows/plan.py` | Example workflow - shows full pattern (fetch→classify→branch→worktree→plan→commit→PR) |

---

## 📝 Command Templates (Understanding Prompts)

| Command | Role |
|---------|------|
| `commands/implement.md` | Core build prompt - simple but central |
| `commands/feature.md` | Full planning template with detailed `Plan Format` |
| `commands/classify_issue.md` | Issue classification (`/chore`, `/bug`, `/feature`) |
| `commands/review.md` | Review process template |

---

## 🎯 Key Concepts to Understand

1. **ADW ID** - Unique 8-char identifier per workflow instance
2. **Isolated Worktrees** - Git worktrees under `artifacts/{project_id}/trees/{adw-id}/`  
3. **Port Allocation** - Deterministic ports (9100-9114 backend, 9200-9214 frontend) per instance
4. **State Persistence** - `adw_state.json` carries: `adw_id`, `issue_number`, `branch_name`, `plan_file`, `worktree_path`, `model_set`
5. **Model Selection** - `base` (Sonnet) vs `heavy` (Opus) per command type
6. **Agent Logs** - JSONL format in `artifacts/{org}/{repo}/{adw-id}/{agent}/raw_output.jsonl`

---

## 🚀 Minimal Quick-Start Reading

If time-constrained, read just these three:

1. `docs/ORCHESTRATOR_GUIDE.md` - The "how it all works" guide
2. `adw/workflows/sdlc.py` - See the orchestration flow
3. `adw/workflows/plan.py` - Understand a complete single-phase workflow