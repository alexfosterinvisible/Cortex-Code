"""Integration tests for SDLC workflow.

<R12> SDLC Workflow Integration Tests

Tests cover:
- SDLC runs all phases in order
- SDLC stops on plan failure
- SDLC continues on test failure with warning
- SDLC stops on review failure
- CXC ID passed correctly to all phases
"""

import sys
import pytest
from unittest.mock import MagicMock, patch

from cxc.workflows.wt import sdlc_iso as sdlc


# ----- Test SDLC Runs All Phases -----

class TestSdlcRunsAllPhases:
    """Tests for SDLC running all phases in order."""

    def test_sdlc_runs_phases_in_order(self):
        """<R12.1> All phases executed in order."""
        with patch.object(sdlc, "run_workflow_module") as mock_run, \
             patch.object(sdlc, "ensure_cxc_id") as mock_ensure, \
             patch.object(sys, "argv", ["sdlc", "42"]):
            mock_ensure.return_value = "test1234"
            mock_run.return_value = MagicMock(returncode=0)
            
            sdlc.main()
            
            # Verify phases were called in order
            calls = mock_run.call_args_list
            assert len(calls) == 5
            
            # Check order: plan, build, test, review, document
            assert calls[0][0][0] == "plan_iso"
            assert calls[1][0][0] == "build_iso"
            assert calls[2][0][0] == "test_iso"
            assert calls[3][0][0] == "review_iso"
            assert calls[4][0][0] == "document_iso"

    def test_sdlc_passes_issue_and_cxc_id(self):
        """<R12.1> Issue number and CXC ID passed to all phases."""
        with patch.object(sdlc, "run_workflow_module") as mock_run, \
             patch.object(sdlc, "ensure_cxc_id") as mock_ensure, \
             patch.object(sys, "argv", ["sdlc", "99"]):
            mock_ensure.return_value = "abc12345"
            mock_run.return_value = MagicMock(returncode=0)
            
            sdlc.main()
            
            # Verify all phases received correct arguments
            for call_args in mock_run.call_args_list:
                args = call_args[0]
                assert args[1] == "99"  # issue_number
                assert args[2] == "abc12345"  # cxc_id


# ----- Test SDLC Stops on Plan Failure -----

class TestSdlcStopsOnPlanFailure:
    """Tests for SDLC stopping when plan fails."""

    def test_sdlc_stops_on_plan_failure(self):
        """<R12.2> Stops if plan fails."""
        with patch.object(sdlc, "run_workflow_module") as mock_run, \
             patch.object(sdlc, "ensure_cxc_id") as mock_ensure, \
             patch.object(sys, "argv", ["sdlc", "42"]), \
             pytest.raises(SystemExit) as exc_info:
            mock_ensure.return_value = "test1234"
            mock_run.return_value = MagicMock(returncode=1)  # Plan fails
            
            sdlc.main()
        
        assert exc_info.value.code == 1
        
        # Should only have called plan
        assert mock_run.call_count == 1


# ----- Test SDLC Continues on Test Failure -----

class TestSdlcContinuesOnTestFailure:
    """Tests for SDLC continuing when test fails."""

    def test_sdlc_continues_on_test_failure(self, capsys):
        """<R12.3> Continues with warning on test failure."""
        call_count = [0]
        
        def mock_run_side_effect(module, *args, **kwargs):
            call_count[0] += 1
            if module == "test_iso":
                return MagicMock(returncode=1)  # Test fails
            return MagicMock(returncode=0)
        
        with patch.object(sdlc, "run_workflow_module") as mock_run, \
             patch.object(sdlc, "ensure_cxc_id") as mock_ensure, \
             patch.object(sys, "argv", ["sdlc", "42"]):
            mock_ensure.return_value = "test1234"
            mock_run.side_effect = mock_run_side_effect
            
            sdlc.main()
        
        # Should have continued past test to review and document
        assert mock_run.call_count == 5
        
        # Should have printed warning
        captured = capsys.readouterr()
        assert "WARNING" in captured.out or "failed" in captured.out.lower()


# ----- Test SDLC Stops on Review Failure -----

