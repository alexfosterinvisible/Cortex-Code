# Feature: Comprehensive CxC Framework Test Suite

## Metadata
issue_number: `internal`
cxc_id: `test-suite`
issue_json: `{"title": "Create comprehensive test suite for CxC Framework", "body": "Build unit, integration, and regression tests for all CxC modules"}`

## Feature Description
Create a comprehensive test suite covering all CxC Framework modules with unit tests, integration tests, and regression tests. The test suite should enable confident refactoring, catch regressions early, and serve as living documentation for the framework's expected behavior.

## User Story
As a **developer maintaining the CxC Framework**
I want to **have comprehensive automated tests**
So that **I can refactor with confidence, catch regressions early, and understand expected behavior through tests**

## Problem Statement
The current CxC Framework has minimal test coverage:
- `test_agents.py` - Tests Claude Code execution with models (requires API)
- `test_model_selection.py` - Tests model mapping logic
- `test_r2_uploader.py` - Tests R2 upload (requires credentials)
- `test_webhook_simplified.py` - Basic workflow validation
- `health_check.py` - System health validation

Missing coverage:
1. **Core modules**: `config.py`, `state.py`, `data_types.py`, `utils.py` - 0% unit test coverage
2. **Integrations**: `git_ops.py`, `github.py`, `worktree_ops.py`, `workflow_ops.py` - 0% unit test coverage
3. **Workflows**: `cxc/workflows/wt/*_iso.py` (plan/build/test/review/document/ship/sdlc) - 0% integration test coverage
4. **CLI**: `cli.py` - 0% test coverage
5. **Regression tests**: No systematic regression test suite

## Solution Statement
Implement a three-tier test architecture:

### Tier 1: Unit Tests (Fast, No External Dependencies)
- Test pure functions and class methods in isolation
- Mock external dependencies (filesystem, git, GitHub API, Claude API)
- Run in < 30 seconds, suitable for pre-commit hooks

### Tier 2: Integration Tests (Medium, Mocked External Services)
- Test module interactions with mocked external services
- Test workflow orchestration logic
- Run in < 2 minutes

### Tier 3: Regression Tests (Slow, Real Services - Optional)
- End-to-end tests with real GitHub and Claude API
- Marked with `@pytest.mark.slow` and `@pytest.mark.requires_api`
- Run manually or in CI with credentials

## Relevant Files

### Core Modules to Test
- `cxc/core/config.py` - CxCConfig loading, path resolution, port config
- `cxc/core/state.py` - CxCState persistence, stdin/stdout piping
- `cxc/core/data_types.py` - Pydantic models validation
- `cxc/core/utils.py` - Utility functions (make_cxc_id, setup_logger, parse_json)
- `cxc/core/agent.py` - Claude Code execution, model selection, retry logic

### Integration Modules to Test
- `cxc/integrations/git_ops.py` - Git operations (branch, commit, push, PR)
- `cxc/integrations/github.py` - GitHub API operations (fetch issue, comment, PR)
- `cxc/integrations/worktree_ops.py` - Worktree management, port allocation
- `cxc/integrations/workflow_ops.py` - Workflow orchestration helpers

### Workflow Modules to Test
- `cxc/workflows/wt/plan_iso.py` - Planning workflow (worktree)
- `cxc/workflows/wt/build_iso.py` - Build workflow (worktree)
- `cxc/workflows/wt/test_iso.py` - Test workflow (worktree)
- `cxc/workflows/wt/review_iso.py` - Review workflow (worktree)
- `cxc/workflows/wt/document_iso.py` - Documentation workflow (worktree)
- `cxc/workflows/wt/ship_iso.py` - Ship workflow (worktree)
- `cxc/workflows/wt/sdlc_iso.py` - Full SDLC orchestration (worktree)
- `cxc/workflows/reg/*.py` - Non-worktree entrypoints (delegating)

### CLI to Test
- `cxc/cli.py` - Command routing and argument parsing

