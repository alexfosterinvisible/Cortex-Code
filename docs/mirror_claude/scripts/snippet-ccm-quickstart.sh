#!/bin/bash
# CC-Mirror Quick Start Examples
# Source: https://github.com/numman-ali/cc-mirror
#
# CC-Mirror creates isolated Claude Code variants with custom providers.
# Each variant has independent config, sessions, themes, and API credentials.

# ============================================================================
# INTERACTIVE SETUP (TUI)
# ============================================================================

# Launch interactive terminal UI wizard
npx cc-mirror

# ============================================================================
# QUICK PROVIDER SETUPS (Fast CLI setup)
# ============================================================================

# Z.ai (GLM Coding Plan)
npx cc-mirror quick --provider zai --api-key "$Z_AI_API_KEY"

# MiniMax (MiniMax-M2.1)
npx cc-mirror quick --provider minimax --api-key "$MINIMAX_API_KEY"

# OpenRouter (100+ models) with custom model mapping
npx cc-mirror quick --provider openrouter --api-key "$OPENROUTER_API_KEY" \
  --model-sonnet "anthropic/claude-3.5-sonnet" \
  --model-opus "anthropic/claude-opus-4" \
  --model-haiku "anthropic/claude-3-5-haiku"

# Claude Code Router (local LLMs)
npx cc-mirror quick --provider ccrouter

# Mirror Claude (pure Claude with team mode enabled by default)
npx cc-mirror quick --provider mirror --name mclaude

# ============================================================================
# ADVANCED CREATE WITH OPTIONS
# ============================================================================

# Create with team mode enabled
npx cc-mirror create --provider zai --name zai-team --enable-team-mode

# Create with custom brand/theme
npx cc-mirror create --provider minimax --name minimax-custom --brand minimax

# Create with custom base URL
npx cc-mirror create --provider custom --name myai \
  --base-url "https://api.example.com" \
  --api-key "$CUSTOM_API_KEY"

# Create without theme tweaks or prompt packs
npx cc-mirror quick --provider zai --name zai-minimal \
  --no-tweak --no-prompt-pack

# ============================================================================
# VARIANT MANAGEMENT
# ============================================================================

# List all created variants
npx cc-mirror list

# Update specific variant (re-run npm install, reapply tweakcc)
npx cc-mirror update zai

# Update all variants
npx cc-mirror update

# Update with brand change
npx cc-mirror update zai --brand zai

# Remove/delete a variant
npx cc-mirror remove zai

# Health check all variants
npx cc-mirror doctor

# Launch tweakcc UI for a variant
npx cc-mirror tweak mclaude

# ============================================================================
# LAUNCHING VARIANTS
# ============================================================================

# Launch variants directly (wrappers in ~/.local/bin/)
zai          # Run Z.ai variant
minimax      # Run MiniMax variant
mclaude      # Run Mirror Claude variant

# ============================================================================
# CONFIGURATION OPTIONS
# ============================================================================

# Available CLI flags:
# --provider <name>          Provider: zai | minimax | openrouter | ccrouter | mirror | custom
# --name <name>              Variant name (becomes CLI command)
# --api-key <key>            Provider API key
# --base-url <url>           Custom API endpoint
# --model-sonnet <name>      Map to sonnet model (OpenRouter)
# --model-opus <name>        Map to opus model (OpenRouter)
# --model-haiku <name>       Map to haiku model (OpenRouter)
# --brand <preset>           Theme: auto | zai | minimax | openrouter | ccrouter | mirror
# --enable-team-mode         Enable team mode (TaskCreate, TaskGet, TaskUpdate, TaskList)
# --no-tweak                 Skip tweakcc theme application
# --no-prompt-pack           Skip prompt pack installation
# --no-skill-install         Skip dev-browser skill installation (Z.ai/MiniMax)
# --prompt-pack-mode <mode>  minimal | maximal (controls prompt overlay depth)

# ============================================================================
# DIRECTORY STRUCTURE
# ============================================================================

# Variants stored in: ~/.cc-mirror/<variant>/
# ├── npm/                    # npm install root (cli.js location)
# ├── config/                 # CLAUDE_CONFIG_DIR
# │   ├── settings.json      # environment overrides
# │   └── .claude.json       # API-key approvals + MCP seeds
# ├── tweakcc/               # brand preset configuration
# │   ├── config.json
# │   └── system-prompts/
# └── variant.json           # metadata
#
# Wrapper commands: ~/.local/bin/<variant>

# ============================================================================
# ARCHITECTURE
# ============================================================================

# CC-Mirror always installs @anthropic-ai/claude-code@2.0.76 into
# ~/.cc-mirror/<variant>/npm and runs its cli.js with custom environment
# variables and configuration.
