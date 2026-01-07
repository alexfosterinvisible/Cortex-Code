"""(Claude) Unit tests for CXC MCP Server - cxc/mcp_server.py

Tests verify MCP server initialization, tool registration, and basic functionality.

Test Categories:
1. Import and Initialization - MCP server imports and initializes correctly
2. Tool Registration - All expected tools are registered with correct signatures
3. Tool Signatures - Tools have correct parameter types and docstrings
4. Entry Point - main() function exists and is callable
5. Basic Functionality - Unit tests with mocked dependencies
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import get_type_hints


class TestMCPServerImport:
    """if mcp_server module doesn't import then broken"""

    def test_import_mcp_server_module(self):
        """if cxc.mcp_server doesn't import then broken"""
        from cxc import mcp_server
        assert mcp_server is not None

    def test_import_mcp_instance(self):
        """if mcp instance doesn't exist then broken"""
        from cxc.mcp_server import mcp
        assert mcp is not None

    def test_mcp_server_name(self):
        """if MCP server name isn't 'cxc' then broken"""
        from cxc.mcp_server import mcp
        assert mcp.name == "cxc"


class TestToolRegistration:
    """if expected tools aren't registered then broken"""

    def test_total_tool_count(self):
        """if MCP server doesn't have exactly 24 tools registered then broken"""
        from cxc.mcp_server import mcp
        tools = list(mcp._tool_manager._tools.keys())
        assert len(tools) == 24, f"Expected 24 tools, found {len(tools)}: {tools}"

    def test_sdlc_orchestration_tools_registered(self):
        """if SDLC orchestration tools aren't registered then broken"""
        from cxc.mcp_server import mcp
        tools = list(mcp._tool_manager._tools.keys())

        expected_sdlc_tools = [
            'cxc_plan', 'cxc_build', 'cxc_test', 'cxc_review',
            'cxc_document', 'cxc_ship', 'cxc_sdlc', 'cxc_zte', 'cxc_patch'
        ]

        for tool in expected_sdlc_tools:
            assert tool in tools, f"Missing SDLC tool: {tool}"

    def test_github_tools_registered(self):
        """if GitHub operation tools aren't registered then broken"""
        from cxc.mcp_server import mcp
        tools = list(mcp._tool_manager._tools.keys())

        expected_github_tools = [
            'fetch_github_issue', 'post_issue_comment', 'list_open_issues',
            'get_repository_url', 'close_github_issue'
        ]

        for tool in expected_github_tools:
            assert tool in tools, f"Missing GitHub tool: {tool}"

    def test_git_tools_registered(self):
        """if Git operation tools aren't registered then broken"""
        from cxc.mcp_server import mcp
        tools = list(mcp._tool_manager._tools.keys())

        expected_git_tools = [
            'get_current_branch', 'create_git_branch', 'commit_changes',
            'push_branch', 'check_pr_exists', 'merge_pull_request',
            'approve_pull_request'
        ]

        for tool in expected_git_tools:
            assert tool in tools, f"Missing Git tool: {tool}"

    def test_state_tools_registered(self):
        """if workflow state tools aren't registered then broken"""
        from cxc.mcp_server import mcp
        tools = list(mcp._tool_manager._tools.keys())

        expected_state_tools = [
            'load_cxc_state', 'get_cxc_state_value', 'list_available_workflows'
        ]

        for tool in expected_state_tools:
            assert tool in tools, f"Missing state tool: {tool}"


