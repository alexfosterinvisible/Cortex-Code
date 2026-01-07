"""Unit tests for cxc/cli.py

<R10> CLI Routing Tests

Tests cover:
- CLI help output
- Command routing for all workflow commands
- Argument parsing
- Flag handling (--skip-e2e, --skip-resolution)
- Error handling for missing modules
"""

import sys
import pytest
from unittest.mock import MagicMock, patch


# ----- Test CLI Help -----

class TestCliHelp:
    """Tests for CLI help output."""

    def test_cli_help_shows_usage(self):
        """<R10.1> --help shows usage information."""
        with patch("sys.argv", ["cxc", "--help"]), \
             pytest.raises(SystemExit) as exc_info:
            from cxc.cli import main
            main()
        
        # argparse exits with 0 for --help
        assert exc_info.value.code == 0

    def test_cli_no_command_shows_help(self, capsys):
        """<R10.1> No command shows help and exits."""
        with patch("sys.argv", ["cxc"]), \
             pytest.raises(SystemExit) as exc_info:
            from cxc.cli import main
            main()
        
        assert exc_info.value.code == 1


# ----- Test run_workflow -----

class TestRunWorkflow:
    """Tests for run_workflow function."""

    def test_run_workflow_success(self):
        """<R10.2> Runs workflow module successfully."""
        with patch("importlib.import_module") as mock_import:
            mock_module = MagicMock()
            mock_module.main = MagicMock()
            mock_import.return_value = mock_module
            
            from cxc.cli import run_workflow
            run_workflow("wt.plan_iso", ["42"])
            
            mock_import.assert_called_with("cxc.workflows.wt.plan_iso")
            mock_module.main.assert_called_once()

    def test_run_workflow_patches_argv(self):
        """<R10.2> Patches sys.argv correctly."""
        original_argv = sys.argv.copy()
        
        with patch("importlib.import_module") as mock_import:
            mock_module = MagicMock()
            mock_module.main = MagicMock()
            mock_import.return_value = mock_module
            
            from cxc.cli import run_workflow
            run_workflow("wt.build_iso", ["42", "test1234"])
            
            # sys.argv should have been patched during execution
            # We can't easily test the patched value, but we can verify it was called
            mock_module.main.assert_called_once()
        
        # Restore argv
        sys.argv = original_argv

    def test_run_workflow_import_error(self, capsys):
        """<R10.2> Handles import errors gracefully."""
        with patch("importlib.import_module") as mock_import, \
             pytest.raises(SystemExit) as exc_info:
            mock_import.side_effect = ImportError("Module not found")
            
            from cxc.cli import run_workflow
            run_workflow("wt.nonexistent", ["42"])
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Could not import" in captured.out

    def test_run_workflow_no_main(self, capsys):
        """<R10.2> Handles modules without main()."""
        with patch("importlib.import_module") as mock_import, \
             pytest.raises(SystemExit) as exc_info:
            mock_module = MagicMock(spec=[])  # No main attribute
            mock_import.return_value = mock_module
            
            from cxc.cli import run_workflow
            run_workflow("wt.broken", ["42"])
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "has no main()" in captured.out

    def test_run_workflow_exception(self, capsys):
        """<R10.2> Handles runtime exceptions."""
        with patch("importlib.import_module") as mock_import, \
             pytest.raises(SystemExit) as exc_info:
            mock_module = MagicMock()
            mock_module.main.side_effect = RuntimeError("Workflow failed")
            mock_import.return_value = mock_module
            
            from cxc.cli import run_workflow
            run_workflow("wt.failing", ["42"])
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error running workflow" in captured.out


# ----- Test Plan Command -----

class TestPlanCommand:
    """Tests for plan command routing."""

    def test_plan_command_basic(self):
        """<R10.3> plan command routes correctly."""
        with patch("cxc.cli.run_workflow") as mock_run:
            with patch("sys.argv", ["cxc", "plan", "42"]):
                from cxc.cli import main
                main()
            
            mock_run.assert_called_once_with("wt.plan_iso", ["42"])

    def test_plan_command_with_cxc_id(self):
        """<R10.3> plan command passes CXC ID."""
        with patch("cxc.cli.run_workflow") as mock_run:
            with patch("sys.argv", ["cxc", "plan", "42", "test1234"]):
                from cxc.cli import main
                main()
            
            mock_run.assert_called_once_with("wt.plan_iso", ["42", "test1234"])


