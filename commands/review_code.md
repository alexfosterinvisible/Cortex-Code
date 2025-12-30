# Review Code

Review code changes against requirements/specs for a Python package (no UI).

## VARIABLES

spec_file: $1 (optional - defaults to finding spec from branch name or recent changes)

## INSTRUCTIONS

- Check current git branch: `git branch --show-current`
- Get recent changes: `git diff origin/master --stat` and `git log origin/master..HEAD --oneline`
- If spec_file not provided, look for matching spec in `specs/` based on branch name or recent commits
- Read the spec file to understand requirements
- Review the code changes against the spec:
  - Run tests: `uv run pytest -v`
  - Check types: `uv run pyright` (if configured)
  - Review implementation matches spec requirements
- Document any issues found

## REPORT

Return JSON:

```json
{
    "success": true/false,
    "review_summary": "2-4 sentences on what was reviewed and outcome",
    "tests_passed": true/false,
    "test_output": "summary of test results",
    "review_issues": [
        {
            "issue_number": 1,
            "description": "what's wrong",
            "resolution": "how to fix",
            "severity": "skippable|tech_debt|blocker"
        }
    ]
}
```