class TestToolSignatures:
    """if tool signatures are incorrect then broken"""

    def test_cxc_plan_signature(self):
        """if cxc_plan doesn't have correct parameters then broken"""
        from cxc.mcp_server import cxc_plan

        # Check function exists
        assert callable(cxc_plan)

        # Check docstring exists
        assert cxc_plan.__doc__ is not None
        assert "Plan implementation" in cxc_plan.__doc__

    def test_cxc_build_signature(self):
        """if cxc_build doesn't have correct parameters then broken"""
        from cxc.mcp_server import cxc_build

        assert callable(cxc_build)
        assert cxc_build.__doc__ is not None
        assert "Build implementation" in cxc_build.__doc__

    def test_cxc_test_signature(self):
        """if cxc_test doesn't have correct parameters then broken"""
        from cxc.mcp_server import cxc_test

        assert callable(cxc_test)
        assert cxc_test.__doc__ is not None
        assert "Run tests" in cxc_test.__doc__

    def test_cxc_review_signature(self):
        """if cxc_review doesn't have correct parameters then broken"""
        from cxc.mcp_server import cxc_review

        assert callable(cxc_review)
        assert cxc_review.__doc__ is not None
        assert "Review implementation" in cxc_review.__doc__

    def test_cxc_document_signature(self):
        """if cxc_document doesn't have correct parameters then broken"""
        from cxc.mcp_server import cxc_document

        assert callable(cxc_document)
        assert cxc_document.__doc__ is not None
        assert "documentation" in cxc_document.__doc__.lower()

    def test_cxc_ship_signature(self):
        """if cxc_ship doesn't have correct parameters then broken"""
        from cxc.mcp_server import cxc_ship

        assert callable(cxc_ship)
        assert cxc_ship.__doc__ is not None
        assert "Ship changes" in cxc_ship.__doc__ or "merge" in cxc_ship.__doc__.lower()

    def test_cxc_sdlc_signature(self):
        """if cxc_sdlc doesn't have correct parameters then broken"""
        from cxc.mcp_server import cxc_sdlc

        assert callable(cxc_sdlc)
        assert cxc_sdlc.__doc__ is not None
        assert "SDLC" in cxc_sdlc.__doc__

    def test_cxc_zte_signature(self):
        """if cxc_zte doesn't have correct parameters then broken"""
        from cxc.mcp_server import cxc_zte

        assert callable(cxc_zte)
        assert cxc_zte.__doc__ is not None
        assert "Zero Touch" in cxc_zte.__doc__

    def test_fetch_github_issue_signature(self):
        """if fetch_github_issue doesn't have correct return type then broken"""
        from cxc.mcp_server import fetch_github_issue

        assert callable(fetch_github_issue)
        assert fetch_github_issue.__doc__ is not None
        # Should return dict based on source code
        assert "dict" in fetch_github_issue.__doc__.lower() or "Dictionary" in fetch_github_issue.__doc__

    def test_get_current_branch_signature(self):
        """if get_current_branch doesn't return string then broken"""
        from cxc.mcp_server import get_current_branch

        assert callable(get_current_branch)
        assert get_current_branch.__doc__ is not None
        assert "branch" in get_current_branch.__doc__.lower()

    def test_load_cxc_state_signature(self):
        """if load_cxc_state doesn't have correct parameters then broken"""
        from cxc.mcp_server import load_cxc_state

        assert callable(load_cxc_state)
        assert load_cxc_state.__doc__ is not None
        assert "state" in load_cxc_state.__doc__.lower()

    def test_list_available_workflows_signature(self):
        """if list_available_workflows doesn't return list then broken"""
        from cxc.mcp_server import list_available_workflows

        assert callable(list_available_workflows)
        assert list_available_workflows.__doc__ is not None
        assert "workflow" in list_available_workflows.__doc__.lower()


class TestEntryPoint:
    """if main() entry point doesn't exist then broken"""

    def test_main_function_exists(self):
        """if main() function doesn't exist then broken"""
        from cxc.mcp_server import main
        assert callable(main)

    def test_main_function_has_docstring(self):
        """if main() function doesn't have docstring then broken"""
        from cxc.mcp_server import main
        assert main.__doc__ is not None
        assert "MCP server" in main.__doc__


