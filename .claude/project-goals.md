# Project Goals

## Vision
Fully automated Issue -> PR -> Ship pipeline using git worktrees and extensive self-validation, serving as an execution arm of a larger orchestrator agent system.

ADW (AI Developer Workflow) processes GitHub issues through a complete SDLC: plan -> build -> test -> review -> document -> ship, with each phase running in isolated git worktrees for safe parallel execution.

## Target Users
- **AI/Automation engineers** building AI-powered development tools
- Engineers integrating ADW into larger orchestration systems
- Teams wanting autonomous development capacity

## Key Features
- **Full SDLC automation** - Plan, build, test, review, document, ship
- **Isolated execution** - Git worktrees with dedicated ports per workflow
- **Self-validation** - Up to 3 auto-fix loops for test/review failures
- **Model selection** - Dynamic Haiku/Sonnet/Opus based on task complexity
- **Persistent state** - ADW state files track workflow progress
- **GitHub integration** - Issue comments, PR creation, webhook triggers

## Success Metrics
- **Code quality metrics** - Test coverage, passing tests, successful reviews
- **PR merge success rate** - Percentage of auto-generated PRs that merge cleanly
- **Self-healing rate** - Issues auto-resolved without human intervention

## Constraints
- **Claude Code dependency** - Requires Claude Code CLI to function
- **GitHub-only integration** - Currently only supports GitHub as issue/PR source
- **Isolated execution** - Must use git worktrees for safety and parallelism
- **Purposeful brittleness** - No fallbacks/defaults during LLM dev phase

---
*This file is maintained by the user. Update it when business objectives change.*
