"""Unit tests for adw/core/data_types.py - <R3> Pydantic Model Tests

Tests Pydantic models:
- GitHubIssue and related models
- Agent request/response models
- ADW state data model
- Review and documentation result models
"""

import pytest
from datetime import datetime
from typing import Dict, Any


class TestGitHubIssue:
    """Tests for GitHubIssue model."""
    
    def test_github_issue_parses_json(self, sample_github_issue: Dict[str, Any]):
        """<R3.1> GitHubIssue parses API response correctly."""
        from adw.core.data_types import GitHubIssue
        
        issue = GitHubIssue(**sample_github_issue)
        
        assert issue.number == 42
        assert issue.title == "Add new feature"
        assert "Description" in issue.body
        assert issue.state == "open"
        assert issue.author.login == "testuser"
    
    def test_github_issue_alias_mapping(self, sample_github_issue: Dict[str, Any]):
        """<R3.2> createdAt -> created_at alias mapping works."""
        from adw.core.data_types import GitHubIssue
        
        issue = GitHubIssue(**sample_github_issue)
        
        # Access via Python name (snake_case)
        assert issue.created_at is not None
        assert isinstance(issue.created_at, datetime)
        assert issue.updated_at is not None
    
    def test_github_issue_optional_fields(self, sample_github_issue: Dict[str, Any]):
        """<R3.3> Optional fields can be None."""
        from adw.core.data_types import GitHubIssue
        
        issue = GitHubIssue(**sample_github_issue)
        
        assert issue.milestone is None
        assert issue.closed_at is None
    
    def test_github_issue_lists(self, sample_github_issue: Dict[str, Any]):
        """<R3.4> List fields parsed correctly."""
        from adw.core.data_types import GitHubIssue
        
        issue = GitHubIssue(**sample_github_issue)
        
        assert isinstance(issue.labels, list)
        assert len(issue.labels) == 1
        assert issue.labels[0].name == "enhancement"
        
        assert isinstance(issue.comments, list)
        assert isinstance(issue.assignees, list)


class TestGitHubIssueListItem:
    """Tests for GitHubIssueListItem model."""
    
    def test_github_issue_list_item_minimal(self):
        """<R3.5> GitHubIssueListItem parses minimal list response."""
        from adw.core.data_types import GitHubIssueListItem
        
        data = {
            "number": 1,
            "title": "Test",
            "body": "Body",
            "labels": [],
            "createdAt": "2025-01-01T00:00:00Z",
            "updatedAt": "2025-01-01T00:00:00Z",
        }
        
        item = GitHubIssueListItem(**data)
        
        assert item.number == 1
        assert item.title == "Test"


class TestAgentPromptRequest:
    """Tests for AgentPromptRequest model."""
    
    def test_agent_prompt_request_defaults(self):
        """<R3.6> Default values are correct."""
        from adw.core.data_types import AgentPromptRequest
        
        request = AgentPromptRequest(
            prompt="Test prompt",
            adw_id="test123",
            output_file="output.jsonl",
        )
        
        assert request.agent_name == "ops"
        assert request.model == "sonnet"
        assert request.dangerously_skip_permissions is False
        assert request.working_dir is None
    
    def test_agent_prompt_request_custom(self):
        """<R3.6b> Custom values override defaults."""
        from adw.core.data_types import AgentPromptRequest
        
        request = AgentPromptRequest(
            prompt="Test prompt",
            adw_id="test123",
            agent_name="planner",
            model="opus",
            dangerously_skip_permissions=True,
            output_file="output.jsonl",
            working_dir="/path/to/dir",
        )
        
        assert request.agent_name == "planner"
        assert request.model == "opus"
        assert request.dangerously_skip_permissions is True
        assert request.working_dir == "/path/to/dir"


class TestAgentPromptResponse:
    """Tests for AgentPromptResponse model."""
    
    def test_agent_prompt_response_success(self):
        """<R3.7> Success response created correctly."""
        from adw.core.data_types import AgentPromptResponse, RetryCode
        
        response = AgentPromptResponse(
            output="Result text",
            success=True,
            session_id="session-123",
        )
        
        assert response.output == "Result text"
        assert response.success is True
        assert response.session_id == "session-123"
        assert response.retry_code == RetryCode.NONE
    
    def test_agent_prompt_response_retry_code(self):
        """<R3.8> RetryCode enum works correctly."""
        from adw.core.data_types import AgentPromptResponse, RetryCode
        
        response = AgentPromptResponse(
            output="Error",
            success=False,
            retry_code=RetryCode.CLAUDE_CODE_ERROR,
        )
        
        assert response.retry_code == RetryCode.CLAUDE_CODE_ERROR
        assert response.retry_code.value == "claude_code_error"


