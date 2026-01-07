# Generate Git Branch Name

Based on the `## INSTRUCTIONS` (see below), take the `## VARIABLES` (see below), follow the `## RUN` (see below) section to generate a concise Git branch name following the specified format. Then follow the `## REPORT` (see below) section to report the results of your work.

## VARIABLES

issue_class: $1
cxc_id: $2
issue: $3

## INSTRUCTIONS

- Generate a branch name in the format: `<issue_class>-issue-<issue_number>-cxc-<cxc_id>-<concise_name>`
- The `<concise_name>` should be:
  - 3-6 words maximum
  - All lowercase
  - Words separated by hyphens
  - Descriptive of the main task/feature
  - No special characters except hyphens
- Examples:
  - `feat-issue-123-cxc-a1b2c3d4-add-user-auth`
  - `bug-issue-456-cxc-e5f6g7h8-fix-login-error`
  - `chore-issue-789-cxc-i9j0k1l2-update-dependencies`
  - `test-issue-323-cxc-m3n4o5p6-fix-failing-tests`
- Extract the issue number, title, and body from the issue JSON

## RUN

Generate the branch name based on the instructions above.
Do NOT create or checkout any branches - just generate the name.

## REPORT

Return ONLY the generated branch name (no other text)