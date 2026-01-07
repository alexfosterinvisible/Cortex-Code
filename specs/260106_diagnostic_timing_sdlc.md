<!--
Original instruction:
make a plan in specs/diagnostic_timing_SDLC.spec for setting up temporary repo in code4b/cxc_temp_repos/, doing cxc_setup command, creating a series of issues with dependencies using mclaude team orchestration mode, then running parallel and recording time everything takes to detect and diagnose unreasonable bottlenecks. include this instruction in a <!-- md comment --> at the top verbatim. then execute it. Don't check in with me except up-front right now so I can walk off
-->

# SDLC Timing Diagnostic Plan (Claude)

## Objective
Stress test the CxC MCP server with 10+ issues running full ZTE (Zero Touch Execution) pipeline. Identify bottlenecks, missing features, and bugs by timing each phase.

## Test Environment
- Temporary repo: `/Users/dev3/code4b/cxc_temp_repos/timing-test-YYMMDD/`
- CxC Framework: `/Users/dev3/code4b/cxc-framework/`
- MCP Server: Using MCP tools exclusively (no CLI fallback)

## Phase 1: Setup (Estimated: 5 min)
1. Create temp directory structure
2. Initialize git repo with basic Python project structure
3. Create GitHub remote repo via `gh repo create`
4. Run CxC setup (create .cxc.yaml, .env)
5. Verify MCP tools are accessible

## Phase 2: Issue Creation (Estimated: 10 min)
Create 10-12 issues with dependency chain:

### Independent Issues (can run in parallel)
- Issue 1: Add logging utility module
- Issue 2: Add configuration loader
- Issue 3: Add basic data models

### Dependent Issues (must wait for dependencies)
- Issue 4: Add API client (depends on 1, 2)
- Issue 5: Add data validation (depends on 3)
- Issue 6: Add caching layer (depends on 2, 3)

### Complex Dependencies
- Issue 7: Add business logic layer (depends on 4, 5, 6)
- Issue 8: Add CLI interface (depends on 7)
- Issue 9: Add test suite (depends on all above)

### Edge Cases
- Issue 10: Tiny fix (typo in README) - should be fast
- Issue 11: Large feature (full REST API) - should be slow
- Issue 12: Ambiguous issue (vague requirements) - test classification

## Phase 3: Parallel SDLC Execution (Estimated: 30-60 min)
Run ZTE on all issues, timing each phase:

### Timing Points
- T0: Issue created
- T1: Classification complete
- T2: Branch created
- T3: Worktree ready
- T4: Plan generated
- T5: Build complete
- T6: Tests run
- T7: Review complete
- T8: Documentation generated
- T9: PR merged (ZTE complete)

### Parallelization Strategy
- Wave 1: Issues 1, 2, 3, 10, 12 (independent)
- Wave 2: Issues 4, 5, 6 (after wave 1)
- Wave 3: Issue 7 (after wave 2)
- Wave 4: Issues 8, 11 (after wave 3)
- Wave 5: Issue 9 (final)

## Phase 4: Analysis
- Calculate time per phase
- Identify phases >2x expected duration
- Log any errors or failures
- Note missing MCP features encountered
- Document any bugs found

## Expected Bottlenecks
- Claude agent invocation (API latency)
- Git worktree creation (disk I/O)
- GitHub API rate limits
- Test execution time

## Success Criteria
- All 12 issues processed through ZTE
- Timing data collected for all phases
- Bottleneck report generated
- Bug/missing feature list compiled

## Output Files
- `specs/reports/260106_sdlc_timing_results.md` - Timing data
- `specs/reports/260106_sdlc_bottleneck_analysis.md` - Analysis
- `specs/reports/260106_mcp_bugs_found.md` - Bugs and missing features
