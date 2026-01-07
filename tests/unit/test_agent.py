"""Unit tests for cxc/core/agent.py - <R5> Agent Logic Tests

Tests agent module functions (with mocked subprocess):
- Model selection based on slash command and model_set
- Output truncation
- Claude CLI installation check
- JSONL parsing
- Prompt saving
- Claude Code execution (mocked)
- Retry logic
- Template execution
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import subprocess


class TestSlashCommandModelMap:
    """Tests for SLASH_COMMAND_MODEL_MAP constant."""
    
    def test_all_commands_have_base_mapping(self):
        """<R5.1> All commands have 'base' model mapping."""
        from cxc.core.agent import SLASH_COMMAND_MODEL_MAP
        
        for command, config in SLASH_COMMAND_MODEL_MAP.items():
            assert "base" in config, f"Command {command} missing 'base' mapping"
    
    def test_all_commands_have_heavy_mapping(self):
        """<R5.1b> All commands have 'heavy' model mapping."""
        from cxc.core.agent import SLASH_COMMAND_MODEL_MAP
        
        for command, config in SLASH_COMMAND_MODEL_MAP.items():
            assert "heavy" in config, f"Command {command} missing 'heavy' mapping"
    
    def test_implement_uses_opus_for_both(self):
        """<R5.1c> /implement uses opus for both base and heavy model_set."""
        from cxc.core.agent import SLASH_COMMAND_MODEL_MAP
        
        assert SLASH_COMMAND_MODEL_MAP["/implement"]["heavy"] == "opus"
        assert SLASH_COMMAND_MODEL_MAP["/implement"]["base"] == "opus"
    
    def test_classify_uses_fast_model(self):
        """<R5.1d> /classify_issue uses haiku (fast) for base, sonnet for heavy."""
        from cxc.core.agent import SLASH_COMMAND_MODEL_MAP
        
        assert SLASH_COMMAND_MODEL_MAP["/classify_issue"]["base"] == "haiku"
        assert SLASH_COMMAND_MODEL_MAP["/classify_issue"]["heavy"] == "sonnet"


class TestGetModelForSlashCommand:
    """Tests for get_model_for_slash_command function."""
    
    def test_get_model_base_model_set(self, mock_cxc_config, tmp_path):
        """<R5.2> Returns opus for base model_set on /implement (uses opus for both)."""
        from cxc.core.agent import get_model_for_slash_command
        from cxc.core.data_types import AgentTemplateRequest
        from cxc.core.state import CxcState
        
        mock_cxc_config.artifacts_dir = tmp_path / "artifacts"
        
        # Create state with base model_set
        state = CxcState("test1234")
        state.update(model_set="base")
        state.save("test")
        
        request = AgentTemplateRequest(
            agent_name="test",
            slash_command="/implement",
            args=["plan.md"],
            cxc_id="test1234",
        )
        
        model = get_model_for_slash_command(request)
        
        # /implement uses opus for both base and heavy
        assert model == "opus"
    
    def test_get_model_heavy_model_set(self, mock_cxc_config, tmp_path):
        """<R5.2b> Returns opus for heavy model_set on /implement."""
        from cxc.core.agent import get_model_for_slash_command
        from cxc.core.data_types import AgentTemplateRequest
        from cxc.core.state import CxcState
        
        mock_cxc_config.artifacts_dir = tmp_path / "artifacts"
        
        # Create state with heavy model_set
        state = CxcState("test1234")
        state.update(model_set="heavy")
        state.save("test")
        
        request = AgentTemplateRequest(
            agent_name="test",
            slash_command="/implement",
            args=["plan.md"],
            cxc_id="test1234",
        )
        
        model = get_model_for_slash_command(request)
        
        assert model == "opus"
    
    def test_get_model_no_state_defaults_to_base(self, mock_cxc_config):
        """<R5.2c> Returns base model when no state exists (/implement uses opus for base)."""
        from cxc.core.agent import get_model_for_slash_command
        from cxc.core.data_types import AgentTemplateRequest
        
        request = AgentTemplateRequest(
            agent_name="test",
            slash_command="/implement",
            args=["plan.md"],
            cxc_id="nonexistent",
        )
        
        model = get_model_for_slash_command(request)
        
        # /implement uses opus for both base and heavy
        assert model == "opus"
    
    def test_get_model_unknown_command_returns_default(self, mock_cxc_config):
        """<R5.2d> Returns default for unknown command."""
        from cxc.core.agent import get_model_for_slash_command
        from cxc.core.data_types import AgentTemplateRequest
        
        # Create request with a command not in the map
        # Note: This would fail validation in real use, but we test the fallback
        with patch("cxc.core.agent.SLASH_COMMAND_MODEL_MAP", {}):
            request = AgentTemplateRequest(
                agent_name="test",
                slash_command="/implement",
                args=[],
                cxc_id="test1234",
            )
            
            model = get_model_for_slash_command(request, default="haiku")
            
            assert model == "haiku"


class TestTruncateOutput:
    """Tests for truncate_output function."""
    
    def test_truncate_short_string(self):
        """<R5.3> Short strings unchanged."""
        from cxc.core.agent import truncate_output
        
        short = "Hello, world!"
        result = truncate_output(short)
        
        assert result == short
    
    def test_truncate_long_string(self):
        """<R5.3b> Long strings truncated with suffix."""
        from cxc.core.agent import truncate_output
        
        long_string = "x" * 1000
        result = truncate_output(long_string, max_length=100)
        
        assert len(result) <= 100 + len("... (truncated)")
        assert result.endswith("... (truncated)")
    
    def test_truncate_at_newline(self):
        """<R5.3c> Truncates at newline when possible."""
        from cxc.core.agent import truncate_output
        
        # Create text longer than max_length with newlines near truncation point
        text = "x" * 450 + "\n" + "y" * 100
        result = truncate_output(text, max_length=480)
        
        # Should truncate near a newline
        assert "... (truncated)" in result
    
    def test_truncate_at_space(self):
        """<R5.3d> Truncates at space when no newline."""
        from cxc.core.agent import truncate_output
        
        text = "word " * 100
        result = truncate_output(text, max_length=100)
        
        assert result.endswith("... (truncated)")
    
    def test_truncate_jsonl_extracts_result(self):
        """<R5.3e> JSONL output extracts result message."""
        from cxc.core.agent import truncate_output
        
        jsonl = '{"type": "system"}\n{"type": "result", "result": "The answer is 42"}'
        result = truncate_output(jsonl)
        
        assert "42" in result
    
    def test_truncate_jsonl_extracts_assistant(self):
        """<R5.3f> JSONL output extracts assistant message if no result."""
        from cxc.core.agent import truncate_output
        
        jsonl = '{"type": "system"}\n{"type": "assistant", "message": {"content": [{"text": "Hello from assistant"}]}}'
        result = truncate_output(jsonl)
        
        assert "Hello from assistant" in result
    
    def test_truncate_jsonl_fallback(self):
        """<R5.3g> JSONL output shows message count if can't extract."""
        from cxc.core.agent import truncate_output
        
        jsonl = '{"type": "system"}\n{"type": "other"}\n{"type": "other"}'
        result = truncate_output(jsonl)
        
        assert "JSONL output with 3 messages" in result
    
    def test_truncate_custom_suffix(self):
        """<R5.3h> Custom suffix works."""
        from cxc.core.agent import truncate_output
        
        long_string = "x" * 1000
        result = truncate_output(long_string, max_length=100, suffix="[cut]")
        
        assert result.endswith("[cut]")