class TestRetryCode:
    """Tests for RetryCode enum."""
    
    def test_retry_code_values(self):
        """<R3.9> All RetryCode values are correct."""
        from adw.core.data_types import RetryCode
        
        assert RetryCode.CLAUDE_CODE_ERROR.value == "claude_code_error"
        assert RetryCode.TIMEOUT_ERROR.value == "timeout_error"
        assert RetryCode.EXECUTION_ERROR.value == "execution_error"
        assert RetryCode.ERROR_DURING_EXECUTION.value == "error_during_execution"
        assert RetryCode.NONE.value == "none"


class TestAgentTemplateRequest:
    """Tests for AgentTemplateRequest model."""
    
    def test_agent_template_request_slash_command(self):
        """<R3.10> SlashCommand literal validation works."""
        from adw.core.data_types import AgentTemplateRequest
        
        request = AgentTemplateRequest(
            agent_name="planner",
            slash_command="/implement",
            args=["plan.md"],
            adw_id="test123",
        )
        
        assert request.slash_command == "/implement"
        assert request.args == ["plan.md"]
    
    def test_agent_template_request_all_commands(self):
        """<R3.10b> All valid slash commands accepted."""
        from adw.core.data_types import AgentTemplateRequest
        
        valid_commands = [
            "/chore", "/bug", "/feature",
            "/classify_issue", "/classify_adw",
            "/generate_branch_name", "/commit", "/pull_request",
            "/implement", "/test", "/resolve_failed_test",
            "/test_e2e", "/resolve_failed_e2e_test",
            "/review", "/patch", "/document",
            "/track_agentic_kpis", "/install_worktree",
        ]
        
        for cmd in valid_commands:
            request = AgentTemplateRequest(
                agent_name="test",
                slash_command=cmd,
                args=[],
                adw_id="test123",
            )
            assert request.slash_command == cmd


class TestADWStateData:
    """Tests for ADWStateData model."""
    
    def test_adw_state_data_optional_fields(self):
        """<R3.11> Optional fields can be None."""
        from adw.core.data_types import ADWStateData
        
        state = ADWStateData(adw_id="test123")
        
        assert state.adw_id == "test123"
        assert state.issue_number is None
        assert state.branch_name is None
        assert state.plan_file is None
        assert state.issue_class is None
        assert state.worktree_path is None
        assert state.backend_port is None
        assert state.frontend_port is None
        assert state.model_set == "base"  # Default
        assert state.all_adws == []
    
    def test_adw_state_data_full(self):
        """<R3.11b> All fields populated correctly."""
        from adw.core.data_types import ADWStateData
        
        state = ADWStateData(
            adw_id="test123",
            issue_number="42",
            branch_name="feature-branch",
            plan_file="specs/plan.md",
            issue_class="/feature",
            worktree_path="/path/to/worktree",
            backend_port=9100,
            frontend_port=9200,
            model_set="heavy",
            all_adws=["adw_plan_iso", "adw_build_iso"],
        )
        
        assert state.issue_number == "42"
        assert state.model_set == "heavy"
        assert len(state.all_adws) == 2
    
    def test_adw_state_data_model_dump(self):
        """<R3.11c> model_dump() produces valid dict."""
        from adw.core.data_types import ADWStateData
        
        state = ADWStateData(
            adw_id="test123",
            issue_number="42",
        )
        
        dumped = state.model_dump()
        
        assert isinstance(dumped, dict)
        assert dumped["adw_id"] == "test123"
        assert dumped["issue_number"] == "42"


