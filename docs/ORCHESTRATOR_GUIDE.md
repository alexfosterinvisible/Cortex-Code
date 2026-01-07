# CxC Framework Orchestrator Guide

> **For**: AI Orchestrators (Claude, Cursor, etc.) managing GitHub-driven SDLC
> **Version**: 0.1.0
> **Last Updated**: 2025-12-26

---

## Overview

Cortex Code (CxC) automates software development using Claude Code agents in isolated git worktrees. As an orchestrator, you manage the workflow lifecycle using GitHub issues and CLI commands.

---

## Quick Reference

### Core Workflow Commands

```bash
# Full SDLC (plan→build→test→review→document)
uv run cxc sdlc <issue-number> [cxc-id] [--skip-e2e] [--skip-resolution]

# Zero Touch Execution (SDLC + auto-merge) ⚠️ MERGES TO MAIN
uv run cxc zte <issue-number> [cxc-id] [--skip-e2e] [--skip-resolution]

# Individual phases
uv run cxc plan <issue-number> [cxc-id]           # Creates worktree + plan
uv run cxc build <issue-number> <cxc-id>          # Implements plan
uv run cxc test <issue-number> <cxc-id>           # Runs tests
uv run cxc review <issue-number> <cxc-id>         # Reviews changes
uv run cxc document <issue-number> <cxc-id>       # Generates docs
uv run cxc ship <issue-number> <cxc-id>           # Approves + merges PR
```

### State & Logs Location

```
artifacts/{org}/{repo}/
├── {cxc-id}/
│   ├── cxc_state.json          # Workflow state
│   ├── ops/                    # Orchestrator logs
│   ├── sdlc_planner/           # Planning agent output
│   ├── sdlc_implementor/       # Build agent output
│   ├── tester/                 # Test agent output
│   ├── reviewer/               # Review agent output
│   │   └── review_img/         # Screenshots
│   └── documenter/             # Documentation agent output
└── trees/
    └── {cxc-id}/               # Isolated git worktree
```

---

## Workflow Lifecycle

### Phase 1: Issue Creation
1. User creates GitHub issue with title + body
2. Issue should describe the desired change clearly

### Phase 2: Triggering CxC
Three options:
1. **Manual CLI**: `uv run cxc sdlc <issue-number>`
2. **Webhook**: Comment `cxc_sdlc_iso` on issue
3. **Cron**: `uv run cxc monitor` polls for new issues

### Phase 3: Plan Phase
CxC creates:
- Isolated worktree at `artifacts/{project_id}/trees/{cxc-id}/`
- Unique ports (backend: 9100-9114, frontend: 9200-9214)
- Feature branch: `{type}-issue-{num}-cxc-{id}-{slug}`
- Implementation plan in `specs/`

### Phase 4: Build Phase
Claude Code implements the plan:
- Executes `/implement` with plan file
- Creates all required files/changes
- Commits to feature branch

### Phase 5: Test Phase
- Runs `uv run pytest` or configured test command
- Auto-fixes failing tests (up to 3 attempts)
- Optionally runs E2E tests

### Phase 6: Review Phase
- Validates implementation against spec
- Takes screenshots (if applicable)
- Auto-resolves blocking issues (up to 3 fix loops for blockers)

### Phase 7: Document Phase
- Generates feature documentation
- Saves to `app_docs/`

### Phase 8: Ship Phase (ZTE only)
- Approves PR
- Squash merges to main

---

## Orchestrator Decision Tree

```
Issue received
    │
    ├─► Is it well-specified?
    │       ├─► YES → uv run cxc sdlc {issue}
    │       └─► NO  → Comment asking for clarification
    │
    ├─► Did plan phase fail?
    │       ├─► Classification error → Check issue format
    │       ├─► Worktree error → Check git state, clean stale worktrees
    │       └─► Plan generation error → Read agent output, retry
    │
    ├─► Did build phase fail?
    │       ├─► Implementation error → Read planner output, refine plan
    │       └─► Git error → Check branch state
    │
    ├─► Did test phase fail?
    │       ├─► Test failures → CxC auto-retries 3x
    │       └─► Persistent failure → Manual intervention needed
    │
    └─► Did review/ship fail?
            ├─► PR conflict → Rebase and retry
            └─► Merge blocked → Check branch protection rules
```

---

## Reading State

```bash
# View current state for an CxC ID
cat artifacts/{org}/{repo}/{cxc-id}/cxc_state.json | jq .

# Key fields:
# - cxc_id: Unique workflow identifier
# - issue_number: GitHub issue being processed
# - branch_name: Feature branch
# - plan_file: Path to implementation plan
# - issue_class: "/chore" | "/bug" | "/feature"
# - worktree_path: Absolute path to isolated worktree
# - backend_port: Allocated backend port
# - frontend_port: Allocated frontend port
```

---

## Reading Agent Logs

```bash
# Latest agent output (JSONL format)
cat artifacts/{org}/{repo}/{cxc-id}/{agent}/raw_output.jsonl | tail -20

# Convert to readable JSON
jq -s '.' artifacts/{org}/{repo}/{cxc-id}/{agent}/raw_output.jsonl

# Find errors
grep -i "error" artifacts/{org}/{repo}/{cxc-id}/{agent}/raw_output.jsonl
```

---

## Chaining Workflows