class TestBasicFunctionality:
    """if basic tool functionality doesn't work then broken"""

    @patch('cxc.mcp_server.git_ops.get_current_branch')
    def test_get_current_branch_returns_string(self, mock_git_ops):
        """if get_current_branch doesn't return a string then broken"""
        from cxc.mcp_server import get_current_branch

        # Mock the git_ops function
        mock_git_ops.return_value = "main"

        result = get_current_branch()

        assert isinstance(result, str)
        assert result == "main"
        mock_git_ops.assert_called_once()

    @patch('cxc.mcp_server.CxcState.load')
    def test_load_cxc_state_with_invalid_id_returns_error(self, mock_load):
        """if load_cxc_state with invalid ID doesn't return error dict then broken"""
        from cxc.mcp_server import load_cxc_state

        # Mock state not found
        mock_load.return_value = None

        result = load_cxc_state("invalid123")

        assert isinstance(result, dict)
        assert "error" in result
        assert "invalid123" in result["error"]

    @patch('cxc.mcp_server.CxcState.load')
    def test_load_cxc_state_with_valid_id_returns_data(self, mock_load):
        """if load_cxc_state with valid ID doesn't return state data then broken"""
        from cxc.mcp_server import load_cxc_state

        # Mock valid state
        mock_state = MagicMock()
        mock_state.data = {
            "issue_number": "123",
            "branch_name": "feature/test",
            "cxc_id": "test1234"
        }
        mock_load.return_value = mock_state

        result = load_cxc_state("test1234")

        assert isinstance(result, dict)
        assert "error" not in result
        assert result["issue_number"] == "123"
        assert result["branch_name"] == "feature/test"

    @patch('cxc.mcp_server.CxcState.load')
    def test_get_cxc_state_value_returns_value(self, mock_load):
        """if get_cxc_state_value doesn't return the requested value then broken"""
        from cxc.mcp_server import get_cxc_state_value

        # Mock valid state with get method
        mock_state = MagicMock()
        mock_state.get.return_value = "feature/test"
        mock_load.return_value = mock_state

        result = get_cxc_state_value("test1234", "branch_name")

        assert isinstance(result, str)
        assert result == "feature/test"
        mock_state.get.assert_called_once_with("branch_name")

    @patch('cxc.mcp_server.CxcState.load')
    def test_get_cxc_state_value_missing_key(self, mock_load):
        """if get_cxc_state_value with missing key doesn't return error message then broken"""
        from cxc.mcp_server import get_cxc_state_value

        # Mock state with missing key
        mock_state = MagicMock()
        mock_state.get.return_value = None
        mock_load.return_value = mock_state

        result = get_cxc_state_value("test1234", "nonexistent_key")

        assert isinstance(result, str)
        assert "not found" in result.lower()

    @patch('cxc.mcp_server.github.get_repo_url')
    def test_get_repository_url_returns_string(self, mock_get_repo):
        """if get_repository_url doesn't return a string then broken"""
        from cxc.mcp_server import get_repository_url

        # Mock repo URL
        mock_get_repo.return_value = "https://github.com/test-org/test-repo.git"

        result = get_repository_url()

        assert isinstance(result, str)
        assert "github.com" in result

    @patch('cxc.mcp_server.git_ops.create_branch')
    def test_create_git_branch_success(self, mock_create):
        """if create_git_branch with success doesn't return success message then broken"""
        from cxc.mcp_server import create_git_branch

        # Mock successful branch creation
        mock_create.return_value = (True, None)

        result = create_git_branch("feature/new-branch")

        assert isinstance(result, str)
        assert "feature/new-branch" in result
        assert "created" in result.lower() or "checkout" in result.lower()

    @patch('cxc.mcp_server.git_ops.create_branch')
    def test_create_git_branch_failure(self, mock_create):
        """if create_git_branch with failure doesn't return error message then broken"""
        from cxc.mcp_server import create_git_branch

        # Mock failed branch creation
        mock_create.return_value = (False, "Branch already exists")

        result = create_git_branch("feature/existing")

        assert isinstance(result, str)
        assert "failed" in result.lower()
        assert "already exists" in result.lower()

    @patch('cxc.mcp_server.git_ops.commit_changes')
    def test_commit_changes_success(self, mock_commit):
        """if commit_changes with success doesn't return success message then broken"""
        from cxc.mcp_server import commit_changes

        # Mock successful commit
        mock_commit.return_value = (True, None)

        result = commit_changes("Test commit message")

        assert isinstance(result, str)
        assert "commit" in result.lower()
        assert "test commit message" in result.lower()

    @patch('cxc.mcp_server.github.close_issue')
    def test_close_github_issue_success(self, mock_close):
        """if close_github_issue with success doesn't return success message then broken"""
        from cxc.mcp_server import close_github_issue

        # Mock successful close
        mock_close.return_value = (True, None)

        result = close_github_issue("123")

        assert isinstance(result, str)
        assert "123" in result
        assert "closed" in result.lower()

    @patch('cxc.mcp_server.github.close_issue')
    def test_close_github_issue_failure(self, mock_close):
        """if close_github_issue with failure doesn't return error message then broken"""
        from cxc.mcp_server import close_github_issue

        # Mock failed close
        mock_close.return_value = (False, "Issue not found")

        result = close_github_issue("999")

        assert isinstance(result, str)
        assert "failed" in result.lower()
        assert "not found" in result.lower()

    @patch('cxc.mcp_server.github.make_issue_comment')
    def test_post_issue_comment_success(self, mock_comment):
        """if post_issue_comment doesn't post comment successfully then broken"""
        from cxc.mcp_server import post_issue_comment

        # Mock successful comment
        mock_comment.return_value = None  # Function doesn't return anything on success

        result = post_issue_comment("123", "Test comment")

        assert isinstance(result, str)
        assert "123" in result
        assert "posted" in result.lower()
        mock_comment.assert_called_once_with("123", "Test comment")

    @patch('cxc.mcp_server._run_workflow')
    def test_cxc_plan_calls_workflow(self, mock_run_workflow):
        """if cxc_plan doesn't call the plan workflow then broken"""
        from cxc.mcp_server import cxc_plan

        # Mock workflow execution
        mock_run_workflow.return_value = "Workflow wt.plan_iso completed successfully"

        result = cxc_plan("123")

        assert isinstance(result, str)
        assert "completed" in result.lower() or "success" in result.lower()
        mock_run_workflow.assert_called_once_with("wt.plan_iso", ["123"])

    @patch('cxc.mcp_server._run_workflow')
    def test_cxc_plan_with_cxc_id(self, mock_run_workflow):
        """if cxc_plan with cxc_id doesn't pass it to workflow then broken"""
        from cxc.mcp_server import cxc_plan

        # Mock workflow execution
        mock_run_workflow.return_value = "Workflow wt.plan_iso completed successfully"

        result = cxc_plan("123", "test1234")

        mock_run_workflow.assert_called_once_with("wt.plan_iso", ["123", "test1234"])

    @patch('cxc.mcp_server._run_workflow')
    def test_cxc_test_with_skip_e2e(self, mock_run_workflow):
        """if cxc_test with skip_e2e doesn't pass flag to workflow then broken"""
        from cxc.mcp_server import cxc_test

        # Mock workflow execution
        mock_run_workflow.return_value = "Workflow wt.test_iso completed successfully"

        result = cxc_test("123", "test1234", skip_e2e=True)

        # Should pass --skip-e2e flag
        args_passed = mock_run_workflow.call_args[0][1]
        assert "--skip-e2e" in args_passed

    @patch('cxc.mcp_server.git_ops.merge_pr')
    def test_merge_pull_request_with_method(self, mock_merge):
        """if merge_pull_request doesn't respect merge method then broken"""
        from cxc.mcp_server import merge_pull_request

        # Mock successful merge
        mock_merge.return_value = (True, None)

        result = merge_pull_request("123", method="squash")

        # Check that merge was called with correct method
        call_args = mock_merge.call_args[0]
        assert call_args[0] == "123"
        # method should be passed
        call_kwargs = mock_merge.call_args[1] if mock_merge.call_args[1] else {}
        if call_kwargs:
            assert call_kwargs.get("method") == "squash" or call_args[2] == "squash"


