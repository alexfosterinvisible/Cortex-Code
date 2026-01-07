# Classify Issue and Generate Branch Name

Based on the `## GITHUB_ISSUE` (see below), perform BOTH tasks in a single response.

## VARIABLES

cxc_id: $1
issue: $2

## TASK 1: CLASSIFY ISSUE

Determine if this issue is a:
- `/bug` - Bug fix, error, crash, broken functionality
- `/chore` - Maintenance, refactoring, dependency updates, config changes
- `/feature` - New feature, enhancement, addition

## TASK 2: GENERATE BRANCH NAME

Generate a branch name in format: `<type>-issue-<number>-cxc-<cxc_id>-<slug>`

Where:
- `<type>` is `feat`, `bug`, or `chore` (based on classification)
- `<number>` is the issue number from the JSON
- `<cxc_id>` is provided above
- `<slug>` is 3-6 lowercase words from the issue title, hyphen-separated

## GITHUB_ISSUE

$2

## RESPONSE FORMAT

Respond with ONLY this JSON (no markdown, no explanation):

```json
{"issue_class": "/feature", "branch_name": "feat-issue-123-cxc-abc123-add-user-auth"}
```

Replace values with your classification and generated branch name.

