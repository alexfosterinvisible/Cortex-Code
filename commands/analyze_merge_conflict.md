# Analyze Merge Conflict

Inspect a failed git merge and provide recommended next steps with commands and consequences. **ANALYSIS ONLY - DO NOT TAKE ACTION.**

## VARIABLES

branch_name: $1
merge_error: $2
repo_root: $3

## INSTRUCTIONS

You are analyzing a failed merge to help the developer understand their options. **DO NOT execute any git commands that modify state.**

### Step 1: Gather Information (READ-ONLY)

Run these diagnostic commands to understand the conflict:

```bash
# Current state
git status
git branch -v

# What's different between branches
git log --oneline main..{branch_name} | head -20
git log --oneline {branch_name}..main | head -20

# Show files that would conflict
git diff --name-only main {branch_name}

# Show the actual diff for conflicting files
git diff main {branch_name} -- <conflicting_files>

# Check for uncommitted changes
git status --porcelain

# Check stash
git stash list
```

### Step 2: Identify Conflict Type

Determine which category the conflict falls into:
1. **Uncommitted local changes** - Files modified but not committed
2. **Diverged branches** - Both branches have commits the other doesn't have
3. **Same-file edits** - Both branches modified the same files differently
4. **Stale branch** - Feature branch is far behind main

### Step 3: Generate Resolution Options

For each option, provide:
- The exact commands to run
- What the command does
- Potential consequences (data loss risk, reversibility)
- When to use this option

## REPORT

Output your analysis in this exact format:

```
## 🔍 MERGE CONFLICT ANALYSIS

### Conflict Type
<one of: uncommitted_changes | diverged_branches | same_file_edits | stale_branch | multiple>

### Current State Summary
- Main branch: <commit hash and status>
- Feature branch: {branch_name}
- Uncommitted files: <list or "none">
- Commits ahead of main: <count>
- Commits behind main: <count>

### Files in Conflict
<list each file with brief description of what changed>

---

## 🛠️ RESOLUTION OPTIONS

### Option 1: [SAFEST] <name>
**Risk Level**: Low | Medium | High
**Reversible**: Yes | Partially | No
**Data Loss Risk**: None | Possible | Likely

**Commands:**
```bash
<exact commands>
```

**What this does:**
<explanation>

**When to use:**
<scenario>

---

### Option 2: <name>
<same format>

---

### Option 3: <name>
<same format>

---

## ⚠️ WARNINGS
<any critical warnings about the specific situation>

## 💡 RECOMMENDATION
Based on this analysis, the recommended approach is **Option X** because:
<reasoning>
```

## IMPORTANT

- **DO NOT** run `git merge`, `git rebase`, `git reset --hard`, or any command that modifies git history
- **DO NOT** delete branches or discard changes
- **ONLY** gather information and provide recommendations
- Output should be helpful for a developer to make an informed decision