class TestCheckClaudeInstalled:
    """Tests for check_claude_installed function."""
    
    def test_check_installed_success(self):
        """<R5.4> Returns None when Claude CLI is installed."""
        from cxc.core.agent import check_claude_installed
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            result = check_claude_installed()
            
            assert result is None
    
    def test_check_installed_not_found(self):
        """<R5.4b> Returns error message when CLI not found."""
        from cxc.core.agent import check_claude_installed
        
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            
            result = check_claude_installed()
            
            assert result is not None
            assert "not installed" in result
    
    def test_check_installed_error_returncode(self):
        """<R5.4c> Returns error message when CLI returns error."""
        from cxc.core.agent import check_claude_installed
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            
            result = check_claude_installed()
            
            assert result is not None
            assert "not installed" in result


class TestParseJsonlOutput:
    """Tests for parse_jsonl_output function."""
    
    def test_parse_extracts_result_message(self, tmp_path):
        """<R5.5> Extracts result message from JSONL."""
        from cxc.core.agent import parse_jsonl_output
        
        jsonl_file = tmp_path / "output.jsonl"
        jsonl_file.write_text(
            '{"type": "system"}\n'
            '{"type": "assistant", "message": {}}\n'
            '{"type": "result", "result": "Success!", "session_id": "abc123"}\n'
        )
        
        messages, result = parse_jsonl_output(str(jsonl_file))
        
        assert len(messages) == 3
        assert result is not None
        assert result["type"] == "result"
        assert result["result"] == "Success!"
    
    def test_parse_empty_file(self, tmp_path):
        """<R5.5b> Returns empty list for empty file."""
        from cxc.core.agent import parse_jsonl_output
        
        jsonl_file = tmp_path / "empty.jsonl"
        jsonl_file.write_text("")
        
        messages, result = parse_jsonl_output(str(jsonl_file))
        
        assert messages == []
        assert result is None
    
    def test_parse_no_result_message(self, tmp_path):
        """<R5.5c> Returns None result when no result message."""
        from cxc.core.agent import parse_jsonl_output
        
        jsonl_file = tmp_path / "no_result.jsonl"
        jsonl_file.write_text('{"type": "system"}\n{"type": "assistant"}\n')
        
        messages, result = parse_jsonl_output(str(jsonl_file))
        
        assert len(messages) == 2
        assert result is None
    
    def test_parse_nonexistent_file(self):
        """<R5.5d> Returns empty for nonexistent file."""
        from cxc.core.agent import parse_jsonl_output
        
        messages, result = parse_jsonl_output("/nonexistent/file.jsonl")
        
        assert messages == []
        assert result is None


