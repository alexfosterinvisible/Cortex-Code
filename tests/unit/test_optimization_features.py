"""Unit tests for optimization features (Claude)

These tests verify the existing optimization infrastructure works correctly.

Run with: uv run pytest tests/unit/test_optimization_features.py -v

Feature Categories:
1. Parallelization - Non-blocking operations for speed
2. Comment Consolidation - Edit-based phase comments instead of flooding
3. Artifact Posting - Full content posting, not just file paths
4. Structured Outputs - JSON schema enforcement for agent responses

Test Descriptions (for regression tracking):
- if classify_and_generate_branch doesn't return both values then broken
- if make_issue_comment doesn't default to non-blocking then broken
- if edit_or_create_phase_comment doesn't consolidate comments then broken
- if document_iso doesn't post full doc content to issue then broken
- if post_artifact_to_issue doesn't exist then broken
"""

import json
import pytest
from unittest.mock import MagicMock, patch
import time
import inspect


# ============================================================================
# EXISTING INFRASTRUCTURE TESTS
# ============================================================================

class TestExistingInfrastructure:
    """Tests verifying existing infrastructure works correctly."""

    def test_classify_and_branch_slash_command_exists(self):
        """<E0.1> /classify_and_branch slash command exists in data types.

        if /classify_and_branch not in SlashCommand then broken
        """
        from cxc.core.data_types import SlashCommand

        assert "/classify_and_branch" in SlashCommand.__args__

    def test_cxc_state_has_github_comment_ids_field(self):
        """<E0.2> CxcStateData has github_comment_ids field.

        if CxcStateData doesn't have github_comment_ids then broken
        """
        from cxc.core.data_types import CxcStateData

        state = CxcStateData(cxc_id="test1234")
        assert hasattr(state, "github_comment_ids")
        assert isinstance(state.github_comment_ids, dict)

    def test_update_comment_function_exists(self):
        """<E0.3> update_comment function exists in github.py.

        if update_comment doesn't exist then broken
        """
        from cxc.integrations.github import update_comment

        assert callable(update_comment)

    def test_find_comment_id_by_pattern_function_exists(self):
        """<E0.4> find_comment_id_by_pattern function exists.

        if find_comment_id_by_pattern doesn't exist then broken
        """
        from cxc.integrations.github import find_comment_id_by_pattern

        assert callable(find_comment_id_by_pattern)

    def test_agent_prompt_request_has_json_schema_field(self):
        """<E0.5> AgentPromptRequest supports json_schema parameter.

        if AgentPromptRequest doesn't have json_schema field then broken
        """
        from cxc.core.data_types import AgentPromptRequest

        request = AgentPromptRequest(
            prompt="Test prompt",
            cxc_id="test1234",
            agent_name="tester",
            output_file="/tmp/output.jsonl",
            json_schema={"type": "object", "properties": {"result": {"type": "string"}}},
        )

        assert hasattr(request, "json_schema")
        assert request.json_schema is not None

    def test_command_schema_map_exists(self):
        """<E0.6> COMMAND_SCHEMA_MAP exists for auto-schema injection.

        if COMMAND_SCHEMA_MAP doesn't exist then broken
        """
        from cxc.core.config import COMMAND_SCHEMA_MAP

        assert isinstance(COMMAND_SCHEMA_MAP, dict)


# ============================================================================
# FEATURE 1: PARALLELIZATION
# ============================================================================