class TestSdlcStopsOnReviewFailure:
    """Tests for SDLC stopping when review fails."""

    def test_sdlc_stops_on_review_failure(self):
        """<R12.4> Stops if review fails."""
        call_count = [0]
        
        def mock_run_side_effect(module, *args, **kwargs):
            call_count[0] += 1
            if module == "review_iso":
                return MagicMock(returncode=1)  # Review fails
            return MagicMock(returncode=0)
        
        with patch.object(sdlc, "run_workflow_module") as mock_run, \
             patch.object(sdlc, "ensure_cxc_id") as mock_ensure, \
             patch.object(sys, "argv", ["sdlc", "42"]), \
             pytest.raises(SystemExit) as exc_info:
            mock_ensure.return_value = "test1234"
            mock_run.side_effect = mock_run_side_effect
            
            sdlc.main()
        
        assert exc_info.value.code == 1
        
        # Should have called plan, build, test, review (but not document)
        assert mock_run.call_count == 4


# ----- Test SDLC Stops on Build Failure -----

class TestSdlcStopsOnBuildFailure:
    """Tests for SDLC stopping when build fails."""

    def test_sdlc_stops_on_build_failure(self):
        """<R12.5> Stops if build fails."""
        call_count = [0]
        
        def mock_run_side_effect(module, *args, **kwargs):
            call_count[0] += 1
            if module == "build_iso":
                return MagicMock(returncode=1)  # Build fails
            return MagicMock(returncode=0)
        
        with patch.object(sdlc, "run_workflow_module") as mock_run, \
             patch.object(sdlc, "ensure_cxc_id") as mock_ensure, \
             patch.object(sys, "argv", ["sdlc", "42"]), \
             pytest.raises(SystemExit) as exc_info:
            mock_ensure.return_value = "test1234"
            mock_run.side_effect = mock_run_side_effect
            
            sdlc.main()
        
        assert exc_info.value.code == 1
        
        # Should have called plan, build (but not test, review, document)
        assert mock_run.call_count == 2


# ----- Test SDLC Flags -----

class TestSdlcFlags:
    """Tests for SDLC flag handling."""

    def test_sdlc_skip_e2e_flag(self):
        """<R12.6> --skip-e2e flag passed to test phase."""
        with patch.object(sdlc, "run_workflow_module") as mock_run, \
             patch.object(sdlc, "ensure_cxc_id") as mock_ensure, \
             patch.object(sys, "argv", ["sdlc", "42", "--skip-e2e"]):
            mock_ensure.return_value = "test1234"
            mock_run.return_value = MagicMock(returncode=0)
            
            sdlc.main()
            
            # Find the test phase call
            test_call = [c for c in mock_run.call_args_list if c[0][0] == "test_iso"][0]
            extra_args = test_call[0][3] if len(test_call[0]) > 3 else []
            
            assert "--skip-e2e" in extra_args

    def test_sdlc_skip_resolution_flag(self):
        """<R12.6> --skip-resolution flag passed to review phase."""
        with patch.object(sdlc, "run_workflow_module") as mock_run, \
             patch.object(sdlc, "ensure_cxc_id") as mock_ensure, \
             patch.object(sys, "argv", ["sdlc", "42", "--skip-resolution"]):
            mock_ensure.return_value = "test1234"
            mock_run.return_value = MagicMock(returncode=0)
            
            sdlc.main()
            
            # Find the review phase call
            review_call = [c for c in mock_run.call_args_list if c[0][0] == "review_iso"][0]
            extra_args = review_call[0][3] if len(review_call[0]) > 3 else []
            
            assert "--skip-resolution" in extra_args

    def test_sdlc_both_flags(self):
        """<R12.6> Both flags passed correctly."""
        with patch.object(sdlc, "run_workflow_module") as mock_run, \
             patch.object(sdlc, "ensure_cxc_id") as mock_ensure, \
             patch.object(sys, "argv", ["sdlc", "42", "--skip-e2e", "--skip-resolution"]):
            mock_ensure.return_value = "test1234"
            mock_run.return_value = MagicMock(returncode=0)
            
            sdlc.main()
            
            # Verify both flags passed to respective phases
            test_call = [c for c in mock_run.call_args_list if c[0][0] == "test_iso"][0]
            review_call = [c for c in mock_run.call_args_list if c[0][0] == "review_iso"][0]
            
            test_args = test_call[0][3] if len(test_call[0]) > 3 else []
            review_args = review_call[0][3] if len(review_call[0]) > 3 else []
            
            assert "--skip-e2e" in test_args
            assert "--skip-resolution" in review_args