### New Files to Create
- `tests/unit/__init__.py`
- `tests/unit/test_config.py` - <R1> Config loading tests
- `tests/unit/test_state.py` - <R2> State persistence tests
- `tests/unit/test_data_types.py` - <R3> Pydantic model tests
- `tests/unit/test_utils.py` - <R4> Utility function tests
- `tests/unit/test_agent_unit.py` - <R5> Agent logic tests (mocked)
- `tests/unit/test_git_ops.py` - <R6> Git operations tests (mocked)
- `tests/unit/test_github.py` - <R7> GitHub operations tests (mocked)
- `tests/unit/test_worktree_ops.py` - <R8> Worktree tests (mocked)
- `tests/unit/test_workflow_ops.py` - <R9> Workflow helpers tests (mocked)
- `tests/unit/test_cli.py` - <R10> CLI routing tests
- `tests/integration/__init__.py`
- `tests/integration/test_workflow_plan.py` - <R11> Plan workflow integration
- `tests/integration/test_workflow_sdlc.py` - <R12> SDLC orchestration integration
- `tests/integration/test_state_persistence.py` - <R13> State file round-trip
- `tests/regression/__init__.py`
- `tests/regression/test_e2e_plan.py` - <R14> E2E plan with real APIs
- `tests/conftest.py` - Shared fixtures
- `pytest.ini` - Pytest configuration

## Implementation Plan

### Phase 1: Test Infrastructure Setup
Set up pytest configuration, fixtures, and directory structure for the three-tier test architecture.

### Phase 2: Unit Tests (Core Modules)
Implement unit tests for all core modules with 100% function coverage goal.

### Phase 3: Unit Tests (Integration Modules)
Implement unit tests for git, GitHub, and worktree operations with mocked subprocesses.

### Phase 4: Integration Tests
Implement integration tests for workflow orchestration with mocked external services.

### Phase 5: Regression Tests
Implement optional E2E tests for real API validation.

## Step by Step Tasks

### Step 1: Create Test Infrastructure

Create pytest configuration and directory structure:

- Create `pytest.ini` with markers for `slow`, `requires_api`, `unit`, `integration`
- Create `tests/conftest.py` with shared fixtures:
  - `tmp_project_dir` - Temporary directory mimicking project structure
  - `mock_cxc_config` - CxCConfig with temp paths
  - `mock_cxc_state` - CxCState with test CxC ID
  - `mock_subprocess` - Patched subprocess.run for git/gh commands
  - `mock_claude_response` - Mocked Claude Code responses
- Create `tests/unit/__init__.py`, `tests/integration/__init__.py`, `tests/regression/__init__.py`

### Step 2: Unit Tests for `config.py` <R1>

Test CxCConfig class:
- `test_load_from_yaml` - Config loads correctly from .cxc.yaml
- `test_load_missing_yaml_uses_defaults` - Graceful fallback to defaults
- `test_project_root_discovery` - Walks up directory tree to find .cxc.yaml
- `test_artifacts_dir_resolution` - Relative paths resolved to absolute
- `test_command_paths_expansion` - ${CxC_FRAMEWORK} expansion works
- `test_port_config_defaults` - Default port ranges are correct
- `test_get_project_artifacts_dir` - Returns correct path structure
- `test_get_agents_dir` - Returns correct agent directory path
- `test_get_trees_dir` - Returns correct worktree base path

### Step 3: Unit Tests for `state.py` <R2>

Test CxCState class:
- `test_init_requires_cxc_id` - ValueError if cxc_id is empty
- `test_update_filters_core_fields` - Only core fields are persisted
- `test_get_returns_default` - Default value returned for missing keys
- `test_append_cxc_id_deduplicates` - all_cxcs list has no duplicates
- `test_get_working_directory_prefers_worktree` - Returns worktree_path if set
- `test_get_state_path_uses_config` - Path matches config structure
- `test_save_creates_directory` - Parent directories created
- `test_save_validates_with_pydantic` - CxCStateData validation runs
- `test_load_returns_none_if_missing` - None returned for nonexistent state
- `test_load_parses_valid_json` - Valid JSON parsed correctly
- `test_from_stdin_returns_none_for_tty` - Returns None when stdin is tty
- `test_to_stdout_outputs_json` - JSON output is valid and complete

