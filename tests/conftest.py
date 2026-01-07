"""Shared pytest fixtures for CXC Framework tests.

Provides reusable fixtures for:
- Temporary project directories
- Mocked CXC configuration and state
- Mocked subprocess calls (git, gh, claude)
- Mocked Claude Code responses
"""

import json
import os
import pytest
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import MagicMock, patch


# ----- Temporary Directory Fixtures -----

@pytest.fixture
def tmp_project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory with CXC structure.
    
    Creates:
        tmp_path/
        ├── .cxc.yaml
        ├── .env
        ├── artifacts/
        │   └── test-org/
        │       └── test-repo/
        │           └── trees/
        ├── specs/
        └── commands/
    """
    # Create .cxc.yaml
    cxc_yaml = tmp_path / ".cxc.yaml"
    cxc_yaml.write_text("""
project_id: "test-org/test-repo"
artifacts_dir: "./artifacts"
ports:
  backend_start: 9100
  backend_count: 15
  frontend_start: 9200
  frontend_count: 15
commands:
  - "./commands"
app:
  test_command: "echo test"
""")
    
    # Create .env
    env_file = tmp_path / ".env"
    env_file.write_text("""
ANTHROPIC_API_KEY=test-key
GITHUB_PAT=ghp_test
CLAUDE_CODE_PATH=claude
GITHUB_REPO_URL=https://github.com/test-org/test-repo.git
""")
    
    # Create directories
    (tmp_path / "artifacts" / "test-org" / "test-repo" / "trees").mkdir(parents=True)
    (tmp_path / "specs").mkdir()
    (tmp_path / "commands").mkdir()
    
    return tmp_path


@pytest.fixture
def tmp_cxc_state_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for CXC state files."""
    state_dir = tmp_path / "artifacts" / "test-org" / "test-repo" / "test1234"
    state_dir.mkdir(parents=True)
    return state_dir


# ----- Mock Configuration Fixtures -----

@pytest.fixture
def mock_cxc_config(tmp_project_dir: Path):
    """Create a mock CxcConfig pointing to temp directory."""
    with patch("cxc.core.config.CxcConfig.load") as mock_load:
        from cxc.core.config import CxcConfig, PortConfig, AgentConfig

        config = CxcConfig(
            project_root=tmp_project_dir,
            project_id="test-org/test-repo",
            artifacts_dir=tmp_project_dir / "artifacts",
            ports=PortConfig(),
            agent=AgentConfig(),
            source_root=tmp_project_dir / "src",
            commands=[tmp_project_dir / "commands"],
            app_config={"test_command": "echo test"},
        )
        mock_load.return_value = config
        yield config


@pytest.fixture
def mock_cxc_state(tmp_cxc_state_dir: Path, mock_cxc_config):
    """Create a mock CxcState with test data."""
    from cxc.core.state import CxcState
    
    # Create state with test CXC ID
    state = CxcState("test1234")
    state.update(
        issue_number="42",
        branch_name="feature-issue-42-cxc-test1234-test-feature",
        plan_file="specs/issue-42-cxc-test1234-test-feature.md",
        issue_class="/feature",
        worktree_path=str(tmp_cxc_state_dir.parent / "trees" / "test1234"),
        backend_port=9100,
        frontend_port=9200,
        model_set="base",
    )
    
    return state


# ----- Mock Subprocess Fixtures -----

@pytest.fixture
def mock_subprocess():
    """Mock subprocess.run for git and gh commands.
    
    Returns a mock that can be configured per-test.
    Default behavior returns success for common commands.
    """
    with patch("subprocess.run") as mock_run:
        # Default: return success with empty output
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )
        yield mock_run


@pytest.fixture
def mock_git_commands(mock_subprocess):
    """Configure mock_subprocess for common git commands."""
    def configure_response(cmd_pattern: str, returncode: int = 0, stdout: str = "", stderr: str = ""):
        """Configure response for a specific command pattern."""
        original_side_effect = mock_subprocess.side_effect
        
        def side_effect(cmd, *args, **kwargs):
            cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
            if cmd_pattern in cmd_str:
                return MagicMock(returncode=returncode, stdout=stdout, stderr=stderr)
            if original_side_effect:
                return original_side_effect(cmd, *args, **kwargs)
            return MagicMock(returncode=0, stdout="", stderr="")
        
        mock_subprocess.side_effect = side_effect
    
    # Set up default git responses
    def default_side_effect(cmd, *args, **kwargs):
        cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
        
        if "git remote get-url" in cmd_str:
            return MagicMock(returncode=0, stdout="https://github.com/test-org/test-repo.git\n", stderr="")
        elif "git rev-parse --abbrev-ref HEAD" in cmd_str:
            return MagicMock(returncode=0, stdout="main\n", stderr="")
        elif "git branch" in cmd_str:
            return MagicMock(returncode=0, stdout="* main\n", stderr="")
        elif "git status --porcelain" in cmd_str:
            return MagicMock(returncode=0, stdout="", stderr="")
        elif "git worktree list" in cmd_str:
            return MagicMock(returncode=0, stdout="", stderr="")
        elif "gh issue view" in cmd_str:
            return MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "number": 42,
                    "title": "Test Issue",
                    "body": "Test body",
                    "state": "open",
                    "author": {"login": "testuser"},
                    "assignees": [],
                    "labels": [],
                    "milestone": None,
                    "comments": [],
                    "createdAt": "2025-01-01T00:00:00Z",
                    "updatedAt": "2025-01-01T00:00:00Z",
                    "closedAt": None,
                    "url": "https://github.com/test-org/test-repo/issues/42",
                }),
                stderr="",
            )
        elif "gh pr list" in cmd_str:
            return MagicMock(returncode=0, stdout="[]", stderr="")
        else:
            return MagicMock(returncode=0, stdout="", stderr="")
    
    mock_subprocess.side_effect = default_side_effect
    mock_subprocess.configure_response = configure_response
    
    return mock_subprocess


