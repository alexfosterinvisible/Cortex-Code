# github.com/numman-ali/n-skills
https://raw.githubusercontent.com/numman-ali/n-skills/main/AGENTS.md

# n-skills Repository Overview

**n-skills** is a curated marketplace for AI coding agent plugins, hosted at https://github.com/numman-ali/n-skills. The project provides high-quality skills following the agentskills.io SKILL.md format.

## Core Features

The repository includes three available skills:

1. **zai-cli**: Offers "Z.AI vision, search, reader, and GitHub exploration via MCP"
2. **dev-browser**: Enables browser automation with persistent page state for website navigation and web data extraction
3. **gastown**: Described as a "Multi-agent orchestrator for Claude Code" for coordinating multiple AI agents

## Installation & Usage

Installation occurs through the openskills package manager:
```
npm i -g openskills
openskills install numman-ali/n-skills
```

Skills are invoked using the command pattern `openskills read <skill-name>`.

## Maintainer Guidelines

The documentation emphasizes critical configuration rules for plugin integration:

- Repository source must reference the root directory `"./"` rather than individual skill folders
- Skill paths should be relative to the repository root
- Configuration must exclude `$schema` and `upstream` keys to prevent validation errors

Versioning follows a v1.MAJOR.MINOR scheme, with major version bumps for new skills or breaking changes, and minor bumps for fixes and documentation updates.

The repository includes automated GitHub Actions workflows for syncing external skills using content hash validation rather than commit hashes, ensuring reliable detection of actual file modifications.