### Step 4: Unit Tests for `data_types.py` <R3>

Test Pydantic models:
- `test_github_issue_parses_json` - GitHubIssue parses API response
- `test_github_issue_alias_mapping` - createdAt -> created_at works
- `test_agent_prompt_request_defaults` - Default values are correct
- `test_agent_prompt_response_retry_code` - RetryCode enum works
- `test_agent_template_request_slash_command` - SlashCommand literal validation
- `test_cxc_state_data_optional_fields` - Optional fields can be None
- `test_review_result_screenshots_list` - List fields work correctly
- `test_cxc_extraction_result_has_workflow` - Property returns correct boolean

### Step 5: Unit Tests for `utils.py` <R4>

Test utility functions:
- `test_make_cxc_id_length` - Returns 8-character string
- `test_make_cxc_id_uniqueness` - Multiple calls return different IDs
- `test_make_cxc_id_alphanumeric` - Only alphanumeric characters
- `test_setup_logger_creates_logger` - Returns configured logger
- `test_setup_logger_file_handler` - Writes to correct log file
- `test_check_env_vars_logs_missing` - Logs warning for missing vars
- `test_parse_json_handles_markdown` - Extracts JSON from markdown code blocks
- `test_parse_json_validates_type` - Raises ValueError for wrong type
- `test_get_safe_subprocess_env` - Returns filtered environment

### Step 6: Unit Tests for `agent.py` <R5>

Test agent module (with mocked subprocess):
- `test_get_model_for_slash_command_base` - Returns sonnet for base model_set
- `test_get_model_for_slash_command_heavy` - Returns opus for heavy commands
- `test_get_model_for_slash_command_default` - Returns default for unknown
- `test_truncate_output_short_string` - Short strings unchanged
- `test_truncate_output_long_string` - Long strings truncated with suffix
- `test_truncate_output_jsonl` - JSONL output handled specially
- `test_check_claude_installed_success` - Returns None when installed
- `test_check_claude_installed_missing` - Returns error message when missing
- `test_parse_jsonl_output_extracts_result` - Result message found
- `test_parse_jsonl_output_empty_file` - Returns empty list for empty file
- `test_convert_jsonl_to_json` - Creates valid JSON array file
- `test_save_prompt_creates_file` - Prompt saved to correct location
- `test_prompt_claude_code_success` - Successful execution returns response
- `test_prompt_claude_code_error` - Error handling works correctly
- `test_prompt_claude_code_with_retry` - Retry logic executes correctly
- `test_execute_template_builds_prompt` - Prompt constructed correctly

### Step 7: Unit Tests for `git_ops.py` <R6>

Test git operations (with mocked subprocess):
- `test_get_current_branch` - Returns branch name
- `test_push_branch_success` - Returns (True, None) on success
- `test_push_branch_failure` - Returns (False, error) on failure
- `test_create_branch_new` - Creates new branch
- `test_create_branch_exists` - Checks out existing branch
- `test_commit_changes_no_changes` - Returns success with no changes
- `test_commit_changes_with_changes` - Stages and commits
- `test_get_pr_number_exists` - Returns PR number when exists
- `test_get_pr_number_missing` - Returns None when no PR
- `test_approve_pr_success` - Approval command succeeds
- `test_merge_pr_not_mergeable` - Returns error for unmergeable PR
- `test_merge_pr_success` - Merge command succeeds
- `test_update_pr_body` - PR body updated correctly

### Step 8: Unit Tests for `github.py` <R7>

