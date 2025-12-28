"""Unit tests for adw/integrations/workflow_ops.py

<R9> Workflow Operations Tests

Tests cover:
- format_issue_message: Formatting messages with ADW tracking
- extract_adw_info: Extracting workflow info from text
- classify_issue: Classifying issues into /feature, /bug, /chore
- build_plan: Building implementation plans
- implement_plan: Implementing plans
- generate_branch_name: Generating git branch names
- create_commit: Creating commit messages
- create_pull_request: Creating PRs
- ensure_adw_id: Ensuring ADW ID exists
- find_existing_branch_for_issue: Finding existing branches
- find_plan_for_issue: Finding plan files
- find_spec_file: Finding spec files
- create_and_implement_patch: Creating and implementing patches
- build_comprehensive_pr_body: Building PR bodies
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from adw.integrations import workflow_ops


# ----- Test format_issue_message -----

class TestFormatIssueMessage:
    """Tests for format_issue_message function."""

    def test_format_issue_message_basic(self):
        """<R9.1> Formats message with ADW ID and agent name."""
        from adw.integrations.workflow_ops import format_issue_message
        
        result = format_issue_message("test1234", "planner", "Plan created")
        
        assert "[ADW-AGENTS]" in result
        assert "test1234" in result
        assert "planner" in result
        assert "Plan created" in result

    def test_format_issue_message_with_session_id(self):
        """<R9.1> Includes session ID when provided."""
        from adw.integrations.workflow_ops import format_issue_message
        
        result = format_issue_message("test1234", "planner", "Plan created", "session123")
        
        assert "session123" in result


# ----- Test extract_adw_info -----

class TestExtractAdwInfo:
    """Tests for extract_adw_info function."""

    def test_extract_adw_info_success(self):
        """<R9.2> Extracts workflow command from text."""
        with patch("adw.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output='{"adw_slash_command": "/adw_plan_iso", "adw_id": "abc12345", "model_set": "base"}',
            )
            
            from adw.integrations.workflow_ops import extract_adw_info
            result = extract_adw_info("Please plan this feature", "temp123")
            
            assert result.workflow_command == "adw_plan_iso"
            assert result.adw_id == "abc12345"
            assert result.model_set == "base"

    def test_extract_adw_info_failure(self):
        """<R9.2> Returns empty result on failure."""
        with patch("adw.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=False,
                output="Error",
            )
            
            from adw.integrations.workflow_ops import extract_adw_info
            result = extract_adw_info("Invalid text", "temp123")
            
            assert result.workflow_command is None

    def test_extract_adw_info_invalid_command(self):
        """<R9.2> Returns empty result for invalid command."""
        with patch("adw.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output='{"adw_slash_command": "/invalid_command", "adw_id": "abc12345"}',
            )
            
            from adw.integrations.workflow_ops import extract_adw_info
            result = extract_adw_info("Some text", "temp123")
            
            assert result.workflow_command is None


# ----- Test classify_issue -----

class TestClassifyIssue:
    """Tests for classify_issue function."""

    def test_classify_issue_feature(self):
        """<R9.3> Returns /feature for feature issues."""
        with patch("adw.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="/feature",
            )
            
            from adw.integrations.workflow_ops import classify_issue
            from adw.core.data_types import GitHubIssue
            
            issue = MagicMock(spec=GitHubIssue)
            issue.number = 42
            issue.title = "Add new feature"
            issue.body = "Implement X"
            issue.model_dump_json = MagicMock(return_value='{"number": 42, "title": "Add new feature", "body": "Implement X"}')
            
            logger = MagicMock()
            result, error = classify_issue(issue, "test1234", logger)
            
            assert result == "/feature"
            assert error is None

    def test_classify_issue_bug(self):
        """<R9.3> Returns /bug for bug issues."""
        with patch("adw.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="/bug",
            )
            
            from adw.integrations.workflow_ops import classify_issue
            
            issue = MagicMock()
            issue.model_dump_json = MagicMock(return_value='{}')
            
            logger = MagicMock()
            result, error = classify_issue(issue, "test1234", logger)
            
            assert result == "/bug"

    def test_classify_issue_chore(self):
        """<R9.3> Returns /chore for chore issues."""
        with patch("adw.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="/chore",
            )
            
            from adw.integrations.workflow_ops import classify_issue
            
            issue = MagicMock()
            issue.model_dump_json = MagicMock(return_value='{}')
            
            logger = MagicMock()
            result, error = classify_issue(issue, "test1234", logger)
            
            assert result == "/chore"

    def test_classify_issue_zero(self):
        """<R9.3> Returns error for 0 (no command)."""
        with patch("adw.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="0",
            )
            
            from adw.integrations.workflow_ops import classify_issue
            
            issue = MagicMock()
            issue.model_dump_json = MagicMock(return_value='{}')
            
            logger = MagicMock()
            result, error = classify_issue(issue, "test1234", logger)
            
            assert result is None
            assert "No command selected" in error

    def test_classify_issue_failure(self):
        """<R9.3> Returns error on classification failure."""
        with patch("adw.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=False,
                output="Error classifying",
            )
            
            from adw.integrations.workflow_ops import classify_issue
            
            issue = MagicMock()
            issue.model_dump_json = MagicMock(return_value='{}')
            
            logger = MagicMock()
            result, error = classify_issue(issue, "test1234", logger)
            
            assert result is None
            assert error is not None


# ----- Test build_plan -----

class TestBuildPlan:
    """Tests for build_plan function."""

    def test_build_plan_success(self):
        """<R9.4> Returns plan response."""
        with patch("adw.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="Plan content here",
            )
            
            from adw.integrations.workflow_ops import build_plan
            
            issue = MagicMock()
            issue.number = 42
            issue.model_dump_json = MagicMock(return_value='{}')
            
            logger = MagicMock()
            result = build_plan(issue, "/feature", "test1234", logger)
            
            assert result.success is True
            assert "Plan content" in result.output


# ----- Test implement_plan -----

class TestImplementPlan:
    """Tests for implement_plan function."""

    def test_implement_plan_success(self):
        """<R9.5> Returns implement response."""
        with patch("adw.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="Implementation complete",
            )
            
            from adw.integrations.workflow_ops import implement_plan
            
            logger = MagicMock()
            result = implement_plan("specs/plan.md", "test1234", logger)
            
            assert result.success is True

    def test_implement_plan_custom_agent(self):
        """<R9.5> Uses custom agent name."""
        with patch("adw.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(success=True, output="Done")
            
            from adw.integrations.workflow_ops import implement_plan
            
            logger = MagicMock()
            implement_plan("specs/plan.md", "test1234", logger, agent_name="custom_agent")
            
            call_args = mock_execute.call_args[0][0]
            assert call_args.agent_name == "custom_agent"


# ----- Test generate_branch_name -----

class TestGenerateBranchName:
    """Tests for generate_branch_name function."""

    def test_generate_branch_name_success(self):
        """<R9.6> Generates valid branch name."""
        with patch("adw.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="feature-issue-42-adw-test1234-add-feature",
            )
            
            from adw.integrations.workflow_ops import generate_branch_name
            
            issue = MagicMock()
            issue.model_dump_json = MagicMock(return_value='{}')
            
            logger = MagicMock()
            result, error = generate_branch_name(issue, "/feature", "test1234", logger)
            
            assert result == "feature-issue-42-adw-test1234-add-feature"
            assert error is None

    def test_generate_branch_name_failure(self):
        """<R9.6> Returns error on failure."""
        with patch("adw.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=False,
                output="Error generating",
            )
            
            from adw.integrations.workflow_ops import generate_branch_name
            
            issue = MagicMock()
            issue.model_dump_json = MagicMock(return_value='{}')
            
            logger = MagicMock()
            result, error = generate_branch_name(issue, "/feature", "test1234", logger)
            
            assert result is None
            assert error is not None


# ----- Test ensure_adw_id -----

class TestEnsureAdwId:
    """Tests for ensure_adw_id function."""

    def test_ensure_adw_id_existing(self):
        """<R9.7> Returns existing ADW ID."""
        with patch("adw.integrations.workflow_ops.ADWState") as mock_state_class:
            mock_state = MagicMock()
            mock_state_class.load.return_value = mock_state
            
            from adw.integrations.workflow_ops import ensure_adw_id
            
            result = ensure_adw_id("42", adw_id="existing123")
            
            assert result == "existing123"

    def test_ensure_adw_id_new(self):
        """<R9.7> Creates new ADW ID when none provided."""
        # Simply test that the function returns a new ID when none exists
        # The actual ID generation is tested in utils tests
        with patch.object(workflow_ops, "ADWState") as mock_state_class:
            mock_state_class.load.return_value = None
            mock_state = MagicMock()
            mock_state_class.return_value = mock_state
            
            # Import and call - the function will create a real ID
            result = workflow_ops.ensure_adw_id("42")
            
            # The function creates a new ID when none exists
            assert result is not None
            assert len(result) == 8  # ADW IDs are 8 chars
            mock_state.update.assert_called()
            mock_state.save.assert_called()


# ----- Test find_existing_branch_for_issue -----

class TestFindExistingBranchForIssue:
    """Tests for find_existing_branch_for_issue function."""

    def test_find_existing_branch_found(self):
        """<R9.8> Finds matching branch."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="  main\n* feature-issue-42-adw-test1234-feature\n  develop\n",
                stderr="",
            )
            
            from adw.integrations.workflow_ops import find_existing_branch_for_issue
            result = find_existing_branch_for_issue("42", "test1234")
            
            assert result == "feature-issue-42-adw-test1234-feature"

    def test_find_existing_branch_not_found(self):
        """<R9.8> Returns None when no match."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="  main\n  develop\n",
                stderr="",
            )
            
            from adw.integrations.workflow_ops import find_existing_branch_for_issue
            result = find_existing_branch_for_issue("42")
            
            assert result is None


# ----- Test find_plan_for_issue -----

class TestFindPlanForIssue:
    """Tests for find_plan_for_issue function."""

    def test_find_plan_for_issue_with_adw_id(self, tmp_path):
        """<R9.9> Finds plan in specific directory."""
        from adw.core import config as config_module
        
        with patch.object(config_module, "ADWConfig") as mock_config:
            config = MagicMock()
            config.get_project_artifacts_dir.return_value = tmp_path
            mock_config.load.return_value = config
            
            # Create plan file
            plan_dir = tmp_path / "test1234" / "sdlc_planner"
            plan_dir.mkdir(parents=True)
            plan_file = plan_dir / "plan.md"
            plan_file.write_text("# Plan")
            
            result = workflow_ops.find_plan_for_issue("42", "test1234")
            
            assert result == str(plan_file)

    def test_find_plan_for_issue_not_found(self, tmp_path):
        """<R9.9> Returns None when no plan exists."""
        from adw.core import config as config_module
        
        with patch.object(config_module, "ADWConfig") as mock_config:
            config = MagicMock()
            config.get_project_artifacts_dir.return_value = tmp_path
            mock_config.load.return_value = config
            
            result = workflow_ops.find_plan_for_issue("42")
            
            assert result is None


# ----- Test find_spec_file -----

class TestFindSpecFile:
    """Tests for find_spec_file function."""

    def test_find_spec_file_from_state(self, tmp_path):
        """<R9.10> Uses spec file from state."""
        spec_file = tmp_path / "specs" / "plan.md"
        spec_file.parent.mkdir(parents=True)
        spec_file.write_text("# Spec")
        
        from adw.integrations.workflow_ops import find_spec_file
        
        state = MagicMock()
        state.get.side_effect = lambda k: {
            "plan_file": str(spec_file),
            "worktree_path": None,
        }.get(k)
        
        logger = MagicMock()
        result = find_spec_file(state, logger)
        
        assert result == str(spec_file)

    def test_find_spec_file_not_found(self):
        """<R9.10> Returns None when no spec file."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            from adw.integrations.workflow_ops import find_spec_file
            
            state = MagicMock()
            state.get.return_value = None
            
            logger = MagicMock()
            result = find_spec_file(state, logger)
            
            assert result is None