# ----- Mock Claude Code Fixtures -----

@pytest.fixture
def mock_claude_response():
    """Create mock Claude Code JSONL response data."""
    def create_response(
        result: str = "Test result",
        is_error: bool = False,
        session_id: str = "test-session-123",
    ) -> str:
        """Generate JSONL response content."""
        messages = [
            {"type": "system", "message": "Starting..."},
            {"type": "assistant", "message": {"content": [{"text": "Working..."}]}},
            {
                "type": "result",
                "subtype": "success" if not is_error else "error",
                "is_error": is_error,
                "duration_ms": 1000,
                "duration_api_ms": 800,
                "num_turns": 1,
                "result": result,
                "session_id": session_id,
                "total_cost_usd": 0.01,
            },
        ]
        return "\n".join(json.dumps(msg) for msg in messages)
    
    return create_response


@pytest.fixture
def mock_claude_execution(mock_subprocess, mock_claude_response, tmp_path):
    """Mock Claude Code CLI execution."""
    output_file = tmp_path / "claude_output.jsonl"
    
    def configure_claude(result: str = "Test result", is_error: bool = False):
        """Configure Claude response for next execution."""
        response_content = mock_claude_response(result=result, is_error=is_error)
        
        def side_effect(cmd, *args, **kwargs):
            cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
            
            if "claude" in cmd_str:
                # Write response to output file
                stdout = kwargs.get("stdout")
                if stdout and hasattr(stdout, "write"):
                    stdout.write(response_content)
                else:
                    output_file.write_text(response_content)
                
                return MagicMock(returncode=0 if not is_error else 1, stdout="", stderr="")
            
            return MagicMock(returncode=0, stdout="", stderr="")
        
        mock_subprocess.side_effect = side_effect
    
    configure_claude()  # Set default
    mock_subprocess.configure_claude = configure_claude
    mock_subprocess.output_file = output_file
    
    return mock_subprocess


# ----- GitHub Data Fixtures -----

@pytest.fixture
def sample_github_issue() -> Dict[str, Any]:
    """Sample GitHub issue data matching API response."""
    return {
        "number": 42,
        "title": "Add new feature",
        "body": "## Description\nImplement a new feature that does X.\n\n## Acceptance Criteria\n- [ ] Feature works\n- [ ] Tests pass",
        "state": "open",
        "author": {"login": "testuser", "name": "Test User"},
        "assignees": [],
        "labels": [{"id": "1", "name": "enhancement", "color": "84b6eb"}],
        "milestone": None,
        "comments": [],
        "createdAt": "2025-01-01T00:00:00Z",
        "updatedAt": "2025-01-01T12:00:00Z",
        "closedAt": None,
        "url": "https://github.com/test-org/test-repo/issues/42",
    }


@pytest.fixture
def sample_github_issue_bug() -> Dict[str, Any]:
    """Sample GitHub bug issue data."""
    return {
        "number": 43,
        "title": "Fix broken login",
        "body": "## Bug Description\nLogin fails with error.\n\n## Steps to Reproduce\n1. Go to login\n2. Enter credentials\n3. See error",
        "state": "open",
        "author": {"login": "bugfinder", "name": "Bug Finder"},
        "assignees": [],
        "labels": [{"id": "2", "name": "bug", "color": "d73a4a"}],
        "milestone": None,
        "comments": [],
        "createdAt": "2025-01-02T00:00:00Z",
        "updatedAt": "2025-01-02T12:00:00Z",
        "closedAt": None,
        "url": "https://github.com/test-org/test-repo/issues/43",
    }


# ----- Environment Fixtures -----

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    env_vars = {
        "ANTHROPIC_API_KEY": "sk-ant-test-key",
        "GITHUB_PAT": "ghp_test_token",
        "CLAUDE_CODE_PATH": "claude",
        "GITHUB_REPO_URL": "https://github.com/test-org/test-repo.git",
    }
    
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    return env_vars


@pytest.fixture
def clean_env(monkeypatch):
    """Remove CXC-related environment variables for testing defaults."""
    vars_to_remove = [
        "ANTHROPIC_API_KEY",
        "GITHUB_PAT",
        "CLAUDE_CODE_PATH",
        "GITHUB_REPO_URL",
        "CLOUDFLARE_ACCOUNT_ID",
        "CLOUDFLARE_R2_ACCESS_KEY_ID",
        "CLOUDFLARE_R2_SECRET_ACCESS_KEY",
        "CLOUDFLARE_R2_BUCKET_NAME",
    ]
    
    for var in vars_to_remove:
        monkeypatch.delenv(var, raising=False)


# ----- Utility Fixtures -----

@pytest.fixture
def capture_logs(caplog):
    """Capture log output for assertions."""
    import logging
    caplog.set_level(logging.DEBUG)
    return caplog

