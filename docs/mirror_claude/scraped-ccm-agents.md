# github.com/numman-ali/cc-mirror
https://raw.githubusercontent.com/numman-ali/cc-mirror/main/AGENTS.md

# Repository Guidelines Summary

This document outlines the structure and conventions for a TypeScript/Node.js project called cc-mirror, which manages Claude Code variants across different AI providers.

## Key Structural Elements

The project divides into several domains:

- **CLI & TUI**: Command-line and terminal UI interfaces for variant management
- **Core**: Variant creation/updating logic organized around "steps" and "prompt packs"
- **Providers & Brands**: Configuration for different AI services (Z.ai, MiniMax, etc.) with theme presets
- **Team Mode**: Multi-agent collaboration features with task storage and dynamic team naming
- **Tests & Docs**: Comprehensive testing framework and architecture documentation

## Runtime Configuration

Variants store configuration in `~/.cc-mirror/<variant>/` with separate directories for settings, TweakCC theming, npm packages, and skill orchestration. A wrapper script at `~/.local/bin/<variant>` manages environment variables and initialization.

## Notable Design Decisions

1. **Team names are purely directory-based** at runtime, derived from project folders with optional `TEAM` environment variable modifiers
2. **Provider blocked tools** are defined per-brand and merged with team-mode toolsets
3. **Build steps are sequential** with specific ordering (theming before team mode to ensure config exists)
4. **Prompt overlays are sanitized** to avoid template literal issues in TweakCC

## Development Workflow

Standard commands include `npm run dev` (CLI), `npm run tui` (wizard interface), `npm test` (testing), and `npm run bundle` (production build). Configuration inspection and team verification use standard file inspection and grep patterns.