# ----- Test build_comprehensive_pr_body -----

class TestBuildComprehensivePrBody:
    """Tests for build_comprehensive_pr_body function."""

    def test_build_comprehensive_pr_body_basic(self):
        """<R9.11> Builds complete PR body."""
        from adw.integrations.workflow_ops import build_comprehensive_pr_body
        
        state = MagicMock()
        state.get.side_effect = lambda k, default=None: {
            "adw_id": "test1234",
            "issue_number": "42",
            "plan_file": "specs/plan.md",
            "issue_class": "/feature",
            "branch_name": "feature-branch",
            "all_adws": ["adw_plan_iso", "adw_build_iso"],
        }.get(k, default)
        
        issue = MagicMock()
        issue.title = "Add new feature"
        
        result = build_comprehensive_pr_body(state, issue)
        
        assert "## Summary" in result
        assert "test1234" in result
        assert "#42" in result
        assert "Add new feature" in result

    def test_build_comprehensive_pr_body_with_review(self):
        """<R9.11> Includes review summary."""
        from adw.integrations.workflow_ops import build_comprehensive_pr_body
        
        state = MagicMock()
        state.get.side_effect = lambda k, default=None: {
            "adw_id": "test1234",
            "issue_number": "42",
            "all_adws": [],
        }.get(k, default)
        
        result = build_comprehensive_pr_body(
            state,
            None,
            review_summary="All checks passed",
        )
        
        assert "Review Summary" in result
        assert "All checks passed" in result

    def test_build_comprehensive_pr_body_with_remediation(self):
        """<R9.11> Shows remediation loops."""
        from adw.integrations.workflow_ops import build_comprehensive_pr_body
        
        state = MagicMock()
        state.get.side_effect = lambda k, default=None: {
            "adw_id": "test1234",
            "issue_number": "42",
            "all_adws": [],
        }.get(k, default)
        
        result = build_comprehensive_pr_body(
            state,
            None,
            remediation_loops=3,
        )
        
        assert "Remediation" in result
        assert "3" in result