Test GitHub operations (with mocked subprocess):
- `test_get_github_env_with_pat` - Returns env dict with GH_TOKEN
- `test_get_github_env_without_pat` - Returns None when no PAT
- `test_get_repo_url_success` - Returns remote URL
- `test_get_repo_url_no_remote` - Raises ValueError
- `test_extract_repo_path_https` - Extracts owner/repo from HTTPS URL
- `test_extract_repo_path_git_suffix` - Handles .git suffix
- `test_fetch_issue_success` - Returns GitHubIssue model
- `test_fetch_issue_not_found` - Handles missing issue
- `test_make_issue_comment_adds_bot_identifier` - Prepends CxC_BOT_IDENTIFIER
- `test_mark_issue_in_progress_adds_label` - Adds in_progress label
- `test_fetch_open_issues_returns_list` - Returns list of issues
- `test_find_keyword_from_comment` - Finds keyword in comments
- `test_find_keyword_skips_bot_comments` - Ignores CxC bot comments
- `test_approve_pr` - PR approval works
- `test_close_issue` - Issue closing works

### Step 9: Unit Tests for `worktree_ops.py` <R8>

Test worktree operations (with mocked subprocess/filesystem):
- `test_get_default_branch_main` - Detects main as default
- `test_get_default_branch_master` - Falls back to master
- `test_create_worktree_new` - Creates new worktree
- `test_create_worktree_exists` - Returns existing worktree path
- `test_create_worktree_branch_exists` - Handles existing branch
- `test_validate_worktree_valid` - Returns (True, None) for valid
- `test_validate_worktree_no_path` - Returns error for missing path
- `test_validate_worktree_no_directory` - Returns error for missing dir
- `test_get_worktree_path` - Returns correct absolute path
- `test_remove_worktree_success` - Removes worktree
- `test_setup_worktree_environment` - Creates .ports.env file
- `test_get_ports_for_cxc_deterministic` - Same ID returns same ports
- `test_get_ports_for_cxc_range` - Ports in 9100-9114 / 9200-9214 range
- `test_is_port_available_free` - Returns True for free port
- `test_is_port_available_bound` - Returns False for bound port
- `test_find_next_available_ports` - Finds available ports

### Step 10: Unit Tests for `workflow_ops.py` <R9>

Test workflow operations (with mocked agent execution):
- `test_format_issue_message` - Formats message with CxC ID
- `test_extract_cxc_info` - Extracts workflow command from text
- `test_classify_issue_feature` - Returns /feature for feature issues
- `test_classify_issue_bug` - Returns /bug for bug issues
- `test_classify_issue_chore` - Returns /chore for chore issues
- `test_build_plan_success` - Returns plan response
- `test_implement_plan_success` - Returns implement response
- `test_generate_branch_name` - Generates valid branch name
- `test_create_commit` - Creates commit message
- `test_ensure_cxc_id_new` - Creates new CxC ID
- `test_ensure_cxc_id_existing` - Returns existing CxC ID
- `test_find_existing_branch_for_issue` - Finds matching branch
- `test_find_plan_for_issue` - Finds plan file
- `test_find_spec_file` - Finds spec file from state or git diff
- `test_create_and_implement_patch` - Creates and implements patch
- `test_build_comprehensive_pr_body` - Builds complete PR body

### Step 11: Unit Tests for `cli.py` <R10>

Test CLI routing:
- `test_cli_help` - --help shows usage
- `test_cli_plan_command` - plan command routes correctly
- `test_cli_build_command` - build command routes correctly
- `test_cli_test_command` - test command routes correctly
- `test_cli_review_command` - review command routes correctly
- `test_cli_document_command` - document command routes correctly
- `test_cli_ship_command` - ship command routes correctly
- `test_cli_sdlc_command` - sdlc command routes correctly
- `test_cli_zte_command` - zte command routes correctly
- `test_cli_monitor_command` - monitor command routes correctly
- `test_cli_webhook_command` - webhook command routes correctly
- `test_cli_skip_e2e_flag` - --skip-e2e flag passed correctly
- `test_cli_skip_resolution_flag` - --skip-resolution flag passed correctly

### Step 12: Integration Test for State Persistence <R13>

Test state round-trip:
- `test_state_save_load_roundtrip` - Save then load returns same data
- `test_state_multiple_updates` - Multiple updates accumulate correctly
- `test_state_across_workflows` - State persists across workflow phases
- `test_state_stdin_stdout_pipe` - Piping state between processes works

