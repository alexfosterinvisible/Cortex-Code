# github.com/numman-ali/cc-mirror
https://raw.githubusercontent.com/numman-ali/cc-mirror/main/README.md

# CC-MIRROR README

CC-MIRROR is a Node.js tool that enables users to create multiple isolated Claude Code instances connected to different AI providers. Here's what the documentation covers:

## Core Functionality

The tool allows setup of separate Claude Code variants, each with its own configuration, sessions, and API credentials. Users can launch variants directly from the terminal using custom commands like `zai`, `minimax`, or `mclaude`.

## Supported Providers

The platform integrates with five main providers:

- **Z.ai** — GLM models optimized for coding
- **MiniMax** — MiniMax-M2.1 unified model
- **OpenRouter** — Access to 100+ models
- **CCRouter** — Local LLM support
- **Mirror** — Native Claude with team capabilities

## Key Features

Users get complete isolation between variants, custom brand themes, prompt packs, team mode for multi-agent collaboration, and a tasks CLI for managing shared work. The tool supports one-command updates across all variants.

## Team Mode & Tasks

When enabled, team mode provides shared task management tools. The tasks CLI allows creating, updating, archiving, and visualizing task dependencies across projects.

## Installation

Users can run `npx cc-mirror` for an interactive setup or use quick-start commands with specific provider flags and API keys.

The project is MIT-licensed and maintained on npm and GitHub.
