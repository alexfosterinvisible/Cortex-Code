# E2E Test Examples

This directory contains example end-to-end test templates for the CxC framework.

## Usage

1. Copy the relevant test template to your project's [.claude/commands/e2e/] directory
2. Replace all `[bracketed items]` with your project-specific values
3. Run tests using the [test_e2e.md] command

## Available Examples

| File | Description |
|------|-------------|
| [test_basic_query.md] | Tests basic query input and result display |
| [test_export_functionality.md] | Tests CSV export for tables and query results |

## Creating New E2E Tests

Follow this structure:

```markdown
# E2E Test: [Test Name]

[Brief description of what this test validates]

## User Story

As a [user role]  
I want to [action]  
So that I can [benefit]

## Test Steps

1. Navigate to the `Application URL`
2. Take a screenshot of the initial state
3. **Verify** [expected condition]
...

## Success Criteria
- [Criterion 1]
- [Criterion 2]
...
```

## Customization Pattern

All app-specific values are wrapped in `[brackets]`. Common items to customize:

- Application name/title
- UI element names (buttons, inputs, sections)
- Test queries and expected outputs
- File names and paths
- User roles and goals