class TestConvertJsonlToJson:
    """Tests for convert_jsonl_to_json function."""
    
    def test_convert_creates_json_file(self, tmp_path):
        """<R5.6> Creates valid JSON array file."""
        from cxc.core.agent import convert_jsonl_to_json
        
        jsonl_file = tmp_path / "output.jsonl"
        jsonl_file.write_text('{"type": "a"}\n{"type": "b"}\n')
        
        json_file = convert_jsonl_to_json(str(jsonl_file))
        
        assert json_file == str(tmp_path / "output.json")
        assert Path(json_file).exists()
        
        # Verify content
        with open(json_file) as f:
            data = json.load(f)
        
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["type"] == "a"
    
    def test_convert_replaces_extension(self, tmp_path):
        """<R5.6b> Replaces .jsonl with .json extension."""
        from cxc.core.agent import convert_jsonl_to_json
        
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text('{"x": 1}\n')
        
        json_file = convert_jsonl_to_json(str(jsonl_file))
        
        assert json_file.endswith(".json")
        assert not json_file.endswith(".jsonl")


class TestGetClaudeEnv:
    """Tests for get_claude_env function."""
    
    def test_get_env_returns_dict(self, mock_env_vars):
        """<R5.7> Returns environment dictionary."""
        from cxc.core.agent import get_claude_env
        
        env = get_claude_env()
        
        assert isinstance(env, dict)
    
    def test_get_env_includes_api_key(self, mock_env_vars):
        """<R5.7b> Includes ANTHROPIC_API_KEY."""
        from cxc.core.agent import get_claude_env
        
        env = get_claude_env()
        
        assert "ANTHROPIC_API_KEY" in env
    
    def test_get_env_includes_path(self, mock_env_vars):
        """<R5.7c> Includes PATH."""
        from cxc.core.agent import get_claude_env
        
        env = get_claude_env()
        
        assert "PATH" in env


class TestSavePrompt:
    """Tests for save_prompt function."""
    
    def test_save_prompt_creates_file(self, mock_cxc_config, tmp_path):
        """<R5.8> Saves prompt to correct location."""
        from cxc.core.agent import save_prompt
        
        mock_cxc_config.artifacts_dir = tmp_path / "artifacts"
        
        save_prompt("/implement plan.md", "test1234", "planner")
        
        prompt_file = (
            tmp_path / "artifacts" / "test-org" / "test-repo" / "test1234" 
            / "planner" / "prompts" / "implement.txt"
        )
        
        assert prompt_file.exists()
        assert prompt_file.read_text() == "/implement plan.md"
    
    def test_save_prompt_extracts_command_name(self, mock_cxc_config, tmp_path):
        """<R5.8b> Extracts command name for filename."""
        from cxc.core.agent import save_prompt
        
        mock_cxc_config.artifacts_dir = tmp_path / "artifacts"
        
        save_prompt("/classify_issue {json}", "test1234", "classifier")
        
        prompt_file = (
            tmp_path / "artifacts" / "test-org" / "test-repo" / "test1234"
            / "classifier" / "prompts" / "classify_issue.txt"
        )
        
        assert prompt_file.exists()
    
    def test_save_prompt_no_slash_command(self, mock_cxc_config, tmp_path):
        """<R5.8c> Does nothing if no slash command."""
        from cxc.core.agent import save_prompt
        
        mock_cxc_config.artifacts_dir = tmp_path / "artifacts"
        
        # Should not raise, just return early
        save_prompt("plain text without slash", "test1234", "ops")
        
        # No file should be created
        prompts_dir = (
            tmp_path / "artifacts" / "test-org" / "test-repo" / "test1234" 
            / "ops" / "prompts"
        )
        assert not prompts_dir.exists()


@pytest.mark.requires_api
class TestPromptClaudeCode:
    """Tests for prompt_claude_code function.

    NOTE: These tests mock subprocess.Popen to simulate streaming JSONL output.
    """

    def test_prompt_success(self, mock_cxc_config, tmp_path, mock_env_vars):
        """<R5.9> Successful execution returns response."""
        from cxc.core.agent import prompt_claude_code
        from cxc.core.data_types import AgentPromptRequest

        mock_cxc_config.artifacts_dir = tmp_path / "artifacts"
        output_file = tmp_path / "output.jsonl"

        # Create mock JSONL response
        jsonl_lines = [
            '{"type": "system"}\n',
            '{"type": "result", "result": "Test success", "session_id": "sess123", "is_error": false}\n'
        ]

        # Create mock process with streaming stdout
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = iter(jsonl_lines)
        mock_process.stderr.read.return_value = ""
        mock_process.wait.return_value = None

        with patch("subprocess.Popen", return_value=mock_process):
            with patch("cxc.core.agent.check_claude_installed", return_value=None):
                request = AgentPromptRequest(
                    prompt="/test prompt",
                    cxc_id="test1234",
                    agent_name="test",
                    output_file=str(output_file),
                )

                response = prompt_claude_code(request)

        assert response.success is True
        assert response.output == "Test success"
        assert response.session_id == "sess123"
    
    def test_prompt_claude_not_installed(self, mock_cxc_config, tmp_path):
        """<R5.9b> Returns error when Claude not installed."""
        from cxc.core.agent import prompt_claude_code
        from cxc.core.data_types import AgentPromptRequest, RetryCode
        
        with patch("cxc.core.agent.check_claude_installed", return_value="Not installed"):
            request = AgentPromptRequest(
                prompt="/test",
                cxc_id="test1234",
                agent_name="test",
                output_file=str(tmp_path / "output.jsonl"),
            )
            
            response = prompt_claude_code(request)
        
        assert response.success is False
        assert "Not installed" in response.output
        assert response.retry_code == RetryCode.NONE
    
    def test_prompt_error_returncode(self, mock_cxc_config, tmp_path, mock_env_vars):
        """<R5.9c> Returns error for non-zero return code."""
        from cxc.core.agent import prompt_claude_code
        from cxc.core.data_types import AgentPromptRequest, RetryCode

        mock_cxc_config.artifacts_dir = tmp_path / "artifacts"
        output_file = tmp_path / "output.jsonl"

        # Create mock process that returns error
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stdout = iter(['{"type": "system"}\n'])
        mock_process.stderr.read.return_value = "Error occurred"
        mock_process.wait.return_value = None

        with patch("subprocess.Popen", return_value=mock_process):
            with patch("cxc.core.agent.check_claude_installed", return_value=None):
                request = AgentPromptRequest(
                    prompt="/test",
                    cxc_id="test1234",
                    agent_name="test",
                    output_file=str(output_file),
                )

                response = prompt_claude_code(request)

        assert response.success is False
        assert response.retry_code == RetryCode.CLAUDE_CODE_ERROR
    
    def test_prompt_timeout(self, mock_cxc_config, tmp_path, mock_env_vars):
        """<R5.9d> Returns timeout error."""
        from cxc.core.agent import prompt_claude_code
        from cxc.core.data_types import AgentPromptRequest, RetryCode

        mock_cxc_config.artifacts_dir = tmp_path / "artifacts"

        with patch("subprocess.Popen") as mock_popen:
            mock_popen.side_effect = subprocess.TimeoutExpired("claude", 300)

            with patch("cxc.core.agent.check_claude_installed", return_value=None):
                request = AgentPromptRequest(
                    prompt="/test",
                    cxc_id="test1234",
                    agent_name="test",
                    output_file=str(tmp_path / "output.jsonl"),
                )

                response = prompt_claude_code(request)

        assert response.success is False
        assert "timed out" in response.output
        assert response.retry_code == RetryCode.TIMEOUT_ERROR

    def test_prompt_execution_error(self, mock_cxc_config, tmp_path, mock_env_vars):
        """<R5.9e> Returns execution error for exceptions."""
        from cxc.core.agent import prompt_claude_code
        from cxc.core.data_types import AgentPromptRequest, RetryCode

        mock_cxc_config.artifacts_dir = tmp_path / "artifacts"

        with patch("subprocess.Popen") as mock_popen:
            mock_popen.side_effect = Exception("Unexpected error")

            with patch("cxc.core.agent.check_claude_installed", return_value=None):
                request = AgentPromptRequest(
                    prompt="/test",
                    cxc_id="test1234",
                    agent_name="test",
                    output_file=str(tmp_path / "output.jsonl"),
                )

                response = prompt_claude_code(request)

        assert response.success is False
        assert "Unexpected error" in response.output
        assert response.retry_code == RetryCode.EXECUTION_ERROR

    def test_prompt_error_during_execution(self, mock_cxc_config, tmp_path, mock_env_vars):
        """<R5.9f> Handles error_during_execution subtype."""
        from cxc.core.agent import prompt_claude_code
        from cxc.core.data_types import AgentPromptRequest, RetryCode

        mock_cxc_config.artifacts_dir = tmp_path / "artifacts"
        output_file = tmp_path / "output.jsonl"

        # Create JSONL lines with error_during_execution
        jsonl_lines = [
            '{"type": "system"}\n',
            '{"type": "result", "subtype": "error_during_execution", "session_id": "sess123", "is_error": true}\n'
        ]

        # Create mock process with streaming stdout
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = iter(jsonl_lines)
        mock_process.stderr.read.return_value = ""
        mock_process.wait.return_value = None

        with patch("subprocess.Popen", return_value=mock_process):
            with patch("cxc.core.agent.check_claude_installed", return_value=None):
                request = AgentPromptRequest(
                    prompt="/test",
                    cxc_id="test1234",
                    agent_name="test",
                    output_file=str(output_file),
                )

                response = prompt_claude_code(request)

        assert response.success is False
        assert response.retry_code == RetryCode.ERROR_DURING_EXECUTION