### Step 13: Integration Test for Plan Workflow <R11>

Test plan workflow orchestration (with mocked external services):
- `test_plan_workflow_happy_path` - Full plan workflow succeeds
- `test_plan_workflow_creates_worktree` - Worktree created correctly
- `test_plan_workflow_classifies_issue` - Issue classified correctly
- `test_plan_workflow_generates_branch` - Branch name generated
- `test_plan_workflow_creates_plan_file` - Plan file created in specs/
- `test_plan_workflow_commits_plan` - Plan committed to branch
- `test_plan_workflow_pushes_and_creates_pr` - PR created

### Step 14: Integration Test for SDLC Workflow <R12>

Test SDLC orchestration (with mocked workflows):
- `test_sdlc_runs_all_phases` - All phases executed in order
- `test_sdlc_stops_on_plan_failure` - Stops if plan fails
- `test_sdlc_continues_on_test_failure` - Continues with warning on test failure
- `test_sdlc_stops_on_review_failure` - Stops if review fails
- `test_sdlc_passes_cxc_id_to_phases` - CxC ID passed correctly

### Step 15: Regression Tests (Optional E2E) <R14>

Create E2E tests that require real APIs:
- `test_e2e_plan_real_issue` - Plan workflow with real GitHub issue
- `test_e2e_classify_real_issue` - Issue classification with real Claude
- Mark with `@pytest.mark.slow` and `@pytest.mark.requires_api`
- Skip by default, run with `pytest -m requires_api`

### Step 16: Run Validation Commands

Execute validation to ensure all tests pass:

```bash
# Run all unit tests (fast, no API required)
uv run pytest tests/unit/ -v

# Run integration tests
uv run pytest tests/integration/ -v

# Run all tests except slow/API-dependent
uv run pytest -v -m "not slow and not requires_api"

# Check coverage
uv run pytest --cov=cxc --cov-report=term-missing tests/unit/
```

## Testing Strategy

### Unit Tests
- Test each function/method in isolation
- Mock all external dependencies (subprocess, filesystem, network)
- Use pytest fixtures for common setup
- Aim for 100% function coverage on core modules

### Integration Tests
- Test module interactions with mocked external services
- Use temporary directories for filesystem tests
- Mock subprocess for git/gh commands
- Mock Claude API responses

### Edge Cases
- Empty/None inputs
- Missing configuration files
- Invalid JSON responses
- Network timeouts
- Permission errors
- Concurrent access to state files
- Port conflicts
- Git merge conflicts

## Acceptance Criteria
- [ ] All unit tests pass with 0 failures
- [ ] Unit test coverage > 80% for core modules
- [ ] Integration tests validate workflow orchestration
- [ ] Tests run in < 2 minutes total (excluding slow tests)
- [ ] No external API calls in unit/integration tests
- [ ] Clear test documentation via docstrings
- [ ] Fixtures are reusable and well-documented

## Validation Commands

```bash
# Install test dependencies
uv add --dev pytest pytest-cov pytest-mock

# Run unit tests
uv run pytest tests/unit/ -v --tb=short

# Run integration tests  
uv run pytest tests/integration/ -v --tb=short

# Run all tests with coverage
uv run pytest --cov=cxc --cov-report=term-missing --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_config.py -v

# Run tests matching pattern
uv run pytest -k "test_state" -v

# Run only fast tests (default)
uv run pytest -m "not slow" -v
```

## Notes

### Test Isolation
- Each test should be independent and not rely on test execution order
- Use `tmp_path` fixture for filesystem tests
- Clean up any created resources in teardown

### Mocking Strategy
- Use `unittest.mock.patch` for subprocess calls
- Use `pytest-mock` for cleaner mock syntax
- Create reusable mock fixtures in conftest.py

### CI Integration
- Unit tests should run on every PR
- Integration tests should run on every PR
- Regression tests (requires_api) should run nightly or manually

### Future Enhancements
- Property-based testing with Hypothesis for data types
- Mutation testing to verify test quality
- Performance benchmarks for critical paths
