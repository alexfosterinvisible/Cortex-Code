"""Integration tests for plan workflow.

<R11> Plan Workflow Integration Tests

Tests cover:
- Plan workflow happy path
- Worktree creation
- Issue classification
- Branch name generation
- Plan file creation
- Commit and push operations
- PR creation
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, call


# ----- Test Plan Workflow Happy Path -----

class TestPlanWorkflowHappyPath:
    """Tests for complete plan workflow execution."""

    @pytest.fixture
    def mock_workflow_deps(self, tmp_path):
        """Set up all mocks for plan workflow."""
        with patch("cxc.core.config.CxcConfig.load") as mock_config, \
             patch("subprocess.run") as mock_subprocess, \
             patch("cxc.integrations.github.get_repo_url") as mock_url, \
             patch("cxc.integrations.github.extract_repo_path") as mock_path, \
             patch("cxc.integrations.github.fetch_issue") as mock_fetch, \
             patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            
            from cxc.core.config import CxcConfig, PortConfig
            
            config = CxcConfig(
                project_root=tmp_path,
                project_id="test-org/test-repo",
                artifacts_dir=tmp_path / "artifacts",
                ports=PortConfig(),
                source_root=tmp_path / "src",
                commands=[tmp_path / "commands"],
                app_config={},
            )
            mock_config.return_value = config
            
            mock_url.return_value = "https://github.com/test-org/test-repo.git"
            mock_path.return_value = "test-org/test-repo"
            
            # Create mock issue
            mock_issue = MagicMock()
            mock_issue.number = 42
            mock_issue.title = "Add new feature"
            mock_issue.body = "Implement X"
            mock_issue.model_dump_json = MagicMock(return_value='{"number": 42, "title": "Add new feature", "body": "Implement X"}')
            mock_fetch.return_value = mock_issue
            
            # Default subprocess responses
            def subprocess_side_effect(cmd, *args, **kwargs):
                cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
                
                if "git remote get-url" in cmd_str:
                    return MagicMock(returncode=0, stdout="https://github.com/test-org/test-repo.git\n")
                elif "git fetch" in cmd_str:
                    return MagicMock(returncode=0, stdout="", stderr="")
                elif "git remote show" in cmd_str:
                    return MagicMock(returncode=0, stdout="HEAD branch: main\n")
                elif "git worktree add" in cmd_str:
                    return MagicMock(returncode=0, stdout="", stderr="")
                elif "git worktree list" in cmd_str:
                    return MagicMock(returncode=0, stdout=str(tmp_path / "trees" / "test1234"))
                elif "git checkout" in cmd_str:
                    return MagicMock(returncode=0, stdout="", stderr="")
                elif "git add" in cmd_str:
                    return MagicMock(returncode=0, stdout="", stderr="")
                elif "git commit" in cmd_str:
                    return MagicMock(returncode=0, stdout="", stderr="")
                elif "git push" in cmd_str:
                    return MagicMock(returncode=0, stdout="", stderr="")
                elif "git status" in cmd_str:
                    return MagicMock(returncode=0, stdout="M file.py\n", stderr="")
                elif "gh pr list" in cmd_str:
                    return MagicMock(returncode=0, stdout="[]", stderr="")
                elif "gh pr create" in cmd_str:
                    return MagicMock(returncode=0, stdout="https://github.com/test-org/test-repo/pull/1", stderr="")
                else:
                    return MagicMock(returncode=0, stdout="", stderr="")
            
            mock_subprocess.side_effect = subprocess_side_effect
            
            # Default execute_template responses
            def execute_side_effect(request):
                if "/classify_issue" in request.slash_command:
                    return MagicMock(success=True, output="/feature")
                elif "/generate_branch_name" in request.slash_command:
                    return MagicMock(success=True, output="feature-issue-42-cxc-test1234-add-feature")
                elif "/feature" in request.slash_command or "/bug" in request.slash_command:
                    return MagicMock(success=True, output="specs/issue-42-plan.md")
                elif "/commit" in request.slash_command:
                    return MagicMock(success=True, output="feat: Add new feature")
                elif "/pull_request" in request.slash_command:
                    return MagicMock(success=True, output="https://github.com/test-org/test-repo/pull/1")
                else:
                    return MagicMock(success=True, output="OK")
            
            mock_execute.side_effect = execute_side_effect
            
            yield {
                "config": mock_config,
                "subprocess": mock_subprocess,
                "url": mock_url,
                "path": mock_path,
                "fetch": mock_fetch,
                "execute": mock_execute,
                "issue": mock_issue,
                "tmp_path": tmp_path,
            }

    def test_plan_workflow_creates_state(self, mock_workflow_deps):
        """<R11.1> Plan workflow creates CXC state."""
        from cxc.core.state import CxcState
        
        # Create state as plan workflow would
        state = CxcState("test1234")
        state.update(
            issue_number="42",
            issue_class="/feature",
            branch_name="feature-issue-42-cxc-test1234-add-feature",
        )
        state.save("plan_test")
        
        # Verify state was created
        loaded = CxcState.load("test1234")
        assert loaded is not None
        assert loaded.get("issue_number") == "42"

    def test_plan_workflow_classifies_issue(self, mock_workflow_deps):
        """<R11.2> Issue classified correctly."""
        from cxc.integrations.workflow_ops import classify_issue
        
        issue = mock_workflow_deps["issue"]
        logger = MagicMock()
        
        result, error = classify_issue(issue, "test1234", logger)
        
        assert result == "/feature"
        assert error is None

    def test_plan_workflow_generates_branch(self, mock_workflow_deps):
        """<R11.3> Branch name generated correctly."""
        from cxc.integrations.workflow_ops import generate_branch_name
        
        issue = mock_workflow_deps["issue"]
        logger = MagicMock()
        
        result, error = generate_branch_name(issue, "/feature", "test1234", logger)
        
        assert "feature" in result
        assert "42" in result
        assert error is None


# ----- Test Worktree Creation -----

class TestWorktreeCreation:
    """Tests for worktree creation in plan workflow."""

    def test_create_worktree_success(self, tmp_path):
        """<R11.4> Worktree created correctly."""
        with patch("cxc.integrations.worktree_ops.CxcConfig") as mock_config, \
             patch("subprocess.run") as mock_run, \
             patch("cxc.integrations.worktree_ops.get_default_branch") as mock_branch:
            
            config = MagicMock()
            config.project_root = tmp_path
            config.get_trees_dir.return_value = tmp_path / "trees"
            mock_config.load.return_value = config
            
            mock_branch.return_value = "main"
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            from cxc.integrations.worktree_ops import create_worktree
            
            logger = MagicMock()
            path, error = create_worktree("test1234", "feature-branch", logger)
            
            assert path is not None
            assert "test1234" in path
            assert error is None

    def test_worktree_ports_allocated(self, tmp_path):
        """<R11.4> Ports allocated for worktree."""
        from cxc.integrations.worktree_ops import get_ports_for_cxc
        
        backend, frontend = get_ports_for_cxc("test1234")
        
        assert 9100 <= backend <= 9114
        assert 9200 <= frontend <= 9214


# ----- Test Plan File Creation -----

class TestPlanFileCreation:
    """Tests for plan file creation."""

    def test_build_plan_returns_path(self):
        """<R11.5> Plan file path returned."""
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="specs/issue-42-plan.md",
            )
            
            from cxc.integrations.workflow_ops import build_plan
            
            issue = MagicMock()
            issue.number = 42
            issue.model_dump_json = MagicMock(return_value='{}')
            
            logger = MagicMock()
            result = build_plan(issue, "/feature", "test1234", logger)
            
            assert result.success is True
            assert "specs/" in result.output


# ----- Test Git Operations -----

class TestPlanGitOperations:
    """Tests for git operations in plan workflow."""

    def test_commit_plan(self):
        """<R11.6> Plan committed to branch."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="M specs/plan.md\n", stderr=""),  # status
                MagicMock(returncode=0, stdout="", stderr=""),  # add
                MagicMock(returncode=0, stdout="", stderr=""),  # commit
            ]
            
            from cxc.integrations.git_ops import commit_changes
            
            success, error = commit_changes("feat: Add plan for issue #42")
            
            assert success is True
            assert error is None

    def test_push_branch(self):
        """<R11.6> Branch pushed to remote."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            from cxc.integrations.git_ops import push_branch
            
            success, error = push_branch("feature-issue-42-branch")
            
            assert success is True
            assert error is None


# ----- Test PR Creation -----

class TestPlanPrCreation:
    """Tests for PR creation in plan workflow."""

    def test_create_pr_success(self):
        """<R11.7> PR created successfully."""
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output="https://github.com/test-org/test-repo/pull/1",
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
            result, error = create_pull_request("feature-branch", issue, state, logger, "/work")
            
            assert "pull/1" in result
            assert error is None


# ----- Test Full Plan Flow -----

class TestFullPlanFlow:
    """Tests for complete plan workflow flow."""

    def test_plan_flow_state_accumulation(self, tmp_path):
        """<R11.8> State accumulates through plan phases."""
        with patch("cxc.core.config.CxcConfig.load") as mock_config:
            from cxc.core.config import CxcConfig, PortConfig
            
            config = CxcConfig(
                project_root=tmp_path,
                project_id="test-org/test-repo",
                artifacts_dir=tmp_path / "artifacts",
                ports=PortConfig(),
                source_root=tmp_path / "src",
                commands=[],
                app_config={},
            )
            mock_config.return_value = config
            
            from cxc.core.state import CxcState
            
            # Simulate plan workflow phases
            state = CxcState("planflow123")
            
            # Phase 1: Initialize
            state.update(issue_number="42")
            state.save("init")
            
            # Phase 2: Classify
            state.update(issue_class="/feature")
            state.save("classify")
            
            # Phase 3: Create branch
            state.update(branch_name="feature-issue-42-branch")
            state.save("branch")
            
            # Phase 4: Create worktree
            state.update(
                worktree_path=str(tmp_path / "trees" / "planflow123"),
                backend_port=9100,
                frontend_port=9200,
            )
            state.save("worktree")
            
            # Phase 5: Build plan
            state.update(plan_file="specs/issue-42-plan.md")
            state.save("plan")
            
            # Phase 6: Mark complete
            state.append_cxc_id("cxc_plan_iso")
            state.save("complete")
            
            # Verify final state
            final = CxcState.load("planflow123")
            assert final.get("issue_number") == "42"
            assert final.get("issue_class") == "/feature"
            assert final.get("branch_name") == "feature-issue-42-branch"
            assert final.get("worktree_path") is not None
            assert final.get("plan_file") == "specs/issue-42-plan.md"
            assert "cxc_plan_iso" in final.get("all_cxcs", [])

