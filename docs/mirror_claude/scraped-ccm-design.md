# github.com/numman-ali/cc-mirror
https://raw.githubusercontent.com/numman-ali/cc-mirror/main/DESIGN.md

# cc-mirror Design Document

## Summary

The cc-mirror project creates isolated Claude Code variants with independent configurations and session stores. It provides a full-screen TUI for discovery, creation, and management while supporting unlimited providers with editable templates.

## Key Architecture Elements

The system organizes each variant in `~/.cc-mirror/<variant>` with separate directories for npm, config, tweakcc settings, and metadata. Wrappers install to `~/.local/bin/<variant>`.

Core functionality spans provider templates, brand presets, file operations, CLI entry points, and an Ink-based TUI wizard. The system uses tweakcc as a dependency to apply patches for each variant.

## Main Features

The TUI offers multiple workflows: home screen with variant management, quick setup with minimal configuration, an advanced create wizard with extensive customization options, management tools for updating or removing variants, and a doctor utility for system diagnostics.

Users can update binaries individually or globally, reapply brand presets, adjust API credentials, and toggle features like prompt packs and skill installation. Prompt packs function as provider overlays injected after tweakcc processing.

## Authentication & Configuration

"When an API key is supplied, cc-mirror writes `ANTHROPIC_API_KEY` into the variant config so Claude Code recognizes API-key auth during onboarding."

Wrappers load environment variables from settings.json at launch. The system stores the final 20 characters of API keys in `.claude.json` to bypass OAuth screens. Brand presets control user labels via `CLAUDE_CODE_USER_LABEL`.

## Provider Support

Providers are TypeScript objects extending `src/providers/index.ts`. MiniMax variants include MCP server seeds, while Z.ai variants receive deny lists for server-side tools and dev-browser installation by default.