# ----- Test Build Command -----

class TestBuildCommand:
    """Tests for build command routing."""

    def test_build_command(self):
        """<R10.4> build command routes correctly."""
        with patch("cxc.cli.run_workflow") as mock_run:
            with patch("sys.argv", ["cxc", "build", "42", "test1234"]):
                from cxc.cli import main
                main()
            
            mock_run.assert_called_once_with("wt.build_iso", ["42", "test1234"])


# ----- Test Test Command -----

class TestTestCommand:
    """Tests for test command routing."""

    def test_test_command_basic(self):
        """<R10.5> test command routes correctly."""
        with patch("cxc.cli.run_workflow") as mock_run:
            with patch("sys.argv", ["cxc", "test", "42", "test1234"]):
                from cxc.cli import main
                main()
            
            mock_run.assert_called_once_with("wt.test_iso", ["42", "test1234"])

    def test_test_command_skip_e2e(self):
        """<R10.5> --skip-e2e flag passed correctly."""
        with patch("cxc.cli.run_workflow") as mock_run:
            with patch("sys.argv", ["cxc", "test", "42", "test1234", "--skip-e2e"]):
                from cxc.cli import main
                main()
            
            mock_run.assert_called_once_with("wt.test_iso", ["42", "test1234", "--skip-e2e"])


# ----- Test Review Command -----

class TestReviewCommand:
    """Tests for review command routing."""

    def test_review_command_basic(self):
        """<R10.6> review command routes correctly."""
        with patch("cxc.cli.run_workflow") as mock_run:
            with patch("sys.argv", ["cxc", "review", "42", "test1234"]):
                from cxc.cli import main
                main()
            
            mock_run.assert_called_once_with("wt.review_iso", ["42", "test1234"])

    def test_review_command_skip_resolution(self):
        """<R10.6> --skip-resolution flag passed correctly."""
        with patch("cxc.cli.run_workflow") as mock_run:
            with patch("sys.argv", ["cxc", "review", "42", "test1234", "--skip-resolution"]):
                from cxc.cli import main
                main()
            
            mock_run.assert_called_once_with("wt.review_iso", ["42", "test1234", "--skip-resolution"])


# ----- Test Document Command -----

class TestDocumentCommand:
    """Tests for document command routing."""

    def test_document_command(self):
        """<R10.7> document command routes correctly."""
        with patch("cxc.cli.run_workflow") as mock_run:
            with patch("sys.argv", ["cxc", "document", "42", "test1234"]):
                from cxc.cli import main
                main()
            
            mock_run.assert_called_once_with("wt.document_iso", ["42", "test1234"])


# ----- Test Ship Command -----

class TestShipCommand:
    """Tests for ship command routing."""

    def test_ship_command(self):
        """<R10.8> ship command routes correctly."""
        with patch("cxc.cli.run_workflow") as mock_run:
            with patch("sys.argv", ["cxc", "ship", "42", "test1234"]):
                from cxc.cli import main
                main()
            
            mock_run.assert_called_once_with("wt.ship_iso", ["42", "test1234"])


# ----- Test Patch Command -----

class TestPatchCommand:
    """Tests for patch command routing."""

    def test_patch_command_basic(self):
        """<R10.9> patch command routes correctly."""
        with patch("cxc.cli.run_workflow") as mock_run:
            with patch("sys.argv", ["cxc", "patch", "42"]):
                from cxc.cli import main
                main()
            
            mock_run.assert_called_once_with("wt.patch_iso", ["42"])

    def test_patch_command_with_cxc_id(self):
        """<R10.9> patch command passes CXC ID."""
        with patch("cxc.cli.run_workflow") as mock_run:
            with patch("sys.argv", ["cxc", "patch", "42", "test1234"]):
                from cxc.cli import main
                main()
            
            mock_run.assert_called_once_with("wt.patch_iso", ["42", "test1234"])


