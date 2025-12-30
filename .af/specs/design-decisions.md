# Design Decisions

## 2025-12-30
- Keep framework command templates under `commands/` in this repo; consumer repos should place overrides in `.claude/commands`. `ADWConfig.load` now auto-adds `.claude/commands` if present.
- Reintroduce explicit `_iso` workflow modules and group them under `adw/workflows/wt/` for worktree isolation; group non-worktree entrypoints under `adw/workflows/reg/` for parsability.
- Default CLI routes to worktree-isolated workflows. Non-worktree entrypoints currently delegate to `wt/*_iso` until reg implementations are restored.
- Skip backward-compatibility shims for old `adw.*` imports for now; revisit once external repos exist.