# ----- Test create_pull_request -----

class TestCreatePullRequest:
    """Tests for create_pull_request function."""

    def test_create_pull_request_success(self):
        """<R9.12> Creates PR successfully."""
        with patch("adw.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="https://github.com/org/repo/pull/42",
            )
            
            from adw.integrations.workflow_ops import create_pull_request
            
            state = MagicMock()
            state.get.side_effect = lambda k: {
                "plan_file": "specs/plan.md",
                "adw_id": "test1234",
            }.get(k)
            
            issue = MagicMock()
            issue.model_dump_json = MagicMock(return_value='{}')
            
            logger = MagicMock()
            result, error = create_pull_request("feature-branch", issue, state, logger, "/work/dir")
            
            assert "pull/42" in result
            assert error is None


# ----- Test create_commit -----

class TestCreateCommit:
    """Tests for create_commit function."""

    def test_create_commit_success(self):
        """<R9.13> Creates commit message."""
        with patch("adw.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="feat: Add new feature",
            )
            
            from adw.integrations.workflow_ops import create_commit
            
            issue = MagicMock()
            issue.model_dump_json = MagicMock(return_value='{}')
            
            logger = MagicMock()
            result, error = create_commit("planner", issue, "/feature", "test1234", logger, "/work/dir")
            
            assert result == "feat: Add new feature"
            assert error is None