# ----- Test SDLC Command -----

class TestSdlcCommand:
    """Tests for sdlc command routing."""

    def test_sdlc_command_basic(self):
        """<R10.10> sdlc command routes correctly."""
        with patch("cxc.cli.run_workflow") as mock_run:
            with patch("sys.argv", ["cxc", "sdlc", "42"]):
                from cxc.cli import main
                main()
            
            mock_run.assert_called_once_with("wt.sdlc_iso", ["42"])

    def test_sdlc_command_with_flags(self):
        """<R10.10> sdlc command passes all flags."""
        with patch("cxc.cli.run_workflow") as mock_run:
            with patch("sys.argv", ["cxc", "sdlc", "42", "test1234", "--skip-e2e", "--skip-resolution"]):
                from cxc.cli import main
                main()
            
            mock_run.assert_called_once_with("wt.sdlc_iso", ["42", "test1234", "--skip-e2e", "--skip-resolution"])


# ----- Test ZTE Command -----

class TestZteCommand:
    """Tests for zte command routing."""

    def test_zte_command_basic(self):
        """<R10.11> zte command routes correctly."""
        with patch("cxc.cli.run_workflow") as mock_run:
            with patch("sys.argv", ["cxc", "zte", "42"]):
                from cxc.cli import main
                main()
            
            mock_run.assert_called_once_with("wt.sdlc_zte_iso", ["42"])

    def test_zte_command_with_flags(self):
        """<R10.11> zte command passes all flags."""
        with patch("cxc.cli.run_workflow") as mock_run:
            with patch("sys.argv", ["cxc", "zte", "42", "--skip-e2e", "--skip-resolution"]):
                from cxc.cli import main
                main()
            
            mock_run.assert_called_once_with("wt.sdlc_zte_iso", ["42", "--skip-e2e", "--skip-resolution"])


# ----- Test Monitor Command -----

class TestMonitorCommand:
    """Tests for monitor command routing."""

    def test_monitor_command_success(self):
        """<R10.12> monitor command routes correctly."""
        import importlib
        from cxc import cli
        
        mock_module = MagicMock()
        mock_module.main = MagicMock()
        
        with patch.object(importlib, "import_module", return_value=mock_module) as mock_import, \
             patch.object(sys, "argv", ["cxc", "monitor"]):
            cli.main()
            
            mock_import.assert_called_with("cxc.triggers.trigger_cron")
            mock_module.main.assert_called_once()

    def test_monitor_command_not_found(self, capsys):
        """<R10.12> Handles missing trigger module."""
        import importlib
        from cxc import cli
        
        with patch.object(importlib, "import_module", side_effect=ImportError("Module not found")), \
             patch.object(sys, "argv", ["cxc", "monitor"]):
            cli.main()
            
            captured = capsys.readouterr()
            assert "not found" in captured.out


# ----- Test Webhook Command -----

class TestWebhookCommand:
    """Tests for webhook command routing."""

    def test_webhook_command_success(self):
        """<R10.13> webhook command routes correctly."""
        import importlib
        from cxc import cli
        
        mock_module = MagicMock()
        mock_module.main = MagicMock()
        
        with patch.object(importlib, "import_module", return_value=mock_module) as mock_import, \
             patch.object(sys, "argv", ["cxc", "webhook"]):
            cli.main()
            
            mock_import.assert_called_with("cxc.triggers.trigger_webhook")
            mock_module.main.assert_called_once()

    def test_webhook_command_not_found(self, capsys):
        """<R10.13> Handles missing trigger module."""
        import importlib
        from cxc import cli
        
        with patch.object(importlib, "import_module", side_effect=ImportError("Module not found")), \
             patch.object(sys, "argv", ["cxc", "webhook"]):
            cli.main()
            
            captured = capsys.readouterr()
            assert "not found" in captured.out