class TestPromptClaudeCodeWithRetry:
    """Tests for prompt_claude_code_with_retry function."""
    
    def test_retry_success_first_attempt(self, mock_cxc_config, tmp_path, mock_env_vars):
        """<R5.10> Returns immediately on first success."""
        from cxc.core.agent import prompt_claude_code_with_retry
        from cxc.core.data_types import AgentPromptRequest, AgentPromptResponse, RetryCode
        
        mock_cxc_config.artifacts_dir = tmp_path / "artifacts"
        
        success_response = AgentPromptResponse(
            output="Success",
            success=True,
            retry_code=RetryCode.NONE,
        )
        
        with patch("cxc.core.agent.prompt_claude_code", return_value=success_response) as mock_prompt:
            request = AgentPromptRequest(
                prompt="/test",
                cxc_id="test1234",
                agent_name="test",
                output_file=str(tmp_path / "output.jsonl"),
            )
            
            response = prompt_claude_code_with_retry(request, max_retries=3)
        
        assert response.success is True
        assert mock_prompt.call_count == 1
    
    def test_retry_on_error(self, mock_cxc_config, tmp_path, mock_env_vars):
        """<R5.10b> Retries on retryable errors."""
        from cxc.core.agent import prompt_claude_code_with_retry
        from cxc.core.data_types import AgentPromptRequest, AgentPromptResponse, RetryCode
        
        mock_cxc_config.artifacts_dir = tmp_path / "artifacts"
        
        error_response = AgentPromptResponse(
            output="Error",
            success=False,
            retry_code=RetryCode.CLAUDE_CODE_ERROR,
        )
        success_response = AgentPromptResponse(
            output="Success",
            success=True,
            retry_code=RetryCode.NONE,
        )
        
        # First call fails, second succeeds
        with patch("cxc.core.agent.prompt_claude_code", side_effect=[error_response, success_response]) as mock_prompt:
            with patch("time.sleep"):  # Skip actual delays
                request = AgentPromptRequest(
                    prompt="/test",
                    cxc_id="test1234",
                    agent_name="test",
                    output_file=str(tmp_path / "output.jsonl"),
                )
                
                response = prompt_claude_code_with_retry(request, max_retries=3, retry_delays=[0, 0, 0])
        
        assert response.success is True
        assert mock_prompt.call_count == 2
    
    def test_retry_exhausted(self, mock_cxc_config, tmp_path, mock_env_vars):
        """<R5.10c> Returns last error after max retries."""
        from cxc.core.agent import prompt_claude_code_with_retry
        from cxc.core.data_types import AgentPromptRequest, AgentPromptResponse, RetryCode
        
        mock_cxc_config.artifacts_dir = tmp_path / "artifacts"
        
        error_response = AgentPromptResponse(
            output="Persistent error",
            success=False,
            retry_code=RetryCode.TIMEOUT_ERROR,
        )
        
        with patch("cxc.core.agent.prompt_claude_code", return_value=error_response) as mock_prompt:
            with patch("time.sleep"):
                request = AgentPromptRequest(
                    prompt="/test",
                    cxc_id="test1234",
                    agent_name="test",
                    output_file=str(tmp_path / "output.jsonl"),
                )
                
                response = prompt_claude_code_with_retry(request, max_retries=2, retry_delays=[0, 0])
        
        assert response.success is False
        assert "Persistent error" in response.output
        # Initial attempt + 2 retries = 3 calls
        assert mock_prompt.call_count == 3
    
    def test_retry_non_retryable_error(self, mock_cxc_config, tmp_path, mock_env_vars):
        """<R5.10d> Does not retry non-retryable errors."""
        from cxc.core.agent import prompt_claude_code_with_retry
        from cxc.core.data_types import AgentPromptRequest, AgentPromptResponse, RetryCode
        
        mock_cxc_config.artifacts_dir = tmp_path / "artifacts"
        
        # NONE retry code means non-retryable
        error_response = AgentPromptResponse(
            output="Non-retryable error",
            success=False,
            retry_code=RetryCode.NONE,
        )
        
        with patch("cxc.core.agent.prompt_claude_code", return_value=error_response) as mock_prompt:
            request = AgentPromptRequest(
                prompt="/test",
                cxc_id="test1234",
                agent_name="test",
                output_file=str(tmp_path / "output.jsonl"),
            )
            
            response = prompt_claude_code_with_retry(request, max_retries=3)
        
        assert response.success is False
        assert mock_prompt.call_count == 1  # No retries
    
    def test_retry_delays_extended(self, mock_cxc_config, tmp_path, mock_env_vars):
        """<R5.10e> Extends retry_delays if too short."""
        from cxc.core.agent import prompt_claude_code_with_retry
        from cxc.core.data_types import AgentPromptRequest, AgentPromptResponse, RetryCode
        
        mock_cxc_config.artifacts_dir = tmp_path / "artifacts"
        
        error_response = AgentPromptResponse(
            output="Error",
            success=False,
            retry_code=RetryCode.EXECUTION_ERROR,
        )
        
        delays_used = []
        
        def track_sleep(delay):
            delays_used.append(delay)
        
        with patch("cxc.core.agent.prompt_claude_code", return_value=error_response):
            with patch("time.sleep", side_effect=track_sleep):
                request = AgentPromptRequest(
                    prompt="/test",
                    cxc_id="test1234",
                    agent_name="test",
                    output_file=str(tmp_path / "output.jsonl"),
                )
                
                # Provide only 1 delay but max_retries=3
                prompt_claude_code_with_retry(request, max_retries=3, retry_delays=[1])
        
        # Should have extended delays: [1, 3, 5] (adding +2 each time)
        assert len(delays_used) == 3


