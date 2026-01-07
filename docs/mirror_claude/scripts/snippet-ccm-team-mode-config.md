# CC-Mirror Team Mode Configuration

**Source:** [cc-mirror GitHub Repository](https://github.com/numman-ali/cc-mirror)

## Overview

Team mode in cc-mirror enables collaborative task management features including:
- **TaskCreate** - Create new tasks
- **TaskGet** - Retrieve task details
- **TaskUpdate** - Update task status, add comments, set dependencies
- **TaskList** - List all tasks
- **Orchestrator skill** - Teaches Claude effective multi-agent coordination patterns

Mirror Claude variants have team mode **enabled by default**. Other providers can enable it with the `--enable-team-mode` flag.

---

## Enabling Team Mode

### Quick Setup with Team Mode

```bash
# Z.ai with team mode
npx cc-mirror quick --provider zai --name zai-team --enable-team-mode

# MiniMax with team mode
npx cc-mirror quick --provider minimax --name minimax-team --enable-team-mode

# OpenRouter with team mode
npx cc-mirror quick --provider openrouter --name or-team \
  --api-key "$OPENROUTER_API_KEY" \
  --model-sonnet "anthropic/claude-3.5-sonnet" \
  --enable-team-mode
```

### Full Wizard with Team Mode

```bash
# Interactive creation with team mode selection
npx cc-mirror create
# Follow prompts and select "Yes" when asked about team mode
```

### Mirror Claude (Team Mode by Default)

```bash
# Mirror Claude has team mode enabled automatically
npx cc-mirror quick --provider mirror --name mclaude
```

---

## Team Mode Task Management

### CLI Task Commands

```bash
# List all open tasks
npx cc-mirror tasks

# Create a new task
npx cc-mirror tasks create --subject "Add authentication system"

# Update task status
npx cc-mirror tasks update 5 --status resolved

# Archive completed task (preserves history)
npx cc-mirror tasks archive 5

# Visualize task dependencies
npx cc-mirror tasks graph

# Clean up resolved tasks
npx cc-mirror tasks clean --resolved --force
```

### Task Status Values

- `pending` - Task not yet started
- `in_progress` - Currently being worked on
- `resolved` - Task completed successfully
- `blocked` - Task cannot proceed (awaiting dependency)
- `cancelled` - Task abandoned

---

## Project-Scoped Teams

CC-Mirror automatically scopes tasks by project directory to avoid collision between different projects.

### Automatic Scoping

```bash
# Working in API project
cd ~/projects/api
mc                  # Team: mc-api

# Switch to frontend project
cd ~/projects/frontend
mc                  # Team: mc-frontend
```

### Manual Team Assignment

```bash
# Override automatic scoping with TEAM variable
TEAM=backend mc     # Team: mc-myproject-backend
TEAM=frontend mc    # Team: mc-myproject-frontend
```

### Team Naming Pattern

Format: `<variant>-<project>`

Examples:
- `mclaude-api`
- `zai-team-frontend`
- `minimax-backend`

---

## Technical Implementation

### Architecture

Team mode operates through a **single-function patch** in `cli.js`:

```javascript
// Before patch (team mode disabled)
return !1

// After patch (team mode enabled)
return !0
```

This patch is applied during the variant creation/update process in the setup pipeline.

### Configuration Files

Team mode affects these files in `~/.cc-mirror/<variant>/`:

**`config/settings.json`** - Environment variables:
```json
{
  "env": {
    "ANTHROPIC_API_KEY": "your-api-key",
    "TEAM": "auto-detected-or-manual"
  }
}
```

**`variant.json`** - Metadata tracking:
```json
{
  "name": "mclaude",
  "provider": "mirror",
  "teamMode": true,
  "created": "2026-01-06T12:00:00Z"
}
```

---

## Setup Pipeline for Team Mode

When creating a variant with `--enable-team-mode`, cc-mirror executes:

1. **Directory creation** - `~/.cc-mirror/<variant>/`
2. **npm installation** - Install `@anthropic-ai/claude-code@2.0.76`
3. **Team mode patching** - Apply `cli.js` patch to enable team features
4. **Brand theme application** - Via tweakcc (optional)
5. **Configuration writing** - Write `settings.json` and `.claude.json`
6. **Prompt pack deployment** - Add orchestrator skill prompts
7. **Shell wrapper generation** - Create `~/.local/bin/<variant>`
8. **Metadata finalization** - Write `variant.json`

---

## Use Cases

### Multi-Agent Workflows

```bash
# Agent 1: Planning agent
mclaude tasks create --subject "Design auth system architecture"

# Agent 2: Implementation agent
mclaude tasks create --subject "Implement JWT authentication" --depends-on 1

# Agent 3: Testing agent
mclaude tasks create --subject "Write auth integration tests" --depends-on 2

# Visualize workflow
mclaude tasks graph
```

### Parallel Development

```bash
# Frontend team
cd ~/project/frontend
TEAM=frontend mclaude tasks create --subject "Build login UI"

# Backend team
cd ~/project/backend
TEAM=backend mclaude tasks create --subject "Implement auth API"

# Tasks are isolated by team
```

### Task Dependencies

```bash
# Create dependent tasks
mclaude tasks create --subject "Set up database schema"
mclaude tasks create --subject "Create migration scripts" --depends-on 1
mclaude tasks create --subject "Seed test data" --depends-on 2

# Graph shows execution order
mclaude tasks graph
```

---

## Comparison: Team Mode vs Standard Mode

| Feature | Standard Mode | Team Mode |
|---------|--------------|-----------|
| TaskCreate | ❌ | ✅ |
| TaskGet | ❌ | ✅ |
| TaskUpdate | ❌ | ✅ |
| TaskList | ❌ | ✅ |
| Task Dependencies | ❌ | ✅ |
| Project Scoping | ❌ | ✅ |
| Orchestrator Skill | ❌ | ✅ |
| Multi-Agent Coordination | Limited | Full Support |

---

## Provider-Specific Notes

### Mirror Claude (Pure Claude)
- Team mode **enabled by default**
- No additional configuration needed
- Direct connection to Anthropic API

### Z.ai / MiniMax
- Requires `--enable-team-mode` flag
- Adds deny list for server-side MCP tools in `settings.json`
- Dev-browser skill installed by default (disable with `--no-skill-install`)

### OpenRouter
- Requires `--enable-team-mode` flag
- Supports 100+ models
- Model mapping via `--model-sonnet`, `--model-opus`, `--model-haiku`

### CCRouter (Local LLMs)
- Requires `--enable-team-mode` flag
- Handles model mapping internally
- Optional authentication

---

## Troubleshooting

### Team Mode Not Working

```bash
# Verify team mode is enabled
npx cc-mirror list
# Check "Team Mode" column

# Re-enable team mode
npx cc-mirror update <variant> --enable-team-mode

# Verify cli.js patch
# Should see "return !0" in team mode function
```

### Tasks Not Scoping Correctly

```bash
# Check current team
echo $TEAM

# Manually set team
TEAM=myteam mclaude

# Verify task list
mclaude tasks
# Should show team name in output
```

### Variant Not Found

```bash
# Ensure ~/.local/bin is in PATH
echo $PATH | grep -q "$HOME/.local/bin" || echo "Add ~/.local/bin to PATH"

# Verify wrapper exists
ls -la ~/.local/bin/mclaude

# Regenerate wrapper
npx cc-mirror update mclaude
```

---

## Best Practices

1. **Use descriptive task subjects** - Makes task lists readable
2. **Set up dependencies** - Ensures correct execution order
3. **Archive completed tasks** - Keeps task list clean while preserving history
4. **Use project scoping** - Prevents task collision between projects
5. **Visualize with graphs** - Use `tasks graph` to understand workflow
6. **Manual TEAM override** - Use when automatic scoping isn't sufficient

---

## Related Commands

```bash
# Create variant with team mode
npx cc-mirror create --enable-team-mode

# List all variants (shows team mode status)
npx cc-mirror list

# Update variant to enable team mode
npx cc-mirror update <variant> --enable-team-mode

# Health check (verifies team mode patch)
npx cc-mirror doctor

# Task management
npx cc-mirror tasks [create|update|archive|graph|clean]
```

---

## References

- [CC-Mirror GitHub Repository](https://github.com/numman-ali/cc-mirror)
- [CC-Mirror DESIGN.md](https://github.com/numman-ali/cc-mirror/blob/main/DESIGN.md)
- [CC-Mirror Architecture Overview](https://github.com/numman-ali/cc-mirror/blob/main/docs/architecture/overview.md)