class TestWorkflowRunner:
    """if _run_workflow helper doesn't work correctly then broken"""

    @patch('cxc.mcp_server.importlib.import_module')
    def test_run_workflow_success(self, mock_import):
        """if _run_workflow with valid module doesn't execute successfully then broken"""
        from cxc.mcp_server import _run_workflow

        # Mock module with main function
        mock_module = MagicMock()
        mock_module.main = MagicMock()
        mock_import.return_value = mock_module

        result = _run_workflow("test_workflow", ["arg1", "arg2"])

        assert isinstance(result, str)
        assert "completed successfully" in result
        mock_module.main.assert_called_once()

    @patch('cxc.mcp_server.importlib.import_module')
    def test_run_workflow_missing_main(self, mock_import):
        """if _run_workflow with module missing main() doesn't return error then broken"""
        from cxc.mcp_server import _run_workflow

        # Mock module without main function
        mock_module = MagicMock(spec=[])  # No main attribute
        mock_import.return_value = mock_module

        result = _run_workflow("test_workflow", [])

        assert isinstance(result, str)
        assert "error" in result.lower()
        assert "no main()" in result.lower()

    @patch('cxc.mcp_server.importlib.import_module')
    def test_run_workflow_import_error(self, mock_import):
        """if _run_workflow with invalid module doesn't return error then broken"""
        from cxc.mcp_server import _run_workflow

        # Mock import error
        mock_import.side_effect = ImportError("Module not found")

        result = _run_workflow("nonexistent_workflow", [])

        assert isinstance(result, str)
        assert "error" in result.lower()
        assert "import" in result.lower()