# ----- Test SDLC CXC ID Handling -----

class TestSdlcCxcIdHandling:
    """Tests for CXC ID handling in SDLC."""

    def test_sdlc_creates_new_cxc_id(self):
        """<R12.7> Creates new CXC ID when not provided."""
        with patch.object(sdlc, "run_workflow_module") as mock_run, \
             patch.object(sdlc, "ensure_cxc_id") as mock_ensure, \
             patch.object(sys, "argv", ["sdlc", "42"]):
            mock_ensure.return_value = "new12345"
            mock_run.return_value = MagicMock(returncode=0)
            
            sdlc.main()
            
            # ensure_cxc_id should have been called without cxc_id
            mock_ensure.assert_called_once_with("42", None)

    def test_sdlc_uses_provided_cxc_id(self):
        """<R12.7> Uses provided CXC ID."""
        with patch.object(sdlc, "run_workflow_module") as mock_run, \
             patch.object(sdlc, "ensure_cxc_id") as mock_ensure, \
             patch.object(sys, "argv", ["sdlc", "42", "provided123"]):
            mock_ensure.return_value = "provided123"
            mock_run.return_value = MagicMock(returncode=0)
            
            sdlc.main()
            
            # ensure_cxc_id should have been called with provided cxc_id
            mock_ensure.assert_called_once_with("42", "provided123")


# ----- Test SDLC Output -----

class TestSdlcOutput:
    """Tests for SDLC output messages."""

    def test_sdlc_prints_phase_headers(self, capsys):
        """<R12.8> Prints phase headers."""
        with patch.object(sdlc, "run_workflow_module") as mock_run, \
             patch.object(sdlc, "ensure_cxc_id") as mock_ensure, \
             patch.object(sys, "argv", ["sdlc", "42"]):
            mock_ensure.return_value = "test1234"
            mock_run.return_value = MagicMock(returncode=0)
            
            sdlc.main()
        
        captured = capsys.readouterr()
        
        assert "PLAN" in captured.out.upper()
        assert "BUILD" in captured.out.upper()
        assert "TEST" in captured.out.upper()
        assert "REVIEW" in captured.out.upper()
        assert "DOCUMENT" in captured.out.upper()

    def test_sdlc_prints_completion_message(self, capsys):
        """<R12.8> Prints completion message."""
        with patch.object(sdlc, "run_workflow_module") as mock_run, \
             patch.object(sdlc, "ensure_cxc_id") as mock_ensure, \
             patch.object(sys, "argv", ["sdlc", "42"]):
            mock_ensure.return_value = "test1234"
            mock_run.return_value = MagicMock(returncode=0)
            
            sdlc.main()
        
        captured = capsys.readouterr()
        
        assert "COMPLETED" in captured.out.upper() or "completed" in captured.out.lower()

    def test_sdlc_prints_cxc_id(self, capsys):
        """<R12.8> Prints CXC ID."""
        with patch.object(sdlc, "run_workflow_module") as mock_run, \
             patch.object(sdlc, "ensure_cxc_id") as mock_ensure, \
             patch.object(sys, "argv", ["sdlc", "42"]):
            mock_ensure.return_value = "abc12345"
            mock_run.return_value = MagicMock(returncode=0)
            
            sdlc.main()
        
        captured = capsys.readouterr()
        
        assert "abc12345" in captured.out


# ----- Test SDLC Usage -----

class TestSdlcUsage:
    """Tests for SDLC usage message."""

    def test_sdlc_shows_usage_without_args(self, capsys):
        """<R12.9> Shows usage when no arguments."""
        with patch.object(sys, "argv", ["sdlc"]), \
             pytest.raises(SystemExit) as exc_info:
            sdlc.main()
        
        assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert "Usage" in captured.out or "usage" in captured.out.lower()