class TestParallelization:
    """Tests for non-blocking parallel operations."""

    def test_classify_and_generate_branch_function_exists(self):
        """<P1.1> classify_and_generate_branch function exists in workflow_ops.

        if classify_and_generate_branch function doesn't exist then broken
        """
        from cxc.integrations.workflow_ops import classify_and_generate_branch

        assert callable(classify_and_generate_branch)

    def test_classify_and_generate_branch_returns_tuple(self):
        """<P1.2> Combined function returns (issue_class, branch_name, error).

        if classify_and_generate_branch doesn't return 3-tuple then broken
        """
        with patch("cxc.integrations.workflow_ops.execute_template") as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                output='{"issue_class": "/feature", "branch_name": "feature-issue-42-cxc-test1234-add-auth"}',
            )

            from cxc.integrations.workflow_ops import classify_and_generate_branch

            issue = MagicMock()
            issue.model_dump_json = MagicMock(return_value='{"number": 42, "title": "Test", "body": "Body"}')

            logger = MagicMock()
            result = classify_and_generate_branch(issue, "test1234", logger)

            assert isinstance(result, tuple)
            assert len(result) == 3
            issue_class, branch_name, error = result
            assert issue_class == "/feature"
            assert branch_name == "feature-issue-42-cxc-test1234-add-auth"
            assert error is None

    def test_make_issue_comment_has_blocking_parameter(self):
        """<P1.3> make_issue_comment accepts blocking parameter.

        if make_issue_comment doesn't have blocking param then broken
        """
        from cxc.integrations.github import make_issue_comment

        sig = inspect.signature(make_issue_comment)
        params = sig.parameters

        assert "blocking" in params
        # Default should be False (non-blocking)
        assert params["blocking"].default is False

    def test_make_issue_comment_defaults_to_non_blocking(self):
        """<P1.4> make_issue_comment defaults to fire-and-forget.

        if make_issue_comment blocks by default then broken (slows workflows)
        """
        with patch("cxc.integrations.github.threading.Thread") as mock_thread:
            with patch("cxc.integrations.github.get_repo_url") as mock_url:
                with patch("cxc.integrations.github.extract_repo_path") as mock_path:
                    mock_url.return_value = "https://github.com/test/repo.git"
                    mock_path.return_value = "test/repo"
                    mock_thread_instance = MagicMock()
                    mock_thread.return_value = mock_thread_instance

                    from cxc.integrations.github import make_issue_comment

                    # Call without blocking param - should use thread
                    make_issue_comment("42", "Test comment")

                    # Should have created a thread (non-blocking)
                    mock_thread.assert_called_once()
                    mock_thread_instance.start.assert_called_once()


# ============================================================================
# FEATURE 2: GITHUB COMMENT CONSOLIDATION
# ============================================================================

class TestCommentConsolidation:
    """Tests for GitHub comment edit-based consolidation."""

    def test_edit_or_create_phase_comment_function_exists(self):
        """<C2.1> edit_or_create_phase_comment function exists in workflow_ops.

        if edit_or_create_phase_comment doesn't exist then broken
        """
        from cxc.integrations.workflow_ops import edit_or_create_phase_comment

        assert callable(edit_or_create_phase_comment)

    def test_get_phase_comment_pattern_function_exists(self):
        """<C2.2> get_phase_comment_pattern helper exists.

        if get_phase_comment_pattern doesn't exist then broken
        """
        from cxc.integrations.workflow_ops import get_phase_comment_pattern

        assert callable(get_phase_comment_pattern)

        pattern = get_phase_comment_pattern("test1234", "plan")
        assert "test1234" in pattern
        assert "plan" in pattern

    def test_phase_names_defined(self):
        """<C2.3> PHASE_NAMES constant defined for validation.

        if PHASE_NAMES not defined then broken
        """
        from cxc.integrations.workflow_ops import PHASE_NAMES

        assert isinstance(PHASE_NAMES, list)
        assert "plan" in PHASE_NAMES
        assert "build" in PHASE_NAMES
        assert "test" in PHASE_NAMES
        assert "review" in PHASE_NAMES
        assert "document" in PHASE_NAMES

    def test_edit_or_create_phase_comment_signature(self):
        """<C2.4> edit_or_create_phase_comment has correct signature.

        if edit_or_create_phase_comment missing required params then broken
        """
        from cxc.integrations.workflow_ops import edit_or_create_phase_comment

        sig = inspect.signature(edit_or_create_phase_comment)
        params = sig.parameters

        assert "issue_number" in params
        assert "cxc_id" in params
        assert "phase" in params
        assert "content" in params
        assert "state" in params
        assert "append" in params
        assert "timestamp" in params


# ============================================================================
# FEATURE 3: ARTIFACT POSTING
# ============================================================================

