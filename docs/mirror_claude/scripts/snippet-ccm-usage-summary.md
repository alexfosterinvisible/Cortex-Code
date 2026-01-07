# CC-Mirror Usage Summary & Key Patterns

**Source:** [cc-mirror GitHub Repository](https://github.com/numman-ali/cc-mirror)
**Generated:** 2026-01-06

---

## What is CC-Mirror?

CC-Mirror creates **isolated Claude Code variants** with custom AI providers. Each variant has independent configuration, sessions, themes, and API credentials—completely separate from standard Claude Code and from each other.

**Key Benefits:**
- Access multiple AI providers (Z.ai, MiniMax, OpenRouter, local LLMs)
- Isolated configurations prevent interference
- Team mode for multi-agent workflows
- Cost optimization through provider selection
- Client-specific variants with separate billing

---

## Quick Reference Commands

### Installation & Setup

```bash
# Interactive TUI wizard
npx cc-mirror

# Fast CLI setup
npx cc-mirror quick --provider <provider> --api-key "$API_KEY"

# Full configuration wizard
npx cc-mirror create
```

### Variant Management

```bash
npx cc-mirror list              # List all variants
npx cc-mirror update [name]     # Update variant(s)
npx cc-mirror remove <name>     # Delete variant
npx cc-mirror doctor            # Health check
npx cc-mirror tweak <name>      # Launch theme UI
```

### Task Management (Team Mode)

```bash
npx cc-mirror tasks                              # List tasks
npx cc-mirror tasks create --subject "..."       # Create task
npx cc-mirror tasks update <id> --status <s>     # Update task
npx cc-mirror tasks archive <id>                 # Archive task
npx cc-mirror tasks graph                        # Visualize dependencies
npx cc-mirror tasks clean --resolved --force     # Clean completed
```

---

## Provider Quick Start Examples

### Z.ai (GLM Coding Plan)

```bash
npx cc-mirror quick --provider zai --api-key "$Z_AI_API_KEY"
zai "Your prompt here"
```

**Features:** GLM models, dev-browser skill, Carbon theme preset

---

### MiniMax (M2.1)

```bash
npx cc-mirror quick --provider minimax --api-key "$MINIMAX_API_KEY"
minimax "Your prompt here"
```

**Features:** MCP server integration, Pulse theme preset

---

### OpenRouter (100+ Models)

```bash
npx cc-mirror quick --provider openrouter \
  --api-key "$OPENROUTER_API_KEY" \
  --model-sonnet "anthropic/claude-3.5-sonnet" \
  --model-opus "anthropic/claude-opus-4"

openrouter "Your prompt here"
```

**Features:** Multi-model access, flexible provider selection

---

### CCRouter (Local LLMs)

```bash
npx cc-mirror quick --provider ccrouter
ccrouter "Your prompt here"
```

**Features:** Local LLM routing, no API key required

---

### Mirror Claude (Pure Claude + Team Mode)

```bash
npx cc-mirror quick --provider mirror --name mclaude
mclaude "Your prompt here"
```

**Features:** Official Claude API, team mode enabled by default

---

## Key Configuration Options

| Flag | Description | Example |
|------|-------------|---------|
| `--provider` | Provider selection | `zai`, `minimax`, `openrouter`, `ccrouter`, `mirror`, `custom` |
| `--name` | Variant CLI command name | `--name myai` → command: `myai` |
| `--api-key` | Provider API key | `--api-key "$API_KEY"` |
| `--base-url` | Custom API endpoint | `--base-url "https://api.example.com"` |
| `--model-sonnet` | Sonnet model mapping (OR) | `--model-sonnet "anthropic/claude-3.5-sonnet"` |
| `--model-opus` | Opus model mapping (OR) | `--model-opus "anthropic/claude-opus-4"` |
| `--model-haiku` | Haiku model mapping (OR) | `--model-haiku "anthropic/claude-3-5-haiku"` |
| `--brand` | Theme preset | `auto`, `zai`, `minimax`, `openrouter`, `ccrouter`, `mirror` |
| `--enable-team-mode` | Enable team features | Flag only (no value) |
| `--no-tweak` | Skip theme application | Flag only |
| `--no-prompt-pack` | Skip prompt pack install | Flag only |
| `--prompt-pack-mode` | Prompt overlay depth | `minimal`, `maximal` |

---

## Team Mode Patterns

### Enable Team Mode

```bash
# During creation
npx cc-mirror create --provider zai --name zai-team --enable-team-mode

# Or update existing
npx cc-mirror update zai --enable-team-mode
```

### Project Scoping

```bash
# Automatic scoping by directory
cd ~/projects/api && mclaude        # Team: mclaude-api
cd ~/projects/frontend && mclaude   # Team: mclaude-frontend

# Manual team override
TEAM=backend mclaude                # Team: mclaude-myproject-backend
```

### Task Dependencies

```bash
# Create dependent workflow
mclaude tasks create --subject "Design schema"
mclaude tasks create --subject "Write migrations" --depends-on 1
mclaude tasks create --subject "Seed data" --depends-on 2

# Visualize
mclaude tasks graph
```

---

## Common Workflows

### 1. Multi-Variant Development

```bash
# Research (cheap model)
ccrouter "Research auth best practices"

# Planning (balanced model)
mclaude "Create auth system spec"

# Implementation (powerful model)
zai "Implement JWT authentication"

# Review (cost-effective)
minimax "Review auth implementation"
```

### 2. Cost Optimization

```bash
# Simple tasks → local LLM
ccrouter "Format this JSON"

# Standard tasks → Mirror Claude
mclaude "Refactor this function"

# Complex tasks → Z.ai or OpenRouter
zai "Design distributed system"
```

### 3. Client-Specific Variants

```bash
# Create per-client variants
npx cc-mirror quick --provider openrouter --name client-a --api-key "$CLIENT_A_KEY"
npx cc-mirror quick --provider openrouter --name client-b --api-key "$CLIENT_B_KEY"

# Use separately
client-a "Work on Client A code"
client-b "Work on Client B code"
```

### 4. Multi-Model Validation

```bash
# Get responses from multiple providers
zai "Implement feature X" > zai-response.md
minimax "Implement feature X" > minimax-response.md
mclaude "Implement feature X" > mclaude-response.md

# Compare approaches
diff zai-response.md minimax-response.md
```

---

## Directory Structure

```
~/.cc-mirror/<variant>/
├── npm/                      # Claude Code installation
│   └── node_modules/
│       └── @anthropic-ai/claude-code@2.0.76/
├── config/                   # Configuration directory
│   ├── settings.json        # API keys, env vars
│   ├── .claude.json         # MCP servers, API approvals
│   └── skills/              # Custom skills
├── tweakcc/                 # Theme configuration
│   ├── config.json
│   └── system-prompts/
└── variant.json             # Metadata

Wrappers: ~/.local/bin/<variant>
```

---

## Troubleshooting Quick Reference

### Variant Not Found

```bash
# Add to PATH
export PATH="$HOME/.local/bin:$PATH"

# Regenerate wrapper
npx cc-mirror update <variant>
```

### API Connection Issues

```bash
# Check API key
cat ~/.cc-mirror/<variant>/config/settings.json | grep API_KEY

# Update API key
nano ~/.cc-mirror/<variant>/config/settings.json
```

### Team Mode Not Working

```bash
# Verify enabled
npx cc-mirror list

# Re-enable
npx cc-mirror update <variant> --enable-team-mode
```

### npm Installation Corrupted

```bash
# Re-install
npx cc-mirror update <variant>

# Full health check
npx cc-mirror doctor
```

---

## Architecture Summary

**Core Concept:** Each variant is an isolated installation of `@anthropic-ai/claude-code@2.0.76` with custom:
- Environment variables (API keys, base URLs)
- Configuration files (`settings.json`, `.claude.json`)
- Themes (via tweakcc)
- System prompts (provider-specific)
- Shell wrappers (launch commands)

**Team Mode:** Single-function patch in `cli.js` (`return !1` → `return !0`) enables TaskCreate, TaskGet, TaskUpdate, TaskList tools plus orchestrator skill.

**Provider Templates:** Define authentication, base URLs, model mappings, and feature flags per provider type.

**Isolation:** Variants stored in separate `~/.cc-mirror/<variant>/` directories with independent npm installations, configs, and sessions.

---

## Best Practices

1. **Limit Active Variants:** Keep 3-5 variants for performance (each ~200-300MB)
2. **Use Descriptive Names:** `zai-team`, `mclaude`, `or-opus` better than `variant1`
3. **Enable Team Mode Selectively:** Only on variants used for multi-agent workflows
4. **Archive Completed Tasks:** Use `tasks archive` to preserve history while keeping lists clean
5. **Update Regularly:** Run `npx cc-mirror update` monthly to refresh npm packages
6. **Health Check:** Run `npx cc-mirror doctor` after major updates
7. **Document Provider Usage:** Track which variant is best for which task type

---

## Advanced Patterns

### Custom Provider

```bash
npx cc-mirror create --provider custom \
  --name myai \
  --base-url "https://custom-api.com/v1" \
  --api-key "$CUSTOM_KEY"
```

### Environment Overrides

```bash
# Per-invocation override
ANTHROPIC_BASE_URL="https://alt.api.com" zai "Prompt"

# OpenRouter model override
MODEL_SONNET="meta-llama/llama-3.1-405b" openrouter "Prompt"
```

### Custom MCP Servers

```bash
# Edit .claude.json
nano ~/.cc-mirror/<variant>/config/.claude.json

# Add custom server
{
  "mcpServers": {
    "my-tool": {
      "command": "node",
      "args": ["./mcp-server.js"],
      "env": {"API_KEY": "key"}
    }
  }
}
```

---

## Version & Compatibility

- **Pinned Version:** `@anthropic-ai/claude-code@2.0.76`
- **Node.js:** Requires Node 16+
- **Platform:** macOS, Linux (Windows via WSL)
- **Shell:** Bash-compatible shell required for wrappers

---

## References

- [CC-Mirror GitHub](https://github.com/numman-ali/cc-mirror)
- [DESIGN.md](https://github.com/numman-ali/cc-mirror/blob/main/DESIGN.md)
- [Architecture Overview](https://github.com/numman-ali/cc-mirror/blob/main/docs/architecture/overview.md)
- [Claude Code Docs](https://docs.claude.com/en/docs/claude-code)

---

## Quick Start Checklist

- [ ] Install: `npx cc-mirror`
- [ ] Create variant: `npx cc-mirror quick --provider <p> --api-key "$KEY"`
- [ ] Test launch: `<variant> "Test prompt"`
- [ ] Enable team mode (if needed): `npx cc-mirror update <v> --enable-team-mode`
- [ ] Add to PATH: `export PATH="$HOME/.local/bin:$PATH"`
- [ ] Health check: `npx cc-mirror doctor`
- [ ] List variants: `npx cc-mirror list`

---

**Generated by CxC Framework Worker Agent**
**Task:** Search and compile cc-mirror usage examples and patterns