class TestExecuteTemplate:
    """Tests for execute_template function."""
    
    def test_execute_builds_prompt(self, mock_cxc_config, tmp_path, mock_env_vars):
        """<R5.11> Constructs prompt from slash command and args."""
        from cxc.core.agent import execute_template
        from cxc.core.data_types import AgentTemplateRequest, AgentPromptResponse, RetryCode
        
        mock_cxc_config.artifacts_dir = tmp_path / "artifacts"
        
        captured_request = None
        
        def capture_request(req):
            nonlocal captured_request
            captured_request = req
            return AgentPromptResponse(
                output="Success",
                success=True,
                retry_code=RetryCode.NONE,
            )
        
        with patch("cxc.core.agent.prompt_claude_code_with_retry", side_effect=capture_request):
            request = AgentTemplateRequest(
                agent_name="planner",
                slash_command="/implement",
                args=["plan.md", "extra_arg"],
                cxc_id="test1234",
            )
            
            execute_template(request)
        
        assert captured_request is not None
        assert captured_request.prompt == "/implement plan.md extra_arg"
    
    def test_execute_selects_model(self, mock_cxc_config, tmp_path, mock_env_vars):
        """<R5.11b> Selects model based on model_set."""
        from cxc.core.agent import execute_template
        from cxc.core.data_types import AgentTemplateRequest, AgentPromptResponse, RetryCode
        from cxc.core.state import CxcState
        
        mock_cxc_config.artifacts_dir = tmp_path / "artifacts"
        
        # Create state with heavy model_set
        state = CxcState("test1234")
        state.update(model_set="heavy")
        state.save("test")
        
        captured_request = None
        
        def capture_request(req):
            nonlocal captured_request
            captured_request = req
            return AgentPromptResponse(
                output="Success",
                success=True,
                retry_code=RetryCode.NONE,
            )
        
        with patch("cxc.core.agent.prompt_claude_code_with_retry", side_effect=capture_request):
            request = AgentTemplateRequest(
                agent_name="implementor",
                slash_command="/implement",
                args=["plan.md"],
                cxc_id="test1234",
            )
            
            execute_template(request)
        
        assert captured_request is not None
        assert captured_request.model == "opus"  # Heavy uses opus for /implement
    
    def test_execute_creates_output_dir(self, mock_cxc_config, tmp_path, mock_env_vars):
        """<R5.11c> Creates output directory."""
        from cxc.core.agent import execute_template
        from cxc.core.data_types import AgentTemplateRequest, AgentPromptResponse, RetryCode
        
        mock_cxc_config.artifacts_dir = tmp_path / "artifacts"
        
        with patch("cxc.core.agent.prompt_claude_code_with_retry") as mock_prompt:
            mock_prompt.return_value = AgentPromptResponse(
                output="Success",
                success=True,
                retry_code=RetryCode.NONE,
            )
            
            request = AgentTemplateRequest(
                agent_name="test_agent",
                slash_command="/test",
                args=[],
                cxc_id="test1234",
            )
            
            execute_template(request)
        
        output_dir = tmp_path / "artifacts" / "test-org" / "test-repo" / "test1234" / "test_agent"
        assert output_dir.exists()
    
    def test_execute_passes_working_dir(self, mock_cxc_config, tmp_path, mock_env_vars):
        """<R5.11d> Passes working_dir to prompt request."""
        from cxc.core.agent import execute_template
        from cxc.core.data_types import AgentTemplateRequest, AgentPromptResponse, RetryCode
        
        mock_cxc_config.artifacts_dir = tmp_path / "artifacts"
        
        captured_request = None
        
        def capture_request(req):
            nonlocal captured_request
            captured_request = req
            return AgentPromptResponse(
                output="Success",
                success=True,
                retry_code=RetryCode.NONE,
            )
        
        with patch("cxc.core.agent.prompt_claude_code_with_retry", side_effect=capture_request):
            request = AgentTemplateRequest(
                agent_name="test",
                slash_command="/test",
                args=[],
                cxc_id="test1234",
                working_dir="/custom/path",
            )
            
            execute_template(request)
        
        assert captured_request.working_dir == "/custom/path"
    
    def test_execute_sets_skip_permissions(self, mock_cxc_config, tmp_path, mock_env_vars):
        """<R5.11e> Sets dangerously_skip_permissions to True."""
        from cxc.core.agent import execute_template
        from cxc.core.data_types import AgentTemplateRequest, AgentPromptResponse, RetryCode
        
        mock_cxc_config.artifacts_dir = tmp_path / "artifacts"
        
        captured_request = None
        
        def capture_request(req):
            nonlocal captured_request
            captured_request = req
            return AgentPromptResponse(
                output="Success",
                success=True,
                retry_code=RetryCode.NONE,
            )
        
        with patch("cxc.core.agent.prompt_claude_code_with_retry", side_effect=capture_request):
            request = AgentTemplateRequest(
                agent_name="test",
                slash_command="/test",
                args=[],
                cxc_id="test1234",
            )
            
            execute_template(request)
        
        assert captured_request.dangerously_skip_permissions is True