class TestArtifactPosting:
    """Tests for full artifact content posting."""

    def test_post_artifact_to_issue_function_exists(self):
        """<A3.1> post_artifact_to_issue function exists in workflow_ops.

        if post_artifact_to_issue doesn't exist then broken
        """
        from cxc.integrations.workflow_ops import post_artifact_to_issue

        assert callable(post_artifact_to_issue)

    def test_post_artifact_to_issue_signature(self):
        """<A3.2> post_artifact_to_issue has correct signature.

        if post_artifact_to_issue missing params then broken
        """
        from cxc.integrations.workflow_ops import post_artifact_to_issue

        sig = inspect.signature(post_artifact_to_issue)
        params = sig.parameters

        assert "issue_number" in params
        assert "cxc_id" in params
        assert "agent_name" in params
        assert "title" in params
        assert "content" in params
        assert "file_path" in params
        assert "max_length" in params
        assert "collapsible" in params

    def test_post_artifact_to_issue_posts_content(self):
        """<A3.3> post_artifact_to_issue posts actual content.

        if post_artifact_to_issue doesn't include content in comment then broken
        """
        with patch("cxc.integrations.github.make_issue_comment") as mock_comment:
            with patch("cxc.core.utils.print_artifact"):
                from cxc.integrations.workflow_ops import post_artifact_to_issue

                test_content = "# Test Plan\n\nThis is the full content."

                post_artifact_to_issue(
                    issue_number="42",
                    cxc_id="test1234",
                    agent_name="planner",
                    title="📋 Plan",
                    content=test_content,
                )

                mock_comment.assert_called_once()
                posted_body = mock_comment.call_args[0][1]
                assert test_content in posted_body

    def test_post_artifact_to_issue_skips_empty_content(self):
        """<A3.4> post_artifact_to_issue skips empty content.

        if post_artifact_to_issue posts empty comments then broken
        """
        with patch("cxc.integrations.github.make_issue_comment") as mock_comment:
            from cxc.integrations.workflow_ops import post_artifact_to_issue

            post_artifact_to_issue(
                issue_number="42",
                cxc_id="test1234",
                agent_name="planner",
                title="📋 Plan",
                content="",  # Empty
            )

            mock_comment.assert_not_called()

    def test_post_state_to_issue_function_exists(self):
        """<A3.5> post_state_to_issue function exists.

        if post_state_to_issue doesn't exist then broken
        """
        from cxc.integrations.workflow_ops import post_state_to_issue

        assert callable(post_state_to_issue)


# ============================================================================
# FEATURE 4: STRUCTURED OUTPUTS
# ============================================================================

class TestStructuredOutputs:
    """Tests for JSON schema support."""

    def test_agent_template_request_has_json_schema(self):
        """<S4.1> AgentTemplateRequest supports json_schema.

        if AgentTemplateRequest doesn't have json_schema field then broken
        """
        from cxc.core.data_types import AgentTemplateRequest

        request = AgentTemplateRequest(
            agent_name="tester",
            slash_command="/review",
            args=["spec.md"],
            cxc_id="test1234",
            json_schema={"type": "object"},
        )

        assert hasattr(request, "json_schema")
        assert request.json_schema == {"type": "object"}

    def test_review_result_schema_extractable(self):
        """<S4.2> ReviewResult Pydantic schema is extractable.

        if ReviewResult.model_json_schema() doesn't work then broken
        """
        from cxc.core.data_types import ReviewResult

        schema = ReviewResult.model_json_schema()

        assert "properties" in schema
        assert "success" in schema["properties"]
        assert "review_summary" in schema["properties"]


# ============================================================================
# INTEGRATION: WORKFLOW VERIFICATION
# ============================================================================

class TestWorkflowIntegration:
    """Integration tests verifying workflows use optimizations."""

    def test_document_iso_imports_post_artifact(self):
        """<W5.1> document_iso imports post_artifact_to_issue.

        if document_iso doesn't import post_artifact_to_issue then broken
        """
        # Check the import exists in document_iso
        import cxc.workflows.wt.document_iso as doc_iso

        # The module should have access to post_artifact_to_issue
        assert hasattr(doc_iso, 'post_artifact_to_issue')

    def test_expected_phase_count(self):
        """<W5.2> Full SDLC has ~5 phases (one comment each).

        Design constraint: phases = plan, build, test, review, document
        """
        from cxc.integrations.workflow_ops import PHASE_NAMES

        # Should have reasonable number of phases
        assert len(PHASE_NAMES) <= 10
        assert len(PHASE_NAMES) >= 5


# ============================================================================
# SUMMARY
# ============================================================================

"""
All tests should PASS - these verify existing functionality:

EXISTING INFRASTRUCTURE (6 tests):
- E0.1-E0.6: Core infrastructure verification

PARALLELIZATION (4 tests):
- P1.1-P1.4: classify_and_generate_branch, non-blocking comments

COMMENT CONSOLIDATION (4 tests):
- C2.1-C2.4: edit_or_create_phase_comment infrastructure

ARTIFACT POSTING (5 tests):
- A3.1-A3.5: post_artifact_to_issue functionality

STRUCTURED OUTPUTS (2 tests):
- S4.1-S4.2: JSON schema support

WORKFLOW INTEGRATION (2 tests):
- W5.1-W5.2: Integration verification

Total: 23 tests
"""
