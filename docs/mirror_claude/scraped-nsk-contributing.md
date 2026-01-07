# github.com/numman-ali/n-skills
https://raw.githubusercontent.com/numman-ali/n-skills/main/CONTRIBUTING.md

# Contributing to n-skills

This is a **curated marketplace**. All submissions are reviewed for quality.

## Two Ways to Contribute

### Option 1: External Skill (Recommended)

Keep your skill in your own repo, we sync it automatically.

**Benefits:**
- You maintain full ownership and control
- Updates sync automatically (daily)
- Clear attribution preserved

**Process:**

1. Open an [issue](https://github.com/numman-ali/n-skills/issues) with:
   - Your repo URL
   - Path to skill folder (e.g., `skills/my-skill`)
   - Brief description of what it does

2. If approved, submit a PR adding your entry to `sources.yaml`:

```yaml
- name: your-skill
  description: What it does and when to use it
  source:
    repo: your-username/your-repo
    path: skills/your-skill   # Path within your repo
    ref: main                 # Branch, tag, or commit
  target:
    category: tools           # tools, development, productivity, automation, data, documentation
    path: skills/tools/your-skill
  author:
    name: Your Name
    github: your-username
  license: MIT
  homepage: https://github.com/your-username/your-repo
```

3. Once merged, our sync workflow copies your skill folder daily.

### Option 2: Native Skill

Submit the skill directly to this repo.

1. Fork this repository
2. Add your skill to the appropriate category under `skills/`
3. Add an entry to `sources.yaml` with `native: true`
4. Open a PR

---

## SKILL.md Format

All skills must have a valid SKILL.md:

```yaml
---
name: your-skill-name
description: |
  Brief description including:
  - What the skill does
  - When to use it (trigger phrases)
  - Any requirements (API keys, etc.)
---

# Skill Name

[Instructions here]
```

See [docs/skill-format.md](docs/skill-format.md) for the complete specification.

## Skill Structure

```
your-skill/
├── SKILL.md              # Required: Skill definition
├── references/           # Optional: Supporting documentation
│   └── api-docs.md
├── scripts/              # Optional: Helper scripts
│   └── helper.py
└── assets/               # Optional: Templates, configs
    └── template.json
```

## Categories

| Category | Description |
|----------|-------------|
| **tools** | CLI tools and utilities |
| **development** | Language/framework assistance |
| **productivity** | Workflow automation |
| **automation** | Browser, CI/CD, system |
| **data** | Databases, data processing |
| **documentation** | Docs, diagrams, specs |

## Quality Standards

**Required:**
- Clear, actionable instructions
- Working examples
- Proper error handling guidance
- No hardcoded secrets
- Apache 2.0 or MIT license

**Nice to have:**
- Screenshots or demos
- Multiple usage examples
- Edge case handling
- Integration tests

## Sync Configuration

For external skills, you can control what gets synced:

```yaml
sync:
  include:              # Specific files/folders to copy
    - SKILL.md
    - references/
    - scripts/
  exclude:              # Patterns to skip (defaults below)
    - node_modules/
    - "*.lock"
    - tmp/
```

If `include` is not specified, everything is copied except `exclude` patterns.

## Review Process

1. **Issue triage** - We assess fit for the marketplace
2. **Format validation** - SKILL.md structure checked
3. **Manual review** - Quality and usefulness evaluated
4. **Security review** - Scripts and dependencies audited
5. **Merge** - Entry added, sync begins

PRs are typically reviewed within 1-2 days.

## Questions?

- Open an [issue](https://github.com/numman-ali/n-skills/issues)
- DM [@nummanali](https://x.com/nummanali) on X