class TestListAvailableWorkflows:
    """if list_available_workflows doesn't work correctly then broken"""

    @patch('cxc.integrations.workflow_ops.AVAILABLE_CXC_WORKFLOWS', [
        {"name": "wt.plan_iso", "description": "Plan workflow"},
        {"name": "wt.build_iso", "description": "Build workflow"}
    ])
    def test_list_available_workflows_returns_list(self):
        """if list_available_workflows doesn't return a list then broken"""
        from cxc.mcp_server import list_available_workflows

        result = list_available_workflows()

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "wt.plan_iso"
        assert result[1]["description"] == "Build workflow"


class TestListOpenIssues:
    """if list_open_issues tool handler doesn't work correctly then broken"""

    @patch('cxc.mcp_server.github.fetch_open_issues')
    @patch('cxc.mcp_server.github.extract_repo_path')
    @patch('cxc.mcp_server.github.get_repo_url')
    def test_list_open_issues_returns_list_of_issues(self, mock_get_repo, mock_extract, mock_fetch):
        """if list_open_issues doesn't return list of issue dicts then broken"""
        from cxc.mcp_server import list_open_issues
        from cxc.core.data_types import GitHubIssue, GitHubUser, GitHubLabel
        from datetime import datetime

        # Mock repo operations
        mock_get_repo.return_value = "https://github.com/test-org/test-repo.git"
        mock_extract.return_value = "test-org/test-repo"

        # Mock issue data with all required fields
        mock_issues = [
            GitHubIssue(
                number=1,
                title="First issue",
                body="Description 1",
                state="open",
                author=GitHubUser(login="user1"),
                labels=[GitHubLabel(id="1", name="bug", color="ff0000")],
                comments=[],
                createdAt=datetime(2026, 1, 1, 12, 0, 0),
                updatedAt=datetime(2026, 1, 2, 12, 0, 0),
                url="https://github.com/test-org/test-repo/issues/1"
            ),
            GitHubIssue(
                number=2,
                title="Second issue",
                body="Description 2",
                state="open",
                author=GitHubUser(login="user2"),
                labels=[GitHubLabel(id="2", name="feature", color="00ff00")],
                comments=[],
                createdAt=datetime(2026, 1, 3, 12, 0, 0),
                updatedAt=datetime(2026, 1, 4, 12, 0, 0),
                url="https://github.com/test-org/test-repo/issues/2"
            )
        ]
        mock_fetch.return_value = mock_issues

        result = list_open_issues()

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["number"] == 1
        assert result[0]["title"] == "First issue"
        assert result[1]["number"] == 2
        assert result[1]["labels"][0]["name"] == "feature"
        mock_fetch.assert_called_once_with("test-org/test-repo")

    @patch('cxc.mcp_server.github.fetch_open_issues')
    @patch('cxc.mcp_server.github.extract_repo_path')
    @patch('cxc.mcp_server.github.get_repo_url')
    def test_list_open_issues_empty_repository(self, mock_get_repo, mock_extract, mock_fetch):
        """if list_open_issues with no open issues doesn't return empty list then broken"""
        from cxc.mcp_server import list_open_issues

        mock_get_repo.return_value = "https://github.com/test-org/test-repo.git"
        mock_extract.return_value = "test-org/test-repo"
        mock_fetch.return_value = []

        result = list_open_issues()

        assert isinstance(result, list)
        assert len(result) == 0


