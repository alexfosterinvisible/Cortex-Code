# specs/ Directory (Claude)

## Structure

- `specs/` - Plans and specifications for features/issues
- `specs/reports/` - Test reports, verification results, analysis documents

## Naming Convention

All files should be prefixed with `YYMMDD_` (year-month-day):

```
260106_feature_name.md
260115_bug_fix_analysis.md
```

This ensures chronological ordering and easy identification of when documents were created.

## Examples

```
specs/
├── CLAUDE.md                              # This file
├── 260105_auth_system_spec.md            # Feature spec
├── 260106_mcp_server_implementation.md   # Implementation plan
└── reports/
    ├── 260106_mcp_server_test_report.md  # Test report
    └── 260107_coverage_analysis.md       # Analysis report
```
