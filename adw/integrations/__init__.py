"""ADW Integration modules for external services.

Provides:
- git_ops: Git operations (branch, commit, push, PR)
- github: GitHub API operations (fetch issue, comment, PR)
- worktree_ops: Worktree management and port allocation
- workflow_ops: Workflow orchestration helpers
- r2_uploader: Cloudflare R2 screenshot uploads
"""
# Lazy imports to avoid circular dependencies