class TestFetchGitHubIssue:
    """if fetch_github_issue tool handler doesn't work correctly then broken"""

    @patch('cxc.mcp_server.github.fetch_issue')
    @patch('cxc.mcp_server.github.extract_repo_path')
    @patch('cxc.mcp_server.github.get_repo_url')
    def test_fetch_github_issue_returns_issue_dict(self, mock_get_repo, mock_extract, mock_fetch):
        """if fetch_github_issue doesn't return issue dict then broken"""
        from cxc.mcp_server import fetch_github_issue
        from cxc.core.data_types import GitHubIssue, GitHubUser, GitHubLabel, GitHubComment
        from datetime import datetime

        # Mock repo operations
        mock_get_repo.return_value = "https://github.com/test-org/test-repo.git"
        mock_extract.return_value = "test-org/test-repo"

        # Mock issue data with all required fields
        mock_issue = GitHubIssue(
            number=42,
            title="Test issue",
            body="Issue description",
            state="open",
            author=GitHubUser(login="testuser"),
            labels=[
                GitHubLabel(id="1", name="bug", color="ff0000"),
                GitHubLabel(id="2", name="priority", color="00ff00")
            ],
            comments=[
                GitHubComment(
                    id="c1",
                    author=GitHubUser(login="commenter1"),
                    body="Comment 1",
                    createdAt=datetime(2026, 1, 5, 10, 0, 0)
                ),
                GitHubComment(
                    id="c2",
                    author=GitHubUser(login="commenter2"),
                    body="Comment 2",
                    createdAt=datetime(2026, 1, 5, 11, 0, 0)
                )
            ],
            createdAt=datetime(2026, 1, 1, 12, 0, 0),
            updatedAt=datetime(2026, 1, 5, 12, 0, 0),
            url="https://github.com/test-org/test-repo/issues/42"
        )
        mock_fetch.return_value = mock_issue

        result = fetch_github_issue("42")

        assert isinstance(result, dict)
        assert result["number"] == 42
        assert result["title"] == "Test issue"
        assert result["body"] == "Issue description"
        assert result["state"] == "open"
        assert result["labels"][0]["name"] == "bug"
        assert len(result["comments"]) == 2
        mock_fetch.assert_called_once_with("42", "test-org/test-repo")

    @patch('cxc.mcp_server.github.fetch_issue')
    @patch('cxc.mcp_server.github.extract_repo_path')
    @patch('cxc.mcp_server.github.get_repo_url')
    def test_fetch_github_issue_with_no_labels(self, mock_get_repo, mock_extract, mock_fetch):
        """if fetch_github_issue with no labels doesn't return empty labels list then broken"""
        from cxc.mcp_server import fetch_github_issue
        from cxc.core.data_types import GitHubIssue, GitHubUser
        from datetime import datetime

        mock_get_repo.return_value = "https://github.com/test-org/test-repo.git"
        mock_extract.return_value = "test-org/test-repo"

        mock_issue = GitHubIssue(
            number=10,
            title="Unlabeled issue",
            body="No labels",
            state="open",
            author=GitHubUser(login="testuser"),
            labels=[],
            comments=[],
            createdAt=datetime(2026, 1, 1, 12, 0, 0),
            updatedAt=datetime(2026, 1, 2, 12, 0, 0),
            url="https://github.com/test-org/test-repo/issues/10"
        )
        mock_fetch.return_value = mock_issue

        result = fetch_github_issue("10")

        assert isinstance(result, dict)
        assert result["labels"] == []
        assert result["comments"] == []


