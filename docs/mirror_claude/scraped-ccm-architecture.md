# github.com/numman-ali/cc-mirror/docs
https://raw.githubusercontent.com/numman-ali/cc-mirror/main/docs/architecture/overview.md

# CC-Mirror Architecture Overview

CC-Mirror is a system for creating Claude Code variants with different providers and configurations. Here's the key structure:

## Core Components

The system consists of three main layers: a CLI/TUI interface, a core engine managing variants, and stored configurations in `~/.cc-mirror/<name>/` directories with shell wrappers in `~/.local/bin/`.

## Build Process

Creating a variant involves eight sequential steps: directory creation, npm installation, optional team mode patching, theme application, configuration writing, prompt pack copying, wrapper generation, and metadata finalization.

## Provider System

Providers connect Claude Code to different APIs. The document describes three provider categories: proxy services (zai, minimax, openrouter) that require base URLs and API keys; routers (ccrouter) with optional credentials; and direct variants (mirror) requiring neither credential nor URL configuration.

## Team Mode Implementation

Team mode is activated through function patching in the CLI executable, replacing a disabled function that returns false with one returning true. This occurs during creation with the `--enable-team-mode` flag or automatically for providers with `enablesTeamMode: true`.

## Variant Storage

Each variant maintains its own directory containing the npm installation, configuration files, theme settings, and metadata, with the shell wrapper providing command-line access.
