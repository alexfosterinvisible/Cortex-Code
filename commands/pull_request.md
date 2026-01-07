# Create Pull Request

Based on the `## INSTRUCTIONS` (see below), take the `## VARIABLES` (see below), follow the `## RUN` (see below) section to create a pull request. Then follow the `## REPORT` (see below) section to report the results of your work.

## VARIABLES

branch_name: $1
issue: $2
plan_file: $3
cxc_id: $4

## INSTRUCTIONS

- Generate a pull request title in the format: `<issue_type>: #<issue_number> - <issue_title>`
- The PR body should include:
  - A summary section with the issue context
  - Link to the implementation `plan_file` if it exists
  - Reference to the issue (Closes #<issue_number>)
  - CxC tracking ID
  - A checklist of what was done
  - A summary of key changes made
- Extract issue number, type, and title from the issue JSON
- Examples of PR titles:
  - `feat: #123 - Add user authentication`
  - `bug: #456 - Fix login validation error`
  - `chore: #789 - Update dependencies`
  - `test: #1011 - Test xyz`
- Don't mention Claude Code in the PR body - let the author get credit for this.

## RUN

1. Run `git diff origin/main...HEAD --stat` to see a summary of changed files
2. Run `git log origin/main..HEAD --oneline` to see the commits that will be included
3. Run `git diff origin/main...HEAD --name-only` to get a list of changed files
4. Run `git push -u origin <branch_name>` to push the branch
5. Set GH_TOKEN environment variable from GITHUB_PAT if available, then run `gh pr create --title "<pr_title>" --body "<pr_body>" --base main` to create the PR
6. Capture the PR URL from the output

## REPORT

Return ONLY the PR URL that was created (no other text)