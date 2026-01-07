# Example Commands

App-specific command templates for the CxC framework. Copy these to your project's [.claude/commands/] directory and customize the `[bracketed items]`.

## Files

| File | Purpose | Key Customizations |
|------|---------|-------------------|
| [conditional_docs.md] | Documentation routing based on task type | Paths to docs, directories |
| [health_check.md] | Run health check script | Health check script path |
| [in_loop_review.md] | Quick branch checkout + review workflow | Prepare/start commands, port |
| [install.md] | Initial project setup | Env files, scripts, directories |
| [prepare_app.md] | Setup app for review/test | Reset/start/stop scripts, port |
| [prime.md] | Understand codebase before task | README paths |
| [review_bg_iso.md] | Background review process | Review script path |
| [start.md] | Start application | Start script, port |
| [test_e2e.md] | E2E test runner with Playwright | Port, prepare command, agents dir |
| [test.md] | Full test suite (lint, type check, build) | All test commands per stack |
| [tools.md] | List available Claude tools | None |
| [track_agentic_kpis.md] | Track CxC performance metrics | KPI file path |

## E2E Tests ([e2e/])

| File | Purpose |
|------|---------|
| [test_basic_query.md] | Example: basic query flow |
| [test_export_functionality.md] | Example: export/download flow |
| [README.md] | E2E test creation guide |

## Customization Pattern

All app-specific values use `[brackets]`:

```markdown
- Run [./scripts/start.sh]
- Navigate to http://localhost:[5173]
- Check [app/server] directory
```

**To customize:**
1. Copy file to your [.claude/commands/]
2. Search for `[` 
3. Replace each `[bracketed item]` with your value
4. Remove brackets

## Why Examples?

These commands were extracted from a working NL-to-SQL application. They're **app-specific** because they reference:
- Specific ports (5173, 8000)
- Specific directories (app/server, app/client)
- Specific scripts (start.sh, reset_db.sh)
- Specific UI elements and test flows

The **framework commands** (in parent [commands/] directory) are generic and work across all projects.


