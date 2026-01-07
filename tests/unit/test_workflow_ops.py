"""Unit tests for cxc/integrations/workflow_ops.py

<R9> Workflow Operations Tests

Tests cover:
- format_issue_message: Formatting messages with CXC tracking
- extract_cxc_info: Extracting workflow info from text
- classify_issue: Classifying issues into /feature, /bug, /chore
- build_plan: Building implementation plans
- implement_plan: Implementing plans
- generate_branch_name: Generating git branch names
- create_commit: Creating commit messages
- create_pull_request: Creating PRs
- ensure_cxc_id: Ensuring CXC ID exists
- find_existing_branch_for_issue: Finding existing branches
- find_plan_for_issue: Finding plan files
- find_spec_file: Finding spec files
- create_and_implement_patch: Creating and implementing patches
- build_comprehensive_pr_body: Building PR bodies
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from cxc.integrations import workflow_ops


# ----- Test format_issue_message -----

class TestFormatIssueMessage:
    """Tests for format_issue_message function."""

    def test_format_issue_message_basic(self):
        """<R9.1> Formats message with CXC ID and agent name."""
        from cxc.integrations.workflow_ops import format_issue_message
        
        result = format_issue_message("test1234", "planner", "Plan created")
        
        assert "[CXC-AGENTS]" in result
        assert "test1234" in result
        assert "planner" in result
        assert "Plan created" in result

    def test_format_issue_message_with_session_id(self):
        """<R9.1> Includes session ID when provided."""
        from cxc.integrations.workflow_ops import format_issue_message
        
        result = format_issue_message("test1234", "planner", "Plan created", "session123")
        
        assert "session123" in result


# ----- Test extract_cxc_info -----

class TestExtractCxcInfo:
    """Tests for extract_cxc_info function."""

    def test_extract_cxc_info_success(self):
        """<R9.2> Extracts workflow command from text."""
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output='{"cxc_slash_command": "/cxc_plan_iso", "cxc_id": "abc12345", "model_set": "base"}',
            )
            
            from cxc.integrations.workflow_ops import extract_cxc_info
            result = extract_cxc_info("Please plan this feature", "temp123")
            
            assert result.workflow_command == "cxc_plan_iso"
            assert result.cxc_id == "abc12345"
            assert result.model_set == "base"

    def test_extract_cxc_info_failure(self):
        """<R9.2> Returns empty result on failure."""
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=False,
                output="Error",
            )
            
            from cxc.integrations.workflow_ops import extract_cxc_info
            result = extract_cxc_info("Invalid text", "temp123")
            
            assert result.workflow_command is None

    def test_extract_cxc_info_invalid_command(self):
        """<R9.2> Returns empty result for invalid command."""
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output='{"cxc_slash_command": "/invalid_command", "cxc_id": "abc12345"}',
            )
            
            from cxc.integrations.workflow_ops import extract_cxc_info
            result = extract_cxc_info("Some text", "temp123")
            
            assert result.workflow_command is None


# ----- Test classify_issue -----

class TestClassifyIssue:
    """Tests for classify_issue function."""

    def test_classify_issue_feature(self):
        """<R9.3> Returns /feature for feature issues."""
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="/feature",
            )
            
            from cxc.integrations.workflow_ops import classify_issue
            from cxc.core.data_types import GitHubIssue
            
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
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="/bug",
            )
            
            from cxc.integrations.workflow_ops import classify_issue
            
            issue = MagicMock()
            issue.model_dump_json = MagicMock(return_value='{}')
            
            logger = MagicMock()
            result, error = classify_issue(issue, "test1234", logger)
            
            assert result == "/bug"

    def test_classify_issue_chore(self):
        """<R9.3> Returns /chore for chore issues."""
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="/chore",
            )
            
            from cxc.integrations.workflow_ops import classify_issue
            
            issue = MagicMock()
            issue.model_dump_json = MagicMock(return_value='{}')
            
            logger = MagicMock()
            result, error = classify_issue(issue, "test1234", logger)
            
            assert result == "/chore"

    def test_classify_issue_zero(self):
        """<R9.3> Returns error for 0 (no command)."""
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="0",
            )
            
            from cxc.integrations.workflow_ops import classify_issue
            
            issue = MagicMock()
            issue.model_dump_json = MagicMock(return_value='{}')
            
            logger = MagicMock()
            result, error = classify_issue(issue, "test1234", logger)
            
            assert result is None
            assert "No command selected" in error

    def test_classify_issue_failure(self):
        """<R9.3> Returns error on classification failure."""
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=False,
                output="Error classifying",
            )
            
            from cxc.integrations.workflow_ops import classify_issue
            
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
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="Plan content here",
            )
            
            from cxc.integrations.workflow_ops import build_plan
            
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
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="Implementation complete",
            )
            
            from cxc.integrations.workflow_ops import implement_plan
            
            logger = MagicMock()
            result = implement_plan("specs/plan.md", "test1234", logger)
            
            assert result.success is True

    def test_implement_plan_custom_agent(self):
        """<R9.5> Uses custom agent name."""
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(success=True, output="Done")
            
            from cxc.integrations.workflow_ops import implement_plan
            
            logger = MagicMock()
            implement_plan("specs/plan.md", "test1234", logger, agent_name="custom_agent")
            
            call_args = mock_execute.call_args[0][0]
            assert call_args.agent_name == "custom_agent"


# ----- Test generate_branch_name -----

class TestGenerateBranchName:
    """Tests for generate_branch_name function."""

    def test_generate_branch_name_success(self):
        """<R9.6> Generates valid branch name."""
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="feature-issue-42-cxc-test1234-add-feature",
            )
            
            from cxc.integrations.workflow_ops import generate_branch_name
            
            issue = MagicMock()
            issue.model_dump_json = MagicMock(return_value='{}')
            
            logger = MagicMock()
            result, error = generate_branch_name(issue, "/feature", "test1234", logger)
            
            assert result == "feature-issue-42-cxc-test1234-add-feature"
            assert error is None

    def test_generate_branch_name_failure(self):
        """<R9.6> Returns error on failure."""
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=False,
                output="Error generating",
            )
            
            from cxc.integrations.workflow_ops import generate_branch_name
            
            issue = MagicMock()
            issue.model_dump_json = MagicMock(return_value='{}')
            
            logger = MagicMock()
            result, error = generate_branch_name(issue, "/feature", "test1234", logger)
            
            assert result is None
            assert error is not None

    def test_generate_branch_name_strips_code_fence_no_lang(self):
        """<R9.6a> Strips markdown code fences without language specifier.
        
        If generate_branch_name doesn't strip ```\\n...\\n``` then broken.
        """
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="```\nfeature-issue-42-cxc-test1234-add-auth\n```",
            )
            
            from cxc.integrations.workflow_ops import generate_branch_name
            
            issue = MagicMock()
            issue.model_dump_json = MagicMock(return_value='{}')
            
            logger = MagicMock()
            result, error = generate_branch_name(issue, "/feature", "test1234", logger)
            
            assert result == "feature-issue-42-cxc-test1234-add-auth"
            assert error is None

    def test_generate_branch_name_strips_code_fence_with_lang(self):
        """<R9.6b> Strips markdown code fences WITH language specifier (e.g. ```python).
        
        If generate_branch_name doesn't strip ```python\\n...\\n``` then broken.
        """
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="```python\nfeature-issue-42-cxc-test1234-add-auth\n```",
            )
            
            from cxc.integrations.workflow_ops import generate_branch_name
            
            issue = MagicMock()
            issue.model_dump_json = MagicMock(return_value='{}')
            
            logger = MagicMock()
            result, error = generate_branch_name(issue, "/feature", "test1234", logger)
            
            assert result == "feature-issue-42-cxc-test1234-add-auth"
            assert error is None

    def test_generate_branch_name_strips_code_fence_with_bash(self):
        """<R9.6c> Strips markdown code fences with bash language specifier.
        
        If generate_branch_name doesn't strip ```bash\\n...\\n``` then broken.
        """
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="```bash\nbug-issue-99-cxc-xyz12345-fix-crash\n```",
            )
            
            from cxc.integrations.workflow_ops import generate_branch_name
            
            issue = MagicMock()
            issue.model_dump_json = MagicMock(return_value='{}')
            
            logger = MagicMock()
            result, error = generate_branch_name(issue, "/bug", "xyz12345", logger)
            
            assert result == "bug-issue-99-cxc-xyz12345-fix-crash"
            assert error is None


# ----- Test ensure_cxc_id -----

class TestEnsureCxcId:
    """Tests for ensure_cxc_id function."""

    def test_ensure_cxc_id_existing(self):
        """<R9.7> Returns existing CXC ID."""
        with patch("cxc.integrations.workflow_ops.CxcState") as mock_state_class:
            mock_state = MagicMock()
            mock_state_class.load.return_value = mock_state
            
            from cxc.integrations.workflow_ops import ensure_cxc_id
            
            result = ensure_cxc_id("42", cxc_id="existing123")
            
            assert result == "existing123"

    def test_ensure_cxc_id_new(self):
        """<R9.7> Creates new CXC ID when none provided."""
        # Simply test that the function returns a new ID when none exists
        # The actual ID generation is tested in utils tests
        with patch.object(workflow_ops, "CxcState") as mock_state_class:
            mock_state_class.load.return_value = None
            mock_state = MagicMock()
            mock_state_class.return_value = mock_state
            
            # Import and call - the function will create a real ID
            result = workflow_ops.ensure_cxc_id("42")
            
            # The function creates a new ID when none exists
            assert result is not None
            assert len(result) == 8  # CXC IDs are 8 chars
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
                stdout="  main\n* feature-issue-42-cxc-test1234-feature\n  develop\n",
                stderr="",
            )
            
            from cxc.integrations.workflow_ops import find_existing_branch_for_issue
            result = find_existing_branch_for_issue("42", "test1234")
            
            assert result == "feature-issue-42-cxc-test1234-feature"

    def test_find_existing_branch_not_found(self):
        """<R9.8> Returns None when no match."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="  main\n  develop\n",
                stderr="",
            )
            
            from cxc.integrations.workflow_ops import find_existing_branch_for_issue
            result = find_existing_branch_for_issue("42")
            
            assert result is None


# ----- Test find_plan_for_issue -----

class TestFindPlanForIssue:
    """Tests for find_plan_for_issue function."""

    def test_find_plan_for_issue_with_cxc_id(self, tmp_path):
        """<R9.9> Finds plan in specific directory."""
        from cxc.core import config as config_module
        
        with patch.object(config_module, "CxcConfig") as mock_config:
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
        from cxc.core import config as config_module
        
        with patch.object(config_module, "CxcConfig") as mock_config:
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
        
        from cxc.integrations.workflow_ops import find_spec_file
        
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
            
            from cxc.integrations.workflow_ops import find_spec_file
            
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
        from cxc.integrations.workflow_ops import build_comprehensive_pr_body
        
        state = MagicMock()
        state.get.side_effect = lambda k, default=None: {
            "cxc_id": "test1234",
            "issue_number": "42",
            "plan_file": "specs/plan.md",
            "issue_class": "/feature",
            "branch_name": "feature-branch",
            "all_cxcs": ["cxc_plan_iso", "cxc_build_iso"],
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
        from cxc.integrations.workflow_ops import build_comprehensive_pr_body
        
        state = MagicMock()
        state.get.side_effect = lambda k, default=None: {
            "cxc_id": "test1234",
            "issue_number": "42",
            "all_cxcs": [],
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
        from cxc.integrations.workflow_ops import build_comprehensive_pr_body
        
        state = MagicMock()
        state.get.side_effect = lambda k, default=None: {
            "cxc_id": "test1234",
            "issue_number": "42",
            "all_cxcs": [],
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
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="https://github.com/org/repo/pull/42",
            )
            
            from cxc.integrations.workflow_ops import create_pull_request
            
            state = MagicMock()
            state.get.side_effect = lambda k: {
                "plan_file": "specs/plan.md",
                "cxc_id": "test1234",
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
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="feat: Add new feature",
            )
            
            from cxc.integrations.workflow_ops import create_commit
            
            issue = MagicMock()
            issue.model_dump_json = MagicMock(return_value='{}')
            
            logger = MagicMock()
            result, error = create_commit("planner", issue, "/feature", "test1234", logger, "/work/dir")
            
            assert result == "feat: Add new feature"
            assert error is None


# ----- Test post_artifact_to_issue -----

class TestPostArtifactToIssue:
    """Tests for post_artifact_to_issue function."""

    def test_post_artifact_to_issue_basic(self):
        """<R9.14> Posts artifact content to GitHub issue."""
        with patch("cxc.integrations.github.make_issue_comment") as mock_comment:
            from cxc.integrations.workflow_ops import post_artifact_to_issue
            
            post_artifact_to_issue(
                issue_number="42",
                cxc_id="test1234",
                agent_name="planner",
                title="📋 Test Plan",
                content="This is the plan content",
            )
            
            mock_comment.assert_called_once()
            call_args = mock_comment.call_args
            assert call_args[0][0] == "42"  # issue_number
            assert "📋 Test Plan" in call_args[0][1]
            assert "This is the plan content" in call_args[0][1]
            assert "<details>" in call_args[0][1]  # collapsible by default

    def test_post_artifact_to_issue_with_file_path(self):
        """<R9.14> Includes file path in summary when provided."""
        with patch("cxc.integrations.github.make_issue_comment") as mock_comment:
            from cxc.integrations.workflow_ops import post_artifact_to_issue
            
            post_artifact_to_issue(
                issue_number="42",
                cxc_id="test1234",
                agent_name="planner",
                title="📋 Plan",
                content="Content here",
                file_path="specs/plan.md",
            )
            
            call_args = mock_comment.call_args
            assert "specs/plan.md" in call_args[0][1]

    def test_post_artifact_to_issue_truncates_long_content(self):
        """<R9.14> Truncates content exceeding max_length."""
        with patch("cxc.integrations.github.make_issue_comment") as mock_comment:
            from cxc.integrations.workflow_ops import post_artifact_to_issue
            
            long_content = "x" * 10000
            
            post_artifact_to_issue(
                issue_number="42",
                cxc_id="test1234",
                agent_name="planner",
                title="📋 Plan",
                content=long_content,
                max_length=100,
            )
            
            call_args = mock_comment.call_args
            assert "truncated" in call_args[0][1].lower()
            # Should not contain the full 10000 x's
            assert len(call_args[0][1]) < 1000

    def test_post_artifact_to_issue_not_collapsible(self):
        """<R9.14> Skips details block when collapsible=False."""
        with patch("cxc.integrations.github.make_issue_comment") as mock_comment:
            from cxc.integrations.workflow_ops import post_artifact_to_issue
            
            post_artifact_to_issue(
                issue_number="42",
                cxc_id="test1234",
                agent_name="planner",
                title="📋 Plan",
                content="Short content",
                collapsible=False,
            )
            
            call_args = mock_comment.call_args
            assert "<details>" not in call_args[0][1]

    def test_post_artifact_to_issue_empty_content_skipped(self):
        """<R9.14> Skips posting when content is empty."""
        with patch("cxc.integrations.github.make_issue_comment") as mock_comment:
            from cxc.integrations.workflow_ops import post_artifact_to_issue
            
            post_artifact_to_issue(
                issue_number="42",
                cxc_id="test1234",
                agent_name="planner",
                title="📋 Plan",
                content="",  # Empty content
            )
            
            mock_comment.assert_not_called()

    def test_post_artifact_to_issue_whitespace_only_skipped(self):
        """<R9.14> Skips posting when content is whitespace only."""
        with patch("cxc.integrations.github.make_issue_comment") as mock_comment:
            from cxc.integrations.workflow_ops import post_artifact_to_issue

            post_artifact_to_issue(
                issue_number="42",
                cxc_id="test1234",
                agent_name="planner",
                title="📋 Plan",
                content="   \n\t  ",  # Whitespace only
            )

            mock_comment.assert_not_called()


# ----- Test post_state_to_issue -----

class TestPostStateToIssue:
    """Tests for post_state_to_issue function."""

    def test_post_state_to_issue_basic(self):
        """<R9.15> Posts state as collapsible JSON."""
        with patch("cxc.integrations.github.make_issue_comment") as mock_comment:
            from cxc.integrations.workflow_ops import post_state_to_issue

            state_data = {
                "cxc_id": "test1234",
                "issue_number": "42",
                "branch_name": "feature-test",
            }

            post_state_to_issue(
                issue_number="42",
                cxc_id="test1234",
                state_data=state_data,
            )

            mock_comment.assert_called_once()
            call_args = mock_comment.call_args
            assert call_args[0][0] == "42"
            assert "<details>" in call_args[0][1]
            assert "test1234" in call_args[0][1]
            assert "feature-test" in call_args[0][1]

    def test_post_state_to_issue_custom_title(self):
        """<R9.15> Uses custom title when provided."""
        with patch("cxc.integrations.github.make_issue_comment") as mock_comment:
            from cxc.integrations.workflow_ops import post_state_to_issue

            state_data = {"status": "complete"}

            post_state_to_issue(
                issue_number="42",
                cxc_id="test1234",
                state_data=state_data,
                title="🎉 Final State",
            )

            call_args = mock_comment.call_args
            assert "🎉 Final State" in call_args[0][1]


# ----- Test ensure_plan_exists -----

class TestEnsurePlanExists:
    """Tests for ensure_plan_exists function."""

    def test_ensure_plan_exists_from_state(self):
        """<R9.16> Returns plan file from state."""
        from cxc.integrations.workflow_ops import ensure_plan_exists

        state = MagicMock()
        state.get.return_value = "specs/issue-42-plan.md"

        result = ensure_plan_exists(state, "42")

        assert result == "specs/issue-42-plan.md"

    def test_ensure_plan_exists_not_found_raises(self):
        """<R9.16> Raises ValueError when no plan found."""
        with patch("cxc.integrations.git_ops.get_current_branch") as mock_branch:
            with patch("glob.glob") as mock_glob:
                mock_branch.return_value = "main"
                mock_glob.return_value = []

                from cxc.integrations.workflow_ops import ensure_plan_exists

                state = MagicMock()
                state.get.return_value = None

                import pytest
                with pytest.raises(ValueError, match="No plan found"):
                    ensure_plan_exists(state, "42")

    def test_ensure_plan_exists_searches_current_branch(self):
        """<R9.16> Searches for plan in current branch."""
        with patch("cxc.integrations.git_ops.get_current_branch") as mock_branch:
            with patch("glob.glob") as mock_glob:
                mock_branch.return_value = "feature-issue-42-cxc-test1234-feature"
                mock_glob.return_value = ["specs/issue-42-test1234-plan.md"]

                from cxc.integrations.workflow_ops import ensure_plan_exists

                state = MagicMock()
                state.get.return_value = None

                result = ensure_plan_exists(state, "42")

                assert result == "specs/issue-42-test1234-plan.md"


# ----- Test create_and_implement_patch -----

class TestCreateAndImplementPatch:
    """Tests for create_and_implement_patch function."""

    def test_create_and_implement_patch_success(self):
        """<R9.17> Creates patch and implements it."""
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            # First call: create patch (returns file path)
            # Second call: implement patch (returns success)
            mock_execute.side_effect = [
                MagicMock(success=True, output="specs/patch/fix-issue-42.md"),
                MagicMock(success=True, output="Patch implemented"),
            ]

            from cxc.integrations.workflow_ops import create_and_implement_patch

            logger = MagicMock()
            patch_file, implement_response = create_and_implement_patch(
                cxc_id="test1234",
                review_change_request="Fix the bug",
                logger=logger,
                agent_name_planner="planner",
                agent_name_implementor="implementor",
            )

            assert patch_file == "specs/patch/fix-issue-42.md"
            assert implement_response.success is True

    def test_create_and_implement_patch_plan_failure(self):
        """<R9.17> Returns error when patch plan fails."""
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=False,
                output="Failed to create patch plan"
            )

            from cxc.integrations.workflow_ops import create_and_implement_patch

            logger = MagicMock()
            patch_file, implement_response = create_and_implement_patch(
                cxc_id="test1234",
                review_change_request="Fix the bug",
                logger=logger,
                agent_name_planner="planner",
                agent_name_implementor="implementor",
            )

            assert patch_file is None
            assert implement_response.success is False

    def test_create_and_implement_patch_invalid_path(self):
        """<R9.17> Returns error for invalid patch path."""
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="invalid/path.txt"  # Not in specs/patch/
            )

            from cxc.integrations.workflow_ops import create_and_implement_patch

            logger = MagicMock()
            patch_file, implement_response = create_and_implement_patch(
                cxc_id="test1234",
                review_change_request="Fix the bug",
                logger=logger,
                agent_name_planner="planner",
                agent_name_implementor="implementor",
            )

            assert patch_file is None
            assert implement_response.success is False
            assert "Invalid patch plan path" in implement_response.output

    def test_create_and_implement_patch_with_spec(self):
        """<R9.17> Passes spec_path to patch command."""
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.side_effect = [
                MagicMock(success=True, output="specs/patch/fix.md"),
                MagicMock(success=True, output="Done"),
            ]

            from cxc.integrations.workflow_ops import create_and_implement_patch

            logger = MagicMock()
            create_and_implement_patch(
                cxc_id="test1234",
                review_change_request="Fix",
                logger=logger,
                agent_name_planner="planner",
                agent_name_implementor="implementor",
                spec_path="specs/original-spec.md",
            )

            # Check that spec_path was passed in args
            call_args = mock_execute.call_args_list[0][0][0]
            assert "specs/original-spec.md" in call_args.args


# ----- Test create_or_find_branch -----

class TestCreateOrFindBranch:
    """Tests for create_or_find_branch function."""

    def test_create_or_find_branch_from_state(self):
        """<R9.18> Uses branch from state."""
        with patch("cxc.integrations.git_ops.get_current_branch") as mock_current:
            mock_current.return_value = "feature-branch"

            from cxc.integrations.workflow_ops import create_or_find_branch

            state = MagicMock()
            state.get.side_effect = lambda k: {
                "branch_name": "feature-branch",
                "cxc_id": "test1234",
            }.get(k)

            issue = MagicMock()
            logger = MagicMock()

            branch_name, error = create_or_find_branch("42", issue, state, logger)

            assert branch_name == "feature-branch"
            assert error is None

    def test_create_or_find_branch_checkout_existing(self):
        """<R9.18> Checks out existing branch from state."""
        with patch("cxc.integrations.git_ops.get_current_branch") as mock_current:
            with patch("subprocess.run") as mock_run:
                mock_current.return_value = "main"  # Different from state
                mock_run.return_value = MagicMock(returncode=0)

                from cxc.integrations.workflow_ops import create_or_find_branch

                state = MagicMock()
                state.get.side_effect = lambda k: {
                    "branch_name": "feature-branch",
                    "cxc_id": "test1234",
                }.get(k)

                issue = MagicMock()
                logger = MagicMock()

                branch_name, error = create_or_find_branch("42", issue, state, logger)

                assert branch_name == "feature-branch"
                # Should have called git checkout
                mock_run.assert_called()

    def test_create_or_find_branch_finds_existing(self):
        """<R9.18> Finds existing branch for issue."""
        with patch("cxc.integrations.workflow_ops.find_existing_branch_for_issue") as mock_find:
            with patch("subprocess.run") as mock_run:
                mock_find.return_value = "feature-issue-42-cxc-test1234-feature"
                mock_run.return_value = MagicMock(returncode=0)

                from cxc.integrations.workflow_ops import create_or_find_branch

                state = MagicMock()
                state.get.side_effect = lambda k, default=None: {
                    "cxc_id": "test1234",
                }.get(k, default)

                issue = MagicMock()
                logger = MagicMock()

                branch_name, error = create_or_find_branch("42", issue, state, logger)

                assert branch_name == "feature-issue-42-cxc-test1234-feature"
                state.update.assert_called_with(branch_name="feature-issue-42-cxc-test1234-feature")

    def test_create_or_find_branch_creates_new(self):
        """<R9.18> Creates new branch when none exists."""
        with patch("cxc.integrations.workflow_ops.find_existing_branch_for_issue") as mock_find:
            with patch("cxc.integrations.workflow_ops.classify_issue") as mock_classify:
                with patch("cxc.integrations.workflow_ops.generate_branch_name") as mock_gen:
                    with patch("cxc.integrations.git_ops.create_branch") as mock_create:
                        mock_find.return_value = None
                        mock_classify.return_value = ("/feature", None)
                        mock_gen.return_value = ("feature-issue-42-cxc-test1234-new", None)
                        mock_create.return_value = (True, None)

                        from cxc.integrations.workflow_ops import create_or_find_branch

                        state = MagicMock()
                        state.get.side_effect = lambda k, default=None: {
                            "cxc_id": "test1234",
                        }.get(k, default)

                        issue = MagicMock()
                        logger = MagicMock()

                        branch_name, error = create_or_find_branch("42", issue, state, logger)

                        assert branch_name == "feature-issue-42-cxc-test1234-new"
                        assert error is None

    def test_create_or_find_branch_classify_error(self):
        """<R9.18> Returns error when classification fails."""
        with patch("cxc.integrations.workflow_ops.find_existing_branch_for_issue") as mock_find:
            with patch("cxc.integrations.workflow_ops.classify_issue") as mock_classify:
                mock_find.return_value = None
                mock_classify.return_value = (None, "Classification failed")

                from cxc.integrations.workflow_ops import create_or_find_branch

                state = MagicMock()
                state.get.side_effect = lambda k, default=None: {
                    "cxc_id": "test1234",
                }.get(k, default)

                issue = MagicMock()
                logger = MagicMock()

                branch_name, error = create_or_find_branch("42", issue, state, logger)

                assert branch_name == ""
                assert "Classification failed" in error


# ----- Test find_spec_file edge cases -----

class TestFindSpecFileEdgeCases:
    """Additional tests for find_spec_file edge cases."""

    def test_find_spec_file_from_git_diff(self, tmp_path):
        """<R9.19> Finds spec file from git diff."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="specs/issue-42-cxc-test1234-feature.md\nsrc/main.py\n"
            )

            # Create the spec file
            spec_file = tmp_path / "specs" / "issue-42-cxc-test1234-feature.md"
            spec_file.parent.mkdir(parents=True)
            spec_file.write_text("# Spec")

            from cxc.integrations.workflow_ops import find_spec_file

            state = MagicMock()
            state.get.side_effect = lambda k: {
                "plan_file": None,
                "worktree_path": str(tmp_path),
            }.get(k)

            logger = MagicMock()
            result = find_spec_file(state, logger)

            assert result == str(spec_file)

    def test_find_spec_file_from_branch_pattern(self, tmp_path):
        """<R9.19> Finds spec file by branch name pattern."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")

            # Create the spec file
            spec_file = tmp_path / "specs" / "issue-42-cxc-test1234-feature.md"
            spec_file.parent.mkdir(parents=True)
            spec_file.write_text("# Spec")

            from cxc.integrations.workflow_ops import find_spec_file

            state = MagicMock()
            state.get.side_effect = lambda k: {
                "plan_file": None,
                "worktree_path": str(tmp_path),
                "branch_name": "feature-issue-42-cxc-test1234-feature",
                "cxc_id": "test1234",
            }.get(k)

            logger = MagicMock()
            result = find_spec_file(state, logger)

            assert result == str(spec_file)


# ----- Test classify_issue edge cases -----

class TestClassifyIssueEdgeCases:
    """Additional tests for classify_issue edge cases."""

    def test_classify_issue_with_explanation(self):
        """<R9.20> Extracts classification from response with explanation."""
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="Based on the issue description, this is a /bug that needs fixing.",
            )

            from cxc.integrations.workflow_ops import classify_issue

            issue = MagicMock()
            issue.model_dump_json = MagicMock(return_value='{}')

            logger = MagicMock()
            result, error = classify_issue(issue, "test1234", logger)

            assert result == "/bug"
            assert error is None

    def test_classify_issue_invalid_command(self):
        """<R9.20> Returns error for invalid command."""
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="/invalid_command",
            )

            from cxc.integrations.workflow_ops import classify_issue

            issue = MagicMock()
            issue.model_dump_json = MagicMock(return_value='{}')

            logger = MagicMock()
            result, error = classify_issue(issue, "test1234", logger)

            assert result is None
            assert "Invalid command" in error


# ----- Test generate_branch_name edge cases -----

class TestGenerateBranchNameEdgeCases:
    """Additional tests for generate_branch_name edge cases."""

    def test_generate_branch_name_empty_response(self):
        """<R9.21> Returns error for empty response."""
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="",
            )

            from cxc.integrations.workflow_ops import generate_branch_name

            issue = MagicMock()
            issue.model_dump_json = MagicMock(return_value='{}')

            logger = MagicMock()
            result, error = generate_branch_name(issue, "/feature", "test1234", logger)

            assert result is None
            assert "empty" in error


# ----- Test extract_cxc_info edge cases -----

class TestExtractCxcInfoEdgeCases:
    """Additional tests for extract_cxc_info edge cases."""

    def test_extract_cxc_info_json_parse_error(self):
        """<R9.22> Returns empty result on JSON parse error."""
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="not valid json",
            )

            from cxc.integrations.workflow_ops import extract_cxc_info
            result = extract_cxc_info("test text", "temp123")

            assert result.workflow_command is None

    def test_extract_cxc_info_exception(self):
        """<R9.22> Returns empty result on exception."""
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.side_effect = Exception("Unexpected error")

            from cxc.integrations.workflow_ops import extract_cxc_info
            result = extract_cxc_info("test text", "temp123")

            assert result.workflow_command is None


# ----- Test create_commit edge cases -----

class TestCreateCommitEdgeCases:
    """Additional tests for create_commit edge cases."""

    def test_create_commit_failure(self):
        """<R9.23> Returns error on commit creation failure."""
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=False,
                output="Commit failed",
            )

            from cxc.integrations.workflow_ops import create_commit

            issue = MagicMock()
            issue.model_dump_json = MagicMock(return_value='{}')

            logger = MagicMock()
            result, error = create_commit("planner", issue, "/feature", "test1234", logger, "/work")

            assert result is None
            assert error == "Commit failed"


# ----- Test create_pull_request edge cases -----

class TestCreatePullRequestEdgeCases:
    """Additional tests for create_pull_request edge cases."""

    def test_create_pull_request_with_dict_issue(self):
        """<R9.24> Handles dict issue data."""
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="https://github.com/org/repo/pull/42",
            )

            from cxc.integrations.workflow_ops import create_pull_request

            state = MagicMock()
            state.get.side_effect = lambda k: {
                "plan_file": "specs/plan.md",
                "cxc_id": "test1234",
            }.get(k)

            # Pass dict instead of GitHubIssue
            issue_dict = {"number": 42, "title": "Test", "body": "Body"}

            logger = MagicMock()
            result, error = create_pull_request("branch", issue_dict, state, logger, "/work")

            assert "pull/42" in result

    def test_create_pull_request_no_issue(self):
        """<R9.24> Handles None issue."""
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="https://github.com/org/repo/pull/42",
            )

            from cxc.integrations.workflow_ops import create_pull_request

            state = MagicMock()
            state.get.side_effect = lambda k, default=None: {
                "plan_file": None,
                "cxc_id": "test1234",
                "issue": {},
            }.get(k, default)

            logger = MagicMock()
            result, error = create_pull_request("branch", None, state, logger, "/work")

            assert "pull/42" in result

    def test_create_pull_request_failure(self):
        """<R9.24> Returns error on PR creation failure."""
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=False,
                output="PR creation failed",
            )

            from cxc.integrations.workflow_ops import create_pull_request

            state = MagicMock()
            state.get.side_effect = lambda k: {
                "cxc_id": "test1234",
            }.get(k)

            issue = MagicMock()
            issue.model_dump_json = MagicMock(return_value='{}')

            logger = MagicMock()
            result, error = create_pull_request("branch", issue, state, logger, "/work")

            assert result is None
            assert error == "PR creation failed"


# ----- Test ensure_cxc_id edge cases -----

class TestEnsureCxcIdEdgeCases:
    """Additional tests for ensure_cxc_id edge cases."""

    def test_ensure_cxc_id_provided_but_no_state(self):
        """<R9.25> Creates state when CXC ID provided but no state exists."""
        with patch.object(workflow_ops, "CxcState") as mock_state_class:
            mock_state_class.load.return_value = None
            mock_state = MagicMock()
            mock_state_class.return_value = mock_state

            result = workflow_ops.ensure_cxc_id("42", cxc_id="test1234")

            assert result == "test1234"
            mock_state.update.assert_called_with(cxc_id="test1234", issue_number="42")
            mock_state.save.assert_called_once()


# ----- Test find_existing_branch_for_issue edge cases -----

class TestFindExistingBranchForIssueEdgeCases:
    """Additional tests for find_existing_branch_for_issue edge cases."""

    def test_find_existing_branch_git_error(self):
        """<R9.26> Returns None on git error."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stderr="fatal: not a git repository"
            )

            from cxc.integrations.workflow_ops import find_existing_branch_for_issue
            result = find_existing_branch_for_issue("42")

            assert result is None

    def test_find_existing_branch_with_remote(self):
        """<R9.26> Strips remote prefix from branch name."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="  remotes/origin/feature-issue-42-cxc-test1234-feature\n",
            )

            from cxc.integrations.workflow_ops import find_existing_branch_for_issue
            result = find_existing_branch_for_issue("42", "test1234")

            assert result == "feature-issue-42-cxc-test1234-feature"

    def test_find_existing_branch_without_cxc_id(self):
        """<R9.26> Returns first match when no cxc_id specified."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="  feature-issue-42-cxc-abc12345-old\n  feature-issue-42-cxc-xyz67890-new\n",
            )

            from cxc.integrations.workflow_ops import find_existing_branch_for_issue
            result = find_existing_branch_for_issue("42")

            # Should return first match
            assert result == "feature-issue-42-cxc-abc12345-old"

