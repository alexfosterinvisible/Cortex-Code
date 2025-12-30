# ADW Framework Orchestrator Guide

> **For**: AI Orchestrators (Claude, Cursor, etc.) managing GitHub-driven SDLC
> **Version**: 0.1.0
> **Last Updated**: 2025-12-26

---

## Overview

ADW (AI Developer Workflow) automates software development using Claude Code agents in isolated git worktrees. As an orchestrator, you manage the workflow lifecycle using GitHub issues and CLI commands.

---

## Quick Reference

### Core Workflow Commands

```bash
# Full SDLC (plan→build→test→review→document)
uv run adw sdlc <issue-number> [adw-id] [--skip-e2e] [--skip-resolution]

# Zero Touch Execution (SDLC + auto-merge) ⚠️ MERGES TO MAIN
uv run adw zte <issue-number> [adw-id] [--skip-e2e] [--skip-resolution]

# Individual phases
uv run adw plan <issue-number> [adw-id]           # Creates worktree + plan
uv run adw build <issue-number> <adw-id>          # Implements plan
uv run adw test <issue-number> <adw-id>           # Runs tests
uv run adw review <issue-number> <adw-id>         # Reviews changes
uv run adw document <issue-number> <adw-id>       # Generates docs
uv run adw ship <issue-number> <adw-id>           # Approves + merges PR
```

### State & Logs Location

```
artifacts/{org}/{repo}/
├── {adw-id}/
│   ├── adw_state.json          # Workflow state
│   ├── ops/                    # Orchestrator logs
│   ├── sdlc_planner/           # Planning agent output
│   ├── sdlc_implementor/       # Build agent output
│   ├── tester/                 # Test agent output
│   ├── reviewer/               # Review agent output
│   │   └── review_img/         # Screenshots
│   └── documenter/             # Documentation agent output
└── trees/
    └── {adw-id}/               # Isolated git worktree
```

---

## Workflow Lifecycle

### Phase 1: Issue Creation
1. User creates GitHub issue with title + body
2. Issue should describe the desired change clearly

### Phase 2: Triggering ADW
Three options:
1. **Manual CLI**: `uv run adw sdlc <issue-number>`
2. **Webhook**: Comment `adw_sdlc_iso` on issue
3. **Cron**: `uv run adw monitor` polls for new issues

### Phase 3: Plan Phase
ADW creates:
- Isolated worktree at `artifacts/{project_id}/trees/{adw-id}/`
- Unique ports (backend: 9100-9114, frontend: 9200-9214)
- Feature branch: `{type}-issue-{num}-adw-{id}-{slug}`
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
    │       ├─► YES → uv run adw sdlc {issue}
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
    │       ├─► Test failures → ADW auto-retries 3x
    │       └─► Persistent failure → Manual intervention needed
    │
    └─► Did review/ship fail?
            ├─► PR conflict → Rebase and retry
            └─► Merge blocked → Check branch protection rules
```

---

## Reading State

```bash
# View current state for an ADW ID
cat artifacts/{org}/{repo}/{adw-id}/adw_state.json | jq .

# Key fields:
# - adw_id: Unique workflow identifier
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
cat artifacts/{org}/{repo}/{adw-id}/{agent}/raw_output.jsonl | tail -20

# Convert to readable JSON
jq -s '.' artifacts/{org}/{repo}/{adw-id}/{agent}/raw_output.jsonl

# Find errors
grep -i "error" artifacts/{org}/{repo}/{adw-id}/{agent}/raw_output.jsonl
```

---

## Chaining Workflows

```bash
# Start with planning
uv run adw plan 42
# Output: "Using ADW ID: abc12345"

# Chain additional phases using the ADW ID
uv run adw build 42 abc12345
uv run adw test 42 abc12345 --skip-e2e
uv run adw review 42 abc12345
uv run adw document 42 abc12345
uv run adw ship 42 abc12345
```

---

## Parallel Execution

ADW supports up to 15 concurrent workflows:

```bash
# Process multiple issues in parallel
uv run adw sdlc 101 &
uv run adw sdlc 102 &
uv run adw sdlc 103 &

