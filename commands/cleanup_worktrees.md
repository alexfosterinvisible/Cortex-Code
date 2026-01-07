# Cleanup CxC Worktrees

Clean up isolated CxC worktrees and their associated resources.

## VARIABLES

action: $1 (all|specific|list)
cxc_id: $2 (optional, required if action is "specific")

## INSTRUCTIONS

Manage git worktrees created by isolated CxC workflows:
- If action is "list": Show all worktrees under [trees/] directory
- If action is "specific": Remove the specific worktree for the given cxc_id
- If action is "all": Remove all worktrees under [trees/] directory

## RUN

Based on the action:

### List worktrees
If action is "list":
- Run `git worktree list | grep "trees/"` to show isolated worktrees
- List the contents of the [trees/] directory with sizes

### Remove specific worktree
If action is "specific" and cxc_id is provided:
- Check if [trees/{cxc_id}] exists
- Run `git worktree remove trees/{cxc_id}` to remove it
- Report success or any errors

### Remove all worktrees
If action is "all":
- First list all worktrees that will be removed
- For each worktree under [trees/], run `git worktree remove`
- Clean up any remaining directories under [trees/]
- Run `git worktree prune` to clean up any stale entries

## REPORT

Report the results of the cleanup operation:
- Number of worktrees removed
- Any errors encountered
- Current status after cleanup