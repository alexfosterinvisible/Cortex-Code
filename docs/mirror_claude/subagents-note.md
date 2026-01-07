# cc-mirror Team Mode: Sub-Agent Architecture (Claude)

> Investigation: How does cc-mirror's "team mode" orchestrate sub-agents?

## TL;DR

**cc-mirror uses separate CLI instances (bash background jobs), NOT subprocess.run or Claude Code's internal sub-agents.**

Agents coordinate via a shared JSON task store on the local filesystem. This is simpler but less isolated than CxC's worktree-based approach.

---

## Key Findings

### 1. Agent Spawning Mechanism

Team mode launches agents as **independent bash background jobs**:

```bash
# From team-mode.md - NOT subprocess.run from within Claude Code
CLAUDE_CODE_TEAM_NAME="$TEAM_NAME" \
CLAUDE_CODE_AGENT_ID="lead" \
CLAUDE_CODE_AGENT_TYPE="team-lead" \
$VARIANT --print "Plan tasks for: $1" &

for i in 1 2 3; do
  CLAUDE_CODE_TEAM_NAME="$TEAM_NAME" \
  CLAUDE_CODE_AGENT_ID="worker-$i" \
  CLAUDE_CODE_AGENT_TYPE="worker" \
  $VARIANT --print "Check TaskList and claim available tasks." &
done
wait
```

**Each agent is a fully independent Claude Code CLI session** with its own context window.

### 2. Coordination via Shared Task Store

Agents communicate via JSON files:
```
~/.cc-mirror/<variant>/config/tasks/<team_name>/
├── 1.json
├── 2.json
└── 3.json
```

Task structure:
```typescript
interface Task {
  id: string;
  subject: string;
  description: string;
  status: 'open' | 'resolved';
  owner?: string;          // Agent ID that claimed the task
  blocks: string[];        // Tasks this blocks
  blockedBy: string[];     // Tasks blocking this
  comments: TaskComment[];
}
```

### 3. Tool Enablement

cc-mirror patches Claude Code's `cli.js` to enable task tools:

```javascript
// Patches function sU() to return true instead of false
function sU() {
  return !0;  // team mode enabled
}
```

This unlocks: `TaskCreate`, `TaskGet`, `TaskUpdate`, `TaskList`

---

## Architecture Comparison

| Aspect                  | cc-mirror Team Mode                         | CxC Framework                              |
|-------------------------|---------------------------------------------|--------------------------------------------|
| Agent isolation         | Same machine, shared filesystem             | Git worktrees (full repo isolation)        |
| Spawning mechanism      | Bash background jobs (`&`)                  | `subprocess.run(['claude', '-p', ...])` or manual CLI |
| Coordination            | JSON task store                             | State files + GitHub issues/PRs            |
| Port isolation          | Not managed                                 | Deterministic port allocation per worktree |
| Context sharing         | None - each CLI is independent              | None - each CLI is independent             |
| Orchestration pattern   | Fan-out, pipeline, map-reduce               | SDLC pipeline (plan/build/test/review)     |

---

## Implications for CxC

### What cc-mirror Does Well

1. **Simple coordination** - JSON files are easy to debug
2. **Background agents** - Non-blocking orchestrator pattern
3. **Team identity** - Environment variables for agent ID/type

### What CxC Does Better

1. **Git isolation** - Worktrees prevent merge conflicts between parallel agents
2. **State persistence** - `CxCState` tracks full workflow context
3. **GitHub integration** - PRs and issues as coordination points
4. **Port management** - Prevents server conflicts during testing

### Potential CxC Enhancement

cc-mirror's `TaskCreate/TaskUpdate/TaskList` pattern could complement CxC's worktree model:
- Use cc-mirror-style tasks for intra-workflow coordination
- Use CxC's worktrees for inter-workflow isolation

---

## References

| Resource                          | URL                                                                |
|-----------------------------------|--------------------------------------------------------------------|
| cc-mirror GitHub                  | https://github.com/numman-ali/cc-mirror                            |
| Team Mode Docs                    | https://github.com/numman-ali/cc-mirror/blob/main/docs/features/team-mode.md |
| AGENTS.md (architecture)          | https://github.com/numman-ali/cc-mirror/blob/main/AGENTS.md        |
| Task store implementation         | `src/core/tasks/store.ts`                                          |
| Wrapper script                    | `src/core/wrapper.ts`                                              |

---

*Documented: 2026-01-06*