# Each gets isolated:
# - Worktree: artifacts/.../trees/{adw-id}/
# - Ports: Deterministically assigned from ID hash
# - Git branch: Unique per issue
```

---

## Cleanup

```bash
# List all worktrees
git worktree list

# Remove specific worktree
git worktree remove artifacts/{org}/{repo}/trees/{adw-id}

# Prune invalid worktree references
git worktree prune

# Clean old state (manual)
rm -rf artifacts/{org}/{repo}/{adw-id}
```

---

## Troubleshooting

### "No .adw.yaml found"
Create `.adw.yaml` in project root:
```bash
cp /Users/dev3/code4b/adw-framework/templates/adw.yaml .adw.yaml
# Edit project_id in .adw.yaml (org/repo)
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
uv run adw plan <issue-number>
# Note the ADW ID, then:
uv run adw build <issue-number> <adw-id>
```

### Port conflicts
ADW auto-finds next available ports. If persistent:
```bash
lsof -i :9100-9114  # Check what's using ports
```

### Git conflicts
```bash
cd artifacts/{org}/{repo}/trees/{adw-id}
git status
git stash  # or resolve manually
```

---

## GitHub Integration

### Webhook Setup
1. Start webhook: `uv run adw webhook`
2. Expose: `ngrok http 8001`
3. Configure GitHub webhook → `your-url/gh-webhook`

### Trigger Patterns
| Comment | Action |
|---------|--------|
| `adw_plan_iso` | Plan only |
| `adw_plan_build_iso` | Plan + Build |
| `adw_sdlc_iso` | Full SDLC |
| `adw_sdlc_zte_iso` | SDLC + Auto-merge |

### Disable Comment Posting
If you want to run workflows without posting status updates to GitHub issues:
```bash
export ADW_DISABLE_GITHUB_COMMENTS=1
# or add to .env: ADW_DISABLE_GITHUB_COMMENTS=1
```
Workflows will still read issues via `gh`, but will not post progress comments.

### Bot Comments
ADW posts status updates with format:
```
[ADW_BOT] {adw-id}_{agent}: {message}
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | ✅ | Claude API key |
| `GITHUB_PAT` | ✅ | GitHub token with repo scope |
| `GITHUB_REPO_URL` | ✅ | Repository URL |
| `CLAUDE_CODE_PATH` | ❌ | Path to claude CLI (default: "claude") |
| `ADW_DISABLE_GITHUB_COMMENTS` | ❌ | Skip posting status comments on issues |

---

## Model Selection

ADW supports dynamic model selection:

```
model_set base  → Uses Sonnet for all commands
model_set heavy → Uses Opus for complex tasks
```

Add to issue/comment: `adw_sdlc_iso model_set heavy`

Commands using Opus in heavy mode:
- `/implement`, `/document`
- `/resolve_failed_test`, `/resolve_failed_e2e_test`
- `/chore`, `/bug`, `/feature`, `/patch`

---

## Best Practices for Orchestrators

1. **Always check state before acting**
   ```bash
   cat artifacts/{org}/{repo}/{adw-id}/adw_state.json | jq .
   ```

2. **Read logs on failure**
   ```bash
   cat artifacts/{org}/{repo}/{adw-id}/{agent}/raw_output.jsonl | tail -50
   ```

3. **Use `--skip-e2e` for faster iteration**
   ```bash
   uv run adw sdlc 42 --skip-e2e
   ```

4. **Clean up after successful merges**
   ```bash
   git worktree remove artifacts/{org}/{repo}/trees/{adw-id}
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
   
   adw_sdlc_iso model_set heavy
   ```

3. **Track progress via ADW state**
4. **Review PRs before shipping** (don't use ZTE for initial implementation)

---

## File Structure After ADW Run

```
your-project/
├── .adw.yaml                   # ADW config
├── .env                        # Secrets
├── artifacts/                  # ADW artifacts
│   └── your-org/
│       └── your-repo/
│           ├── {adw-id}/       # State + agent logs
│           └── trees/          
│               └── {adw-id}/   # Isolated worktree
├── specs/                      # Implementation plans
│   └── issue-{num}-adw-{id}-*.md
└── app_docs/                   # Generated documentation
```