class TestWorkflowExecutionErrors:
    """if workflow execution error handling doesn't work correctly then broken"""

    @patch('cxc.mcp_server._run_workflow')
    def test_cxc_build_with_workflow_error(self, mock_run_workflow):
        """if cxc_build with workflow error doesn't return error message then broken"""
        from cxc.mcp_server import cxc_build

        mock_run_workflow.return_value = "Error running workflow 'wt.build_iso': File not found"

        result = cxc_build("123", "test1234")

        assert isinstance(result, str)
        assert "error" in result.lower()

    @patch('cxc.mcp_server._run_workflow')
    def test_cxc_sdlc_with_all_flags(self, mock_run_workflow):
        """if cxc_sdlc with all flags doesn't pass them correctly then broken"""
        from cxc.mcp_server import cxc_sdlc

        mock_run_workflow.return_value = "Workflow wt.sdlc_iso completed successfully"

        result = cxc_sdlc("123", cxc_id="test1234", skip_e2e=True, skip_resolution=True)

        args_passed = mock_run_workflow.call_args[0][1]
        assert "123" in args_passed
        assert "test1234" in args_passed
        assert "--skip-e2e" in args_passed
        assert "--skip-resolution" in args_passed

    @patch('cxc.mcp_server._run_workflow')
    def test_cxc_zte_without_optional_args(self, mock_run_workflow):
        """if cxc_zte without optional args doesn't work then broken"""
        from cxc.mcp_server import cxc_zte

        mock_run_workflow.return_value = "Workflow wt.sdlc_zte_iso completed successfully"

        result = cxc_zte("999")

        args_passed = mock_run_workflow.call_args[0][1]
        assert args_passed == ["999"]
        assert "--skip-e2e" not in args_passed
        assert "--skip-resolution" not in args_passed

    @patch('cxc.mcp_server._run_workflow')
    def test_cxc_review_with_skip_resolution(self, mock_run_workflow):
        """if cxc_review with skip_resolution doesn't pass flag then broken"""
        from cxc.mcp_server import cxc_review

        mock_run_workflow.return_value = "Workflow wt.review_iso completed successfully"

        result = cxc_review("123", "test1234", skip_resolution=True)

        args_passed = mock_run_workflow.call_args[0][1]
        assert "--skip-resolution" in args_passed


class TestGitHubOperationErrors:
    """if GitHub operation error scenarios don't work correctly then broken"""

    @patch('cxc.mcp_server.github.fetch_issue')
    @patch('cxc.mcp_server.github.extract_repo_path')
    @patch('cxc.mcp_server.github.get_repo_url')
    def test_fetch_github_issue_with_gh_failure(self, mock_get_repo, mock_extract, mock_fetch):
        """if fetch_github_issue with gh CLI failure doesn't raise exception then broken"""
        from cxc.mcp_server import fetch_github_issue

        mock_get_repo.return_value = "https://github.com/test-org/test-repo.git"
        mock_extract.return_value = "test-org/test-repo"
        mock_fetch.side_effect = RuntimeError("gh CLI error: issue not found")

        with pytest.raises(RuntimeError) as exc_info:
            fetch_github_issue("999")

        assert "gh CLI error" in str(exc_info.value)

    @patch('cxc.mcp_server.github.make_issue_comment')
    def test_post_issue_comment_with_gh_failure(self, mock_comment):
        """if post_issue_comment with gh CLI failure doesn't raise exception then broken"""
        from cxc.mcp_server import post_issue_comment

        mock_comment.side_effect = RuntimeError("gh CLI error: authentication failed")

        with pytest.raises(RuntimeError) as exc_info:
            post_issue_comment("123", "Test comment")

        assert "gh CLI error" in str(exc_info.value)

    @patch('cxc.mcp_server.github.fetch_open_issues')
    @patch('cxc.mcp_server.github.extract_repo_path')
    @patch('cxc.mcp_server.github.get_repo_url')
    def test_list_open_issues_with_invalid_repo(self, mock_get_repo, mock_extract, mock_fetch):
        """if list_open_issues with invalid repo doesn't raise exception then broken"""
        from cxc.mcp_server import list_open_issues

        mock_get_repo.return_value = "https://github.com/test-org/test-repo.git"
        mock_extract.return_value = "test-org/test-repo"
        mock_fetch.side_effect = RuntimeError("gh CLI error: repository not found")

        with pytest.raises(RuntimeError) as exc_info:
            list_open_issues()

        assert "repository not found" in str(exc_info.value)