class TestReviewResult:
    """Tests for ReviewResult model."""
    
    def test_review_result_success(self):
        """<R3.12> Success review result created correctly."""
        from adw.core.data_types import ReviewResult
        
        result = ReviewResult(
            success=True,
            review_summary="Feature implemented correctly.",
            review_issues=[],
            screenshots=["screenshot1.png"],
        )
        
        assert result.success is True
        assert "implemented" in result.review_summary
        assert len(result.screenshots) == 1
    
    def test_review_result_with_issues(self):
        """<R3.12b> Review result with issues."""
        from adw.core.data_types import ReviewResult, ReviewIssue
        
        issue = ReviewIssue(
            review_issue_number=1,
            screenshot_path="/path/to/screenshot.png",
            issue_description="Button color is wrong",
            issue_resolution="Change to blue",
            issue_severity="skippable",
        )
        
        result = ReviewResult(
            success=True,  # Can still be success with skippable issues
            review_summary="Minor issues found.",
            review_issues=[issue],
            screenshots=[],
        )
        
        assert len(result.review_issues) == 1
        assert result.review_issues[0].issue_severity == "skippable"


class TestReviewIssue:
    """Tests for ReviewIssue model."""
    
    def test_review_issue_severities(self):
        """<R3.13> All severity levels valid."""
        from adw.core.data_types import ReviewIssue
        
        for severity in ["skippable", "tech_debt", "blocker"]:
            issue = ReviewIssue(
                review_issue_number=1,
                screenshot_path="/path.png",
                issue_description="Test",
                issue_resolution="Fix",
                issue_severity=severity,
            )
            assert issue.issue_severity == severity


class TestADWExtractionResult:
    """Tests for ADWExtractionResult model."""
    
    def test_adw_extraction_result_has_workflow(self):
        """<R3.14> has_workflow property returns correct boolean."""
        from adw.core.data_types import ADWExtractionResult
        
        # With workflow
        result_with = ADWExtractionResult(
            workflow_command="adw_plan_iso",
            adw_id="test123",
        )
        assert result_with.has_workflow is True
        
        # Without workflow
        result_without = ADWExtractionResult()
        assert result_without.has_workflow is False
    
    def test_adw_extraction_result_defaults(self):
        """<R3.14b> Default values are correct."""
        from adw.core.data_types import ADWExtractionResult
        
        result = ADWExtractionResult()
        
        assert result.workflow_command is None
        assert result.adw_id is None
        assert result.model_set == "base"


class TestTestResult:
    """Tests for TestResult model."""
    
    def test_test_result_passed(self):
        """<R3.15> Passed test result."""
        from adw.core.data_types import TestResult
        
        result = TestResult(
            test_name="test_example",
            passed=True,
            execution_command="pytest test_example.py",
            test_purpose="Verify example works",
        )
        
        assert result.passed is True
        assert result.error is None
    
    def test_test_result_failed(self):
        """<R3.15b> Failed test result with error."""
        from adw.core.data_types import TestResult
        
        result = TestResult(
            test_name="test_example",
            passed=False,
            execution_command="pytest test_example.py",
            test_purpose="Verify example works",
            error="AssertionError: expected True",
        )
        
        assert result.passed is False
        assert "AssertionError" in result.error


class TestE2ETestResult:
    """Tests for E2ETestResult model."""
    
    def test_e2e_test_result_passed(self):
        """<R3.16> Passed E2E test result."""
        from adw.core.data_types import E2ETestResult
        
        result = E2ETestResult(
            test_name="test_login",
            status="passed",
            test_path=".claude/commands/e2e/test_login.md",
            screenshots=["login_success.png"],
        )
        
        assert result.passed is True
        assert result.status == "passed"
    
    def test_e2e_test_result_failed(self):
        """<R3.16b> Failed E2E test result."""
        from adw.core.data_types import E2ETestResult
        
        result = E2ETestResult(
            test_name="test_login",
            status="failed",
            test_path=".claude/commands/e2e/test_login.md",
            error="Element not found",
        )
        
        assert result.passed is False
        assert result.status == "failed"


class TestDocumentationResult:
    """Tests for DocumentationResult model."""
    
    def test_documentation_result_success(self):
        """<R3.17> Success documentation result."""
        from adw.core.data_types import DocumentationResult
        
        result = DocumentationResult(
            success=True,
            documentation_created=True,
            documentation_path="app_docs/feature.md",
        )
        
        assert result.success is True
        assert result.documentation_created is True
        assert result.documentation_path == "app_docs/feature.md"
    
    def test_documentation_result_failure(self):
        """<R3.17b> Failed documentation result."""
        from adw.core.data_types import DocumentationResult
        
        result = DocumentationResult(
            success=False,
            documentation_created=False,
            error_message="Failed to generate docs",
        )
        
        assert result.success is False
        assert result.error_message is not None