```bash
# Start with planning
uv run cxc plan 42
# Output: "Using CxC ID: abc12345"

# Chain additional phases using the CxC ID
uv run cxc build 42 abc12345
uv run cxc test 42 abc12345 --skip-e2e
uv run cxc review 42 abc12345
uv run cxc document 42 abc12345
uv run cxc ship 42 abc12345
```

---

## Parallel Execution

CxC supports up to 15 concurrent workflows:

```bash
# Process multiple issues in parallel
uv run cxc sdlc 101 &
uv run cxc sdlc 102 &
uv run cxc sdlc 103 &

# Each gets isolated:
# - Worktree: artifacts/.../trees/{cxc-id}/
# - Ports: Deterministically assigned from ID hash
# - Git branch: Unique per issue
```

---

## Cleanup

```bash
# List all worktrees
git worktree list

# Remove specific worktree
git worktree remove artifacts/{org}/{repo}/trees/{cxc-id}

# Prune invalid worktree references
git worktree prune

# Clean old state (manual)
rm -rf artifacts/{org}/{repo}/{cxc-id}
```

---

## Troubleshooting

### "No .cxc.yaml found"
Create `.cxc.yaml` in project root:
```bash
cp /Users/dev3/code4b/cxc-framework/templates/cxc.yaml .cxc.yaml
# Edit project_id in .cxc.yaml (org/repo)
```

### "ANTHROPIC_API_KEY not set"
Create `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx
GITHUB_PAT=ghp_xxxxx
```

### "No worktree found" (build/test/review)
Run plan phase first:
```bash
uv run cxc plan <issue-number>
# Note the CxC ID, then:
uv run cxc build <issue-number> <cxc-id>
```

### Port conflicts
CxC auto-finds next available ports. If persistent:
```bash
lsof -i :9100-9114  # Check what's using ports
```

### Git conflicts
```bash
cd artifacts/{org}/{repo}/trees/{cxc-id}
git status
git stash  # or resolve manually
```

---

## GitHub Integration

### Webhook Setup
1. Start webhook: `uv run cxc webhook`
2. Expose: `ngrok http 8001`
3. Configure GitHub webhook → `your-url/gh-webhook`

### Trigger Patterns
| Comment | Action |
|---------|--------|
| `cxc_plan_iso` | Plan only |
| `cxc_plan_build_iso` | Plan + Build |
| `cxc_sdlc_iso` | Full SDLC |
| `cxc_sdlc_zte_iso` | SDLC + Auto-merge |

### Disable Comment Posting
If you want to run workflows without posting status updates to GitHub issues:
```bash
export CxC_DISABLE_GITHUB_COMMENTS=1
# or add to .env: CxC_DISABLE_GITHUB_COMMENTS=1
```
Workflows will still read issues via `gh`, but will not post progress comments.

### Bot Comments
CxC posts status updates with format:
```
[CxC_BOT] {cxc-id}_{agent}: {message}
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | ✅ | Claude API key |
| `GITHUB_PAT` | ✅ | GitHub token with repo scope |
| `GITHUB_REPO_URL` | ✅ | Repository URL |
| `CLAUDE_CODE_PATH` | ❌ | Path to claude CLI (default: "claude") |
| `CxC_DISABLE_GITHUB_COMMENTS` | ❌ | Skip posting status comments on issues |

---

## Model Selection

CxC supports dynamic model selection:

```
model_set base  → Uses Sonnet for all commands
model_set heavy → Uses Opus for complex tasks
```

Add to issue/comment: `cxc_sdlc_iso model_set heavy`

Commands using Opus in heavy mode:
- `/implement`, `/document`
- `/resolve_failed_test`, `/resolve_failed_e2e_test`
- `/chore`, `/bug`, `/feature`, `/patch`

---

## Best Practices for Orchestrators

1. **Always check state before acting**
   ```bash
   cat artifacts/{org}/{repo}/{cxc-id}/cxc_state.json | jq .
   ```

2. **Read logs on failure**
   ```bash
   cat artifacts/{org}/{repo}/{cxc-id}/{agent}/raw_output.jsonl | tail -50
   ```

3. **Use `--skip-e2e` for faster iteration**
   ```bash
   uv run cxc sdlc 42 --skip-e2e
   ```

4. **Clean up after successful merges**
   ```bash
   git worktree remove artifacts/{org}/{repo}/trees/{cxc-id}
   ```

5. **For complex features, use `model_set heavy`**

6. **Monitor GitHub issue for status updates**

---

## Integration with Southwest Ops Universe Brief

For implementing the Southwest Ops Universe (`sw-ops-universe-brief.md`):

1. **Create milestone issues** - One per M1-M5
2. **Use structured issue format**:
   ```
   Title: [M1] Core Mechanics - Crew Assignment
   Body:
   - Implement CrewSchedulerApp
   - Create CrewMember, Flight dataclasses
   - Add legality constraints (8hr daily, 30hr weekly)
   
   cxc_sdlc_iso model_set heavy
   ```

3. **Track progress via CxC state**
4. **Review PRs before shipping** (don't use ZTE for initial implementation)

---

## File Structure After CxC Run

```
your-project/
├── .cxc.yaml                   # CxC config
├── .env                        # Secrets
├── artifacts/                  # CxC artifacts
│   └── your-org/
│       └── your-repo/
│           ├── {cxc-id}/       # State + agent logs
│           └── trees/          
│               └── {cxc-id}/   # Isolated worktree
├── specs/                      # Implementation plans
│   └── issue-{num}-cxc-{id}-*.md
└── app_docs/                   # Generated documentation
```