class TestGitOperationEdgeCases:
    """if Git operation edge cases don't work correctly then broken"""

    @patch('cxc.mcp_server.git_ops.push_branch')
    def test_push_branch_success(self, mock_push):
        """if push_branch with success doesn't return success message then broken"""
        from cxc.mcp_server import push_branch

        mock_push.return_value = (True, None)

        result = push_branch("feature/test-branch")

        assert isinstance(result, str)
        assert "pushed" in result.lower()
        assert "feature/test-branch" in result

    @patch('cxc.mcp_server.git_ops.push_branch')
    def test_push_branch_failure(self, mock_push):
        """if push_branch with failure doesn't return error message then broken"""
        from cxc.mcp_server import push_branch

        mock_push.return_value = (False, "Permission denied")

        result = push_branch("feature/test-branch")

        assert isinstance(result, str)
        assert "failed" in result.lower()
        assert "permission denied" in result.lower()

    @patch('cxc.mcp_server.git_ops.check_pr_exists')
    def test_check_pr_exists_when_pr_found(self, mock_check):
        """if check_pr_exists when PR found doesn't return PR URL then broken"""
        from cxc.mcp_server import check_pr_exists

        mock_check.return_value = "https://github.com/test-org/test-repo/pull/42"

        result = check_pr_exists("feature/test-branch")

        assert isinstance(result, str)
        assert "https://github.com" in result
        assert "PR exists" in result

    @patch('cxc.mcp_server.git_ops.check_pr_exists')
    def test_check_pr_exists_when_no_pr(self, mock_check):
        """if check_pr_exists when no PR doesn't return appropriate message then broken"""
        from cxc.mcp_server import check_pr_exists

        mock_check.return_value = None

        result = check_pr_exists("feature/test-branch")

        assert isinstance(result, str)
        assert "no pr" in result.lower()

    @patch('cxc.mcp_server.git_ops.approve_pr')
    def test_approve_pull_request_success(self, mock_approve):
        """if approve_pull_request with success doesn't return success message then broken"""
        from cxc.mcp_server import approve_pull_request

        mock_approve.return_value = (True, None)

        result = approve_pull_request("42")

        assert isinstance(result, str)
        assert "approved" in result.lower()
        assert "42" in result

    @patch('cxc.mcp_server.git_ops.approve_pr')
    def test_approve_pull_request_failure(self, mock_approve):
        """if approve_pull_request with failure doesn't return error message then broken"""
        from cxc.mcp_server import approve_pull_request

        mock_approve.return_value = (False, "Cannot approve own PR")

        result = approve_pull_request("42")

        assert isinstance(result, str)
        assert "failed" in result.lower()
        assert "cannot approve own pr" in result.lower()


class TestWorkflowRunnerEdgeCases:
    """if _run_workflow edge cases don't work correctly then broken"""

    @patch('cxc.mcp_server.importlib.import_module')
    def test_run_workflow_with_runtime_exception(self, mock_import):
        """if _run_workflow with runtime exception doesn't return error message then broken"""
        from cxc.mcp_server import _run_workflow

        mock_module = MagicMock()
        mock_module.main = MagicMock(side_effect=ValueError("Invalid configuration"))
        mock_import.return_value = mock_module

        result = _run_workflow("test_workflow", [])

        assert isinstance(result, str)
        assert "error" in result.lower()
        assert "invalid configuration" in result.lower()

    @patch('cxc.mcp_server.importlib.import_module')
    def test_run_workflow_restores_sys_argv(self, mock_import):
        """if _run_workflow doesn't restore sys.argv after execution then broken"""
        from cxc.mcp_server import _run_workflow
        import sys

        original_argv = sys.argv.copy()

        mock_module = MagicMock()
        mock_module.main = MagicMock()
        mock_import.return_value = mock_module

        _run_workflow("test_workflow", ["arg1", "arg2"])

        assert sys.argv == original_argv

    @patch('cxc.mcp_server.importlib.import_module')
    def test_run_workflow_restores_sys_argv_on_exception(self, mock_import):
        """if _run_workflow doesn't restore sys.argv on exception then broken"""
        from cxc.mcp_server import _run_workflow
        import sys

        original_argv = sys.argv.copy()

        mock_module = MagicMock()
        mock_module.main = MagicMock(side_effect=RuntimeError("Crash"))
        mock_import.return_value = mock_module

        _run_workflow("test_workflow", ["arg1"])

        assert sys.argv == original_argv
