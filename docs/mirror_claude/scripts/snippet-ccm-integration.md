# CC-Mirror Integration Patterns & Real-World Usage

**Source:** [cc-mirror GitHub Repository](https://github.com/numman-ali/cc-mirror)

## Overview

CC-Mirror enables integration with multiple AI providers through isolated Claude Code variants. Each variant operates independently with its own configuration, sessions, themes, and API credentials.

---

## Integration Architecture

### Directory Structure

```
~/.cc-mirror/<variant>/
├── npm/                      # npm install root (cli.js location)
│   └── node_modules/
│       └── @anthropic-ai/
│           └── claude-code@2.0.76/
├── config/                   # CLAUDE_CONFIG_DIR
│   ├── settings.json        # Environment overrides, API keys
│   ├── .claude.json         # API-key approvals, MCP seeds
│   └── skills/              # Custom skills (e.g., dev-browser)
├── tweakcc/                 # Brand preset configuration
│   ├── config.json          # Theme settings
│   └── system-prompts/      # Provider-specific prompts
└── variant.json             # Metadata (name, provider, team mode)

Wrapper commands: ~/.local/bin/<variant>
```

### Provider System Categories

**1. Proxy Providers** (Z.ai, MiniMax, OpenRouter)
- Set custom base URLs and API keys
- Support optional prompt packs
- Optional team mode enablement
- Example: Redirect Claude API calls to Z.ai's GLM endpoint

**2. Router Providers** (CCRouter)
- Handle model mapping internally
- Optional authentication
- Route to local LLMs or custom endpoints

**3. Direct Providers** (Mirror)
- Connect directly to Anthropic Claude API
- Team mode enabled by default
- No proxy or routing

---

## Provider-Specific Integration Patterns

### Z.ai Integration

**Setup:**
```bash
npx cc-mirror quick --provider zai --api-key "$Z_AI_API_KEY"
```

**Configuration Applied:**
- Sets `Z_AI_API_KEY` in `settings.json`
- Adds deny list for server-side MCP tools
- Installs dev-browser skill by default
- Auto-selects "Carbon" theme preset (if using `--brand zai`)

**Environment Variables:**
```json
{
  "env": {
    "Z_AI_API_KEY": "your-api-key",
    "ANTHROPIC_BASE_URL": "https://api.zai.org/v1"
  }
}
```

**Use Case:** Access GLM Coding Plan models through Claude Code interface

---

### MiniMax Integration

**Setup:**
```bash
npx cc-mirror quick --provider minimax --api-key "$MINIMAX_API_KEY"
```

**Configuration Applied:**
- Seeds default MCP server entry in `.claude.json`
- Sets `MINIMAX_API_KEY` in `settings.json`
- Installs dev-browser skill
- Auto-selects "Pulse" theme preset (if using `--brand minimax`)

**MCP Server Seed Example:**
```json
{
  "mcpServers": {
    "minimax-coding-plan": {
      "command": "npx",
      "args": ["-y", "@minimax/mcp-server"],
      "env": {
        "MINIMAX_API_KEY": "your-api-key"
      }
    }
  }
}
```

**Use Case:** Integrate MiniMax M2.1 coding capabilities with MCP server support

---

### OpenRouter Integration

**Setup:**
```bash
npx cc-mirror quick --provider openrouter \
  --api-key "$OPENROUTER_API_KEY" \
  --model-sonnet "anthropic/claude-3.5-sonnet" \
  --model-opus "anthropic/claude-opus-4" \
  --model-haiku "anthropic/claude-3-5-haiku"
```

**Configuration Applied:**
- Custom model mapping to 100+ OpenRouter models
- Flexible provider selection (Anthropic, OpenAI, Google, etc.)
- Optional brand theme

**Environment Variables:**
```json
{
  "env": {
    "ANTHROPIC_API_KEY": "your-openrouter-key",
    "ANTHROPIC_BASE_URL": "https://openrouter.ai/api/v1",
    "MODEL_SONNET": "anthropic/claude-3.5-sonnet",
    "MODEL_OPUS": "anthropic/claude-opus-4",
    "MODEL_HAIKU": "anthropic/claude-3-5-haiku"
  }
}
```

**Use Case:** Access multiple AI models (Claude, GPT-4, Gemini) through single interface

---

### Claude Code Router (CCRouter) Integration

**Setup:**
```bash
npx cc-mirror quick --provider ccrouter
```

**Configuration Applied:**
- No API key required by default
- Routes to local LLM endpoints
- Internal model mapping

**Use Case:** Connect to locally hosted LLMs (Ollama, LM Studio, etc.)

---

### Mirror Claude Integration

**Setup:**
```bash
npx cc-mirror quick --provider mirror --name mclaude
```

**Configuration Applied:**
- Direct Anthropic API connection
- Team mode enabled by default
- No base URL override
- Pure Claude experience

**Environment Variables:**
```json
{
  "env": {
    "ANTHROPIC_API_KEY": "your-anthropic-key"
  }
}
```

**Use Case:** Official Claude API with team collaboration features

---

## Authentication Patterns

### API Key Management

**Automatic Storage:**
```bash
# API key written to settings.json
npx cc-mirror quick --provider zai --api-key "$Z_AI_API_KEY"

# Stored as ANTHROPIC_API_KEY for Claude Code compatibility
```

**Manual Configuration:**
```bash
# Edit variant settings directly
nano ~/.cc-mirror/zai/config/settings.json

# Update API key
{
  "env": {
    "ANTHROPIC_API_KEY": "new-api-key"
  }
}
```

**OAuth Bypass:**
Last 20 characters of API key stored in `.claude.json`:
```json
{
  "customApiKeyResponses": {
    "approved": ["...last-20-chars"]
  }
}
```
This skips OAuth login screen in interactive mode.

**Security Note:** `ANTHROPIC_AUTH_TOKEN` is stripped from variant settings to prevent conflicts.

---

## Workflow Integration Patterns

### Multi-Variant Development Workflow

```bash
# Research phase - use fast, cheap model
ccrouter "Research authentication best practices"

# Planning phase - use balanced model
mclaude "Create auth system architecture spec"

# Implementation phase - use powerful model
zai "Implement JWT authentication with refresh tokens"

# Review phase - use cost-effective model
minimax "Review auth implementation for security issues"
```

### Provider-Specific Task Routing

```bash
# Complex reasoning - OpenRouter with Claude Opus
openrouter "Design distributed system architecture"

# Code generation - Z.ai with GLM
zai "Generate REST API endpoints for user management"

# Documentation - MiniMax
minimax "Write comprehensive API documentation"

# Quick fixes - CCRouter with local LLM
ccrouter "Fix typo in README"
```

### Team Collaboration with Multiple Variants

```bash
# Team A: Planning with Mirror Claude (team mode)
cd ~/project
mclaude tasks create --subject "Design auth system"

# Team B: Implementation with Z.ai (team mode enabled)
zai-team tasks create --subject "Implement auth endpoints" --depends-on 1

# Team C: Testing with MiniMax (team mode enabled)
minimax-team tasks create --subject "Write auth tests" --depends-on 2

# Visualize workflow across variants
mclaude tasks graph
```

---

## Advanced Integration Patterns

### Custom Provider Integration

```bash
# Create custom provider variant
npx cc-mirror create --provider custom \
  --name myai \
  --base-url "https://api.custom-llm.com/v1" \
  --api-key "$CUSTOM_API_KEY"

# Optional: Add custom prompt pack
# Edit ~/.cc-mirror/myai/tweakcc/system-prompts/
```

### Environment Variable Override

```bash
# Override settings per-invocation
ANTHROPIC_BASE_URL="https://custom.api.com" zai "Run with custom endpoint"

# Override model selection (OpenRouter)
MODEL_SONNET="meta-llama/llama-3.1-405b" openrouter "Use Llama instead"
```

### MCP Server Integration

**Pattern 1: Pre-seeded MCP (MiniMax)**
```json
// Automatically added during variant creation
{
  "mcpServers": {
    "minimax-coding-plan": {
      "command": "npx",
      "args": ["-y", "@minimax/mcp-server"]
    }
  }
}
```

**Pattern 2: Manual MCP Addition**
```bash
# Edit .claude.json for any variant
nano ~/.cc-mirror/zai/config/.claude.json

# Add custom MCP server
{
  "mcpServers": {
    "my-custom-tool": {
      "command": "node",
      "args": ["./path/to/mcp-server.js"],
      "env": {
        "API_KEY": "your-key"
      }
    }
  }
}
```

---

## Maintenance & Updates

### Updating Variants

```bash
# Update single variant (re-run npm install, reapply tweakcc)
npx cc-mirror update zai

# Update all variants
npx cc-mirror update

# Update with configuration changes
npx cc-mirror update zai --brand minimax
npx cc-mirror update zai --enable-team-mode
```

### Variant Health Checks

```bash
# Check all variants for issues
npx cc-mirror doctor

# Expected output:
# ✓ zai - healthy (team mode: enabled)
# ✓ minimax - healthy (team mode: disabled)
# ✗ openrouter - npm install corrupted
```

### Theme Customization

```bash
# Launch tweakcc UI for variant
npx cc-mirror tweak mclaude

# Manual theme editing
nano ~/.cc-mirror/mclaude/tweakcc/config.json
```

---

## Real-World Use Cases

### 1. Cost Optimization

```bash
# Cheap model for simple tasks
ccrouter "Format this JSON"

# Mid-tier for balanced work
mclaude "Refactor this function"

# Premium for complex reasoning
openrouter --model-opus "Design system architecture"
```

### 2. Multi-Model Validation

```bash
# Get same task response from multiple providers
zai "Implement auth system" > zai-auth.md
minimax "Implement auth system" > minimax-auth.md
mclaude "Implement auth system" > mclaude-auth.md

# Compare approaches
diff zai-auth.md minimax-auth.md
```

### 3. Specialized Provider Routing

```bash
# Z.ai for coding-heavy tasks
zai "Write complex SQL query optimization"

# MiniMax for documentation
minimax "Generate API reference docs"

# Mirror Claude for planning
mclaude "Create project roadmap"
```

### 4. Isolated Experimentation

```bash
# Test different prompts without affecting main config
npx cc-mirror quick --provider mirror --name test-variant
test-variant "Experimental prompt"

# Remove when done
npx cc-mirror remove test-variant
```

### 5. Client-Specific Variants

```bash
# Create client-specific variants with different billing
npx cc-mirror quick --provider openrouter --name client-a \
  --api-key "$CLIENT_A_KEY"

npx cc-mirror quick --provider openrouter --name client-b \
  --api-key "$CLIENT_B_KEY"

# Use per client
client-a "Work on Client A project"
client-b "Work on Client B project"
```

---

## Troubleshooting Integration Issues

### API Connection Failures

```bash
# Verify API key in settings
cat ~/.cc-mirror/zai/config/settings.json | grep API_KEY

# Test connection directly
curl -H "Authorization: Bearer $Z_AI_API_KEY" https://api.zai.org/v1/models

# Update API key
nano ~/.cc-mirror/zai/config/settings.json
```

### Variant Not Found

```bash
# Ensure ~/.local/bin in PATH
echo $PATH | grep -q "$HOME/.local/bin" || export PATH="$HOME/.local/bin:$PATH"

# Verify wrapper exists
ls -la ~/.local/bin/zai

# Regenerate wrapper
npx cc-mirror update zai
```

### npm Installation Issues

```bash
# Re-install from scratch
npx cc-mirror update zai

# Check npm logs
cat ~/.cc-mirror/zai/npm/npm-debug.log
```

### Team Mode Not Activating

```bash
# Verify team mode enabled
npx cc-mirror list | grep -A1 zai

# Re-enable team mode
npx cc-mirror update zai --enable-team-mode

# Verify cli.js patch
grep "return !0" ~/.cc-mirror/zai/npm/node_modules/@anthropic-ai/claude-code/dist/cli.js
```

---

## Performance Optimization

### Minimize Variant Count

```bash
# List all variants
npx cc-mirror list

# Remove unused variants
npx cc-mirror remove old-variant

# Keep 3-5 active variants for best performance
```

### Shared npm Cache

CC-Mirror uses separate npm installations per variant to ensure isolation. To reduce disk usage:

```bash
# Check variant sizes
du -sh ~/.cc-mirror/*/

# Each variant ~200-300MB
# Consider removing variants not used in 30+ days
```

### Fast Variant Switching

```bash
# Use shell aliases for quick switching
alias dev='mclaude'
alias fast='ccrouter'
alias powerful='zai'

# Switch contexts rapidly
dev "Plan feature"
fast "Quick fix typo"
powerful "Complex refactoring"
```

---

## References

- [CC-Mirror GitHub Repository](https://github.com/numman-ali/cc-mirror)
- [CC-Mirror DESIGN.md](https://github.com/numman-ali/cc-mirror/blob/main/DESIGN.md)
- [CC-Mirror Architecture Overview](https://github.com/numman-ali/cc-mirror/blob/main/docs/architecture/overview.md)
- [Claude Code Official Docs](https://docs.claude.com/en/docs/claude-code)
- [OpenRouter API](https://openrouter.ai)
- [Z.ai Platform](https://zai.org)
- [MiniMax Platform](https://www.minimax.com)
