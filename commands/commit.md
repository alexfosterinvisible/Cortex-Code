# Generate Git Commit

Based on the `## INSTRUCTIONS` (see below), take the `## VARIABLES` (see below), follow the `## RUN` (see below) section to create a git commit with a properly formatted message. Then follow the `## REPORT` (see below) section to report the results of your work.

## VARIABLES

agent_name: $1
issue_class: $2
issue: $3

## INSTRUCTIONS

- Generate a concise commit message in the format: `<agent_name>: <issue_class>: <commit message>`
- The `<commit message>` should be:
  - Present tense (e.g., "add", "fix", "update", not "added", "fixed", "updated")
  - 50 characters or less
  - Descriptive of the actual changes made
  - No period at the end
- Examples:
  - `sdlc_planner: feat: add user authentication module`
  - `sdlc_implementor: bug: fix login validation error`
  - `sdlc_planner: chore: update dependencies to latest versions`
- Extract context from the issue JSON to make the commit message relevant
- Don't include any 'Generated with...' or 'Authored by...' in the commit message. Focus purely on the changes made.

## RUN

1. Run `git diff HEAD` to understand what changes have been made
2. Run `git add -A` to stage all changes
3. Run `git commit -m "<generated_commit_message>"` to create the commit

## REPORT

Return ONLY the commit message that was used (no other text)