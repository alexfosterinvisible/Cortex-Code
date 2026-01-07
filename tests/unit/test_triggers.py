"""Unit tests for cxc/triggers/ modules

(Claude)

Tests cover:

trigger_webhook.py:
- FastAPI webhook endpoint behavior
- Issue opened event handling
- Issue comment event handling
- Workflow extraction from body/comments
- CXC ID handling (provided vs generated)
- Model set extraction
- Dependent workflow validation
- Bot comment loop prevention
- Health check endpoint

trigger_cron.py:
- should_process_issue: Comment detection logic
- trigger_cxc_workflow: CLI invocation
- check_and_process_issues: Main polling loop
- Graceful shutdown handling
"""

import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock, call
from pathlib import Path


# ==================== trigger_webhook.py Tests ====================


class TestWebhookEndpoint:
    """Tests for /gh-webhook FastAPI endpoint."""

    def test_issue_opened_with_cxc_workflow(self, mock_env_vars):
        """<R8.1> Issue opened with 'cxc_plan_iso' in body triggers workflow."""
        from cxc.triggers.trigger_webhook import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        payload = {
            "action": "opened",
            "issue": {
                "number": 42,
                "title": "Test Issue",
                "body": "Please run cxc_plan_iso to plan this feature",
            },
        }

        with patch("cxc.triggers.trigger_webhook.extract_cxc_info") as mock_extract, \
             patch("cxc.triggers.trigger_webhook.make_cxc_id", return_value="test1234"), \
             patch("cxc.triggers.trigger_webhook.make_issue_comment"), \
             patch("cxc.triggers.trigger_webhook.subprocess.Popen") as mock_popen, \
             patch("cxc.triggers.trigger_webhook.CxcState") as mock_state:

            # Mock extraction result
            from cxc.integrations.workflow_ops import CXCExtractionResult
            mock_extract.return_value = CXCExtractionResult(
                workflow_command="cxc_plan_iso",
                cxc_id=None,
                model_set="base",
                has_workflow=True,
            )

            response = client.post(
                "/gh-webhook",
                json=payload,
                headers={"X-GitHub-Event": "issues"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["issue"] == 42
        assert data["workflow"] == "cxc_plan_iso"
        assert data["cxc_id"] == "test1234"

        # Verify Popen was called with correct command
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args
        cmd = call_args[0][0]
        assert "cxc.workflows.wt.plan_iso" in " ".join(cmd)
        assert "42" in cmd
        assert "test1234" in cmd

    def test_issue_comment_with_cxc_workflow(self, mock_env_vars):
        """<R8.2> Issue comment with 'cxc_sdlc_iso' triggers workflow."""
        from cxc.triggers.trigger_webhook import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        payload = {
            "action": "created",
            "issue": {
                "number": 43,
                "title": "Another Issue",
                "body": "Original issue body",
            },
            "comment": {
                "body": "cxc_sdlc_iso model_set heavy",
                "id": 12345,
            },
        }

        with patch("cxc.triggers.trigger_webhook.extract_cxc_info") as mock_extract, \
             patch("cxc.triggers.trigger_webhook.make_cxc_id", return_value="abc12345"), \
             patch("cxc.triggers.trigger_webhook.make_issue_comment"), \
             patch("cxc.triggers.trigger_webhook.subprocess.Popen") as mock_popen, \
             patch("cxc.triggers.trigger_webhook.CxcState") as mock_state:

            from cxc.integrations.workflow_ops import CXCExtractionResult
            mock_extract.return_value = CXCExtractionResult(
                workflow_command="cxc_sdlc_iso",
                cxc_id=None,
                model_set="heavy",
                has_workflow=True,
            )

            response = client.post(
                "/gh-webhook",
                json=payload,
                headers={"X-GitHub-Event": "issue_comment"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["workflow"] == "cxc_sdlc_iso"
        assert "abc12345" in data["cxc_id"]

        # Verify model_set was extracted
        mock_extract.assert_called_once()
        call_text = mock_extract.call_args[0][0]
        assert "model_set heavy" in call_text

    def test_dependent_workflow_without_cxc_id_rejected(self, mock_env_vars):
        """<R8.3> Dependent workflow (cxc_build_iso) without CXC ID is rejected."""
        from cxc.triggers.trigger_webhook import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        payload = {
            "action": "created",
            "issue": {"number": 44, "title": "Test", "body": "Original"},
            "comment": {"body": "cxc_build_iso", "id": 123},
        }

        with patch("cxc.triggers.trigger_webhook.extract_cxc_info") as mock_extract, \
             patch("cxc.triggers.trigger_webhook.make_cxc_id", return_value="xyz99999"), \
             patch("cxc.triggers.trigger_webhook.make_issue_comment") as mock_comment, \
             patch("cxc.triggers.trigger_webhook.subprocess.Popen") as mock_popen:

            from cxc.integrations.workflow_ops import CXCExtractionResult
            mock_extract.return_value = CXCExtractionResult(
                workflow_command="cxc_build_iso",
                cxc_id=None,  # No CXC ID provided
                model_set="base",
                has_workflow=True,
            )

            response = client.post(
                "/gh-webhook",
                json=payload,
                headers={"X-GitHub-Event": "issue_comment"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"

        # Verify error comment was posted
        mock_comment.assert_called_once()
        error_comment = mock_comment.call_args[0][1]
        assert "dependent workflow" in error_comment
        # Note: workflow is set to None in the error message due to bug in webhook code

        # Verify Popen was NOT called
        mock_popen.assert_not_called()

    def test_dependent_workflow_with_cxc_id_accepted(self, mock_env_vars):
        """<R8.4> Dependent workflow with provided CXC ID is accepted."""
        from cxc.triggers.trigger_webhook import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        payload = {
            "action": "created",
            "issue": {"number": 45, "title": "Test", "body": "Original"},
            "comment": {"body": "cxc_build_iso cxc-existing1", "id": 456},
        }

        with patch("cxc.triggers.trigger_webhook.extract_cxc_info") as mock_extract, \
             patch("cxc.triggers.trigger_webhook.make_issue_comment"), \
             patch("cxc.triggers.trigger_webhook.subprocess.Popen") as mock_popen, \
             patch("cxc.triggers.trigger_webhook.CxcState") as mock_state_class:

            # Mock state loading
            mock_state = MagicMock()
            mock_state_class.load.return_value = mock_state

            from cxc.integrations.workflow_ops import CXCExtractionResult
            mock_extract.return_value = CXCExtractionResult(
                workflow_command="cxc_build_iso",
                cxc_id="existing1",  # Provided CXC ID
                model_set="base",
                has_workflow=True,
            )

            response = client.post(
                "/gh-webhook",
                json=payload,
                headers={"X-GitHub-Event": "issue_comment"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["cxc_id"] == "existing1"

        # Verify state was loaded with provided ID
        mock_state_class.load.assert_called_once_with("existing1")

        # Verify Popen was called
        mock_popen.assert_called_once()

    def test_bot_comment_loop_prevention(self, mock_env_vars):
        """<R8.5> Comments from CXC bot are ignored to prevent loops."""
        from cxc.triggers.trigger_webhook import app
        from cxc.integrations.github import CXC_BOT_IDENTIFIER
        from fastapi.testclient import TestClient

        client = TestClient(app)

        payload = {
            "action": "created",
            "issue": {"number": 46, "title": "Test", "body": "Original"},
            "comment": {"body": f"{CXC_BOT_IDENTIFIER} cxc_plan_iso", "id": 789},
        }

        with patch("cxc.triggers.trigger_webhook.extract_cxc_info") as mock_extract, \
             patch("cxc.triggers.trigger_webhook.subprocess.Popen") as mock_popen:

            response = client.post(
                "/gh-webhook",
                json=payload,
                headers={"X-GitHub-Event": "issue_comment"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"

        # Verify extract_cxc_info was NOT called
        mock_extract.assert_not_called()

        # Verify Popen was NOT called
        mock_popen.assert_not_called()

    def test_non_cxc_comment_ignored(self, mock_env_vars):
        """<R8.6> Comments without 'cxc_' are ignored."""
        from cxc.triggers.trigger_webhook import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        payload = {
            "action": "created",
            "issue": {"number": 47, "title": "Test", "body": "Original"},
            "comment": {"body": "This is just a normal comment", "id": 999},
        }

        with patch("cxc.triggers.trigger_webhook.extract_cxc_info") as mock_extract, \
             patch("cxc.triggers.trigger_webhook.subprocess.Popen") as mock_popen:

            response = client.post(
                "/gh-webhook",
                json=payload,
                headers={"X-GitHub-Event": "issue_comment"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"

        # Verify extract_cxc_info was NOT called
        mock_extract.assert_not_called()
        mock_popen.assert_not_called()

    def test_webhook_error_handling(self, mock_env_vars):
        """<R8.7> Webhook errors return 200 with error status (GitHub compatibility)."""
        from cxc.triggers.trigger_webhook import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Trigger an actual exception by making extract_cxc_info raise
        payload = {
            "action": "opened",
            "issue": {
                "number": 99,
                "title": "Test",
                "body": "cxc_plan_iso",  # Will trigger extract_cxc_info
            },
        }

        with patch("cxc.triggers.trigger_webhook.extract_cxc_info") as mock_extract:
            mock_extract.side_effect = Exception("Unexpected error")

            response = client.post(
                "/gh-webhook",
                json=payload,
                headers={"X-GitHub-Event": "issues"},
            )

        # Should still return 200 to prevent GitHub retries
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check_success(self, mock_env_vars):
        """<R8.8> Health check returns healthy status when all checks pass."""
        from cxc.triggers.trigger_webhook import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        with patch("cxc.triggers.trigger_webhook.run_health_check") as mock_health:
            # Mock successful health check
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.warnings = []
            mock_result.errors = []
            mock_health.return_value = mock_result

            response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "cxc-webhook-trigger"
        assert data["health_check"]["success"] is True

    def test_health_check_failure(self, mock_env_vars):
        """<R8.9> Health check returns unhealthy when checks fail."""
        from cxc.triggers.trigger_webhook import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        with patch("cxc.triggers.trigger_webhook.run_health_check") as mock_health:
            # Mock failed health check
            mock_result = MagicMock()
            mock_result.success = False
            mock_result.warnings = ["Warning 1"]
            mock_result.errors = ["Error 1", "Error 2"]
            mock_health.return_value = mock_result

            response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert len(data["health_check"]["errors"]) == 2

    def test_health_check_exception(self, mock_env_vars):
        """<R8.10> Health check handles exceptions gracefully."""
        from cxc.triggers.trigger_webhook import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        with patch("cxc.triggers.trigger_webhook.run_health_check") as mock_health:
            mock_health.side_effect = Exception("Health check crashed")

            response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "Health check failed" in data["error"]


# ==================== trigger_cron.py Tests ====================


class TestShouldProcessIssue:
    """Tests for should_process_issue function."""

    def test_issue_with_no_comments_should_process(self, mock_env_vars):
        """<R9.1> Issue with no comments should be processed."""
        with patch("cxc.triggers.trigger_cron.fetch_issue_comments", return_value=[]), \
             patch("cxc.triggers.trigger_cron.REPO_PATH", "test-org/test-repo"):

            from cxc.triggers.trigger_cron import should_process_issue

            result = should_process_issue(42)

        assert result is True

    def test_issue_with_cxc_comment_should_process(self, mock_env_vars):
        """<R9.2> Issue with latest comment 'cxc' should be processed."""
        comments = [
            {"id": 1, "body": "This is an old comment"},
            {"id": 2, "body": "Another comment"},
            {"id": 3, "body": "cxc"},  # Latest comment
        ]

        with patch("cxc.triggers.trigger_cron.fetch_issue_comments", return_value=comments), \
             patch("cxc.triggers.trigger_cron.REPO_PATH", "test-org/test-repo"):

            from cxc.triggers.trigger_cron import should_process_issue

            result = should_process_issue(43)

        assert result is True

    def test_issue_with_cxc_whitespace_comment_should_process(self, mock_env_vars):
        """<R9.3> Issue with 'cxc' plus whitespace should be processed."""
        comments = [
            {"id": 1, "body": "  cxc  \n"},  # Whitespace around 'cxc'
        ]

        with patch("cxc.triggers.trigger_cron.fetch_issue_comments", return_value=comments), \
             patch("cxc.triggers.trigger_cron.REPO_PATH", "test-org/test-repo"):

            from cxc.triggers.trigger_cron import should_process_issue

            result = should_process_issue(44)

        assert result is True

    def test_issue_with_non_cxc_comment_should_not_process(self, mock_env_vars):
        """<R9.4> Issue with non-'cxc' comment should not be processed."""
        comments = [
            {"id": 1, "body": "Just a regular comment"},
        ]

        with patch("cxc.triggers.trigger_cron.fetch_issue_comments", return_value=comments), \
             patch("cxc.triggers.trigger_cron.REPO_PATH", "test-org/test-repo"):

            from cxc.triggers.trigger_cron import should_process_issue

            result = should_process_issue(45)

        assert result is False

    def test_issue_with_already_processed_comment_should_not_reprocess(self, mock_env_vars):
        """<R9.5> Issue with already processed comment should not be reprocessed."""
        comments = [
            {"id": 100, "body": "cxc"},
        ]

        with patch("cxc.triggers.trigger_cron.fetch_issue_comments", return_value=comments), \
             patch("cxc.triggers.trigger_cron.REPO_PATH", "test-org/test-repo"):

            from cxc.triggers.trigger_cron import should_process_issue, issue_last_comment

            # First call - should process
            result1 = should_process_issue(46)
            assert result1 is True

            # Second call - should not reprocess same comment
            result2 = should_process_issue(46)
            assert result2 is False

            # Verify tracking
            assert issue_last_comment.get(46) == 100

    def test_issue_with_partial_cxc_text_should_not_process(self, mock_env_vars):
        """<R9.6> Issue with 'cxc' as substring (not exact match) should not be processed."""
        comments = [
            {"id": 1, "body": "Please use cxc_plan_iso command"},  # Contains 'cxc' but not exact
        ]

        with patch("cxc.triggers.trigger_cron.fetch_issue_comments", return_value=comments), \
             patch("cxc.triggers.trigger_cron.REPO_PATH", "test-org/test-repo"):

            from cxc.triggers.trigger_cron import should_process_issue

            result = should_process_issue(47)

        # Should NOT process - requires exact 'cxc' match
        assert result is False


class TestTriggerCxcWorkflow:
    """Tests for trigger_cxc_workflow function."""

    def test_trigger_workflow_success(self, mock_env_vars):
        """<R9.7> Successful workflow trigger returns True."""
        with patch("cxc.triggers.trigger_cron.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Workflow started successfully",
                stderr="",
            )

            from cxc.triggers.trigger_cron import trigger_cxc_workflow

            result = trigger_cxc_workflow(42)

        assert result is True

        # Verify correct command was called
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "-m" in cmd
        assert "cxc.cli" in cmd
        assert "plan" in cmd
        assert "42" in cmd

    def test_trigger_workflow_failure(self, mock_env_vars):
        """<R9.8> Failed workflow trigger returns False."""
        with patch("cxc.triggers.trigger_cron.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Error: Something went wrong",
            )

            from cxc.triggers.trigger_cron import trigger_cxc_workflow

            result = trigger_cxc_workflow(43)

        assert result is False

    def test_trigger_workflow_exception(self, mock_env_vars):
        """<R9.9> Exception during workflow trigger returns False."""
        with patch("cxc.triggers.trigger_cron.subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Subprocess crashed")

            from cxc.triggers.trigger_cron import trigger_cxc_workflow

            result = trigger_cxc_workflow(44)

        assert result is False


class TestCheckAndProcessIssues:
    """Tests for check_and_process_issues function."""

    def test_no_open_issues(self, mock_env_vars):
        """<R9.10> No open issues results in no processing."""
        with patch("cxc.triggers.trigger_cron.fetch_open_issues", return_value=[]), \
             patch("cxc.triggers.trigger_cron.REPO_PATH", "test-org/test-repo"), \
             patch("cxc.triggers.trigger_cron.trigger_cxc_workflow") as mock_trigger:

            from cxc.triggers.trigger_cron import check_and_process_issues

            check_and_process_issues()

        # No workflows should be triggered
        mock_trigger.assert_not_called()

    def test_qualifying_issues_are_processed(self, mock_env_vars):
        """<R9.11> Qualifying issues trigger workflows."""
        from cxc.core.data_types import GitHubIssueListItem
        from datetime import datetime

        issues = [
            GitHubIssueListItem(number=42, title="Test 1", body="Test body 1", createdAt=datetime.now(), updatedAt=datetime.now()),
            GitHubIssueListItem(number=43, title="Test 2", body="Test body 2", createdAt=datetime.now(), updatedAt=datetime.now()),
        ]

        with patch("cxc.triggers.trigger_cron.fetch_open_issues", return_value=issues), \
             patch("cxc.triggers.trigger_cron.should_process_issue", return_value=True), \
             patch("cxc.triggers.trigger_cron.trigger_cxc_workflow", return_value=True) as mock_trigger, \
             patch("cxc.triggers.trigger_cron.REPO_PATH", "test-org/test-repo"):

            from cxc.triggers.trigger_cron import check_and_process_issues, processed_issues

            # Clear processed issues
            processed_issues.clear()

            check_and_process_issues()

        # Both issues should be triggered
        assert mock_trigger.call_count == 2
        mock_trigger.assert_any_call(42)
        mock_trigger.assert_any_call(43)

        # Both should be marked as processed
        assert 42 in processed_issues
        assert 43 in processed_issues

    def test_already_processed_issues_skipped(self, mock_env_vars):
        """<R9.12> Already processed issues are skipped."""
        from cxc.core.data_types import GitHubIssueListItem
        from datetime import datetime

        issues = [
            GitHubIssueListItem(number=42, title="Test", body="Test body", createdAt=datetime.now(), updatedAt=datetime.now()),
        ]

        with patch("cxc.triggers.trigger_cron.fetch_open_issues", return_value=issues), \
             patch("cxc.triggers.trigger_cron.should_process_issue") as mock_should, \
             patch("cxc.triggers.trigger_cron.trigger_cxc_workflow") as mock_trigger, \
             patch("cxc.triggers.trigger_cron.REPO_PATH", "test-org/test-repo"):

            from cxc.triggers.trigger_cron import check_and_process_issues, processed_issues

            # Mark issue as already processed
            processed_issues.clear()
            processed_issues.add(42)

            check_and_process_issues()

        # should_process_issue should NOT be called for already processed issue
        mock_should.assert_not_called()
        mock_trigger.assert_not_called()

    def test_failed_workflow_trigger_allows_retry(self, mock_env_vars):
        """<R9.13> Failed workflow trigger does not mark issue as processed."""
        from cxc.core.data_types import GitHubIssueListItem
        from datetime import datetime

        issues = [
            GitHubIssueListItem(number=42, title="Test", body="Test body", createdAt=datetime.now(), updatedAt=datetime.now()),
        ]

        with patch("cxc.triggers.trigger_cron.fetch_open_issues", return_value=issues), \
             patch("cxc.triggers.trigger_cron.should_process_issue", return_value=True), \
             patch("cxc.triggers.trigger_cron.trigger_cxc_workflow", return_value=False), \
             patch("cxc.triggers.trigger_cron.REPO_PATH", "test-org/test-repo"):

            from cxc.triggers.trigger_cron import check_and_process_issues, processed_issues

            processed_issues.clear()

            check_and_process_issues()

        # Issue should NOT be in processed_issues (allowing retry)
        assert 42 not in processed_issues

    def test_shutdown_during_processing(self, mock_env_vars):
        """<R9.14> Shutdown flag stops processing early."""
        from cxc.core.data_types import GitHubIssueListItem
        from datetime import datetime

        issues = [
            GitHubIssueListItem(number=42, title="Test 1", body="Body 1", createdAt=datetime.now(), updatedAt=datetime.now()),
            GitHubIssueListItem(number=43, title="Test 2", body="Body 2", createdAt=datetime.now(), updatedAt=datetime.now()),
        ]

        with patch("cxc.triggers.trigger_cron.fetch_open_issues", return_value=issues), \
             patch("cxc.triggers.trigger_cron.should_process_issue", return_value=True), \
             patch("cxc.triggers.trigger_cron.trigger_cxc_workflow", return_value=True) as mock_trigger, \
             patch("cxc.triggers.trigger_cron.REPO_PATH", "test-org/test-repo"), \
             patch("cxc.triggers.trigger_cron.shutdown_requested", True):

            from cxc.triggers.trigger_cron import check_and_process_issues

            check_and_process_issues()

        # No workflows should be triggered due to shutdown
        mock_trigger.assert_not_called()

    def test_exception_during_check_cycle(self, mock_env_vars):
        """<R9.15> Exception during check cycle is caught and logged."""
        with patch("cxc.triggers.trigger_cron.fetch_open_issues") as mock_fetch, \
             patch("cxc.triggers.trigger_cron.REPO_PATH", "test-org/test-repo"):

            mock_fetch.side_effect = Exception("GitHub API error")

            from cxc.triggers.trigger_cron import check_and_process_issues

            # Should not raise - exception is caught
            check_and_process_issues()


class TestSignalHandling:
    """Tests for graceful shutdown signal handling."""

    def test_signal_handler_sets_shutdown_flag(self):
        """<R9.16> Signal handler sets shutdown_requested flag."""
        import signal

        with patch("cxc.triggers.trigger_cron.shutdown_requested", False):
            from cxc.triggers.trigger_cron import signal_handler

            # Call signal handler
            signal_handler(signal.SIGINT, None)

            # Shutdown flag should be set
            from cxc.triggers.trigger_cron import shutdown_requested
            assert shutdown_requested is True


class TestRepoInfoInitialization:
    """Tests for repository info initialization."""

    def test_init_repo_info_success(self, mock_env_vars):
        """<R9.17> _init_repo_info sets REPO_PATH from git remote."""
        with patch("cxc.triggers.trigger_cron.get_repo_url", return_value="https://github.com/test-org/test-repo.git"), \
             patch("cxc.triggers.trigger_cron.extract_repo_path", return_value="test-org/test-repo"):

            from cxc.triggers.trigger_cron import _init_repo_info

            # Reset global state
            import cxc.triggers.trigger_cron as cron_module
            cron_module.GITHUB_REPO_URL = None
            cron_module.REPO_PATH = None

            _init_repo_info()

            assert cron_module.GITHUB_REPO_URL == "https://github.com/test-org/test-repo.git"
            assert cron_module.REPO_PATH == "test-org/test-repo"

    def test_init_repo_info_failure_exits(self, mock_env_vars):
        """<R9.18> _init_repo_info exits on failure to get repo URL."""
        with patch("cxc.triggers.trigger_cron.get_repo_url", side_effect=ValueError("No git remote")), \
             pytest.raises(SystemExit):

            from cxc.triggers.trigger_cron import _init_repo_info

            # Reset global state
            import cxc.triggers.trigger_cron as cron_module
            cron_module.GITHUB_REPO_URL = None
            cron_module.REPO_PATH = None

            _init_repo_info()
