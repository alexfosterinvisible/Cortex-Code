import sys
import argparse
import importlib
from typing import List
from dotenv import load_dotenv, find_dotenv

def run_workflow(module_name: str, args: List[str]):
    """Run a workflow module by importing it and calling main()."""
    # Patch sys.argv
    sys.argv = [f"adw {module_name}"] + args
    
    try:
        module = importlib.import_module(f"adw.workflows.{module_name}")
        if hasattr(module, "main"):
            module.main()
        else:
            print(f"Error: Module adw.workflows.{module_name} has no main() function.")
            sys.exit(1)
    except ImportError as e:
        print(f"Error: Could not import workflow '{module_name}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error running workflow '{module_name}': {e}")
        sys.exit(1)

def main():
    load_dotenv(find_dotenv(usecwd=True))  # Load .env from CWD, not package location
    
    parser = argparse.ArgumentParser(description="AI Developer Workflow (ADW) CLI")
    subparsers = parser.add_subparsers(dest="command", help="Workflow command")

    # Plan
    plan_parser = subparsers.add_parser("plan", help="Plan implementation for an issue")
    plan_parser.add_argument("issue_number", help="GitHub issue number")
    plan_parser.add_argument("adw_id", nargs="?", help="Optional ADW ID")

    # Build
    build_parser = subparsers.add_parser("build", help="Build implementation from plan")
    build_parser.add_argument("issue_number", help="GitHub issue number")
    build_parser.add_argument("adw_id", help="ADW ID")

    # Test
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("issue_number", help="GitHub issue number")
    test_parser.add_argument("adw_id", help="ADW ID")
    test_parser.add_argument("--skip-e2e", action="store_true", help="Skip E2E tests")

    # Review
    review_parser = subparsers.add_parser("review", help="Review implementation")
    review_parser.add_argument("issue_number", help="GitHub issue number")
    review_parser.add_argument("adw_id", help="ADW ID")
    review_parser.add_argument("--skip-resolution", action="store_true", help="Skip auto-resolution of issues")

    # Document
    doc_parser = subparsers.add_parser("document", help="Generate documentation")
    doc_parser.add_argument("issue_number", help="GitHub issue number")
    doc_parser.add_argument("adw_id", help="ADW ID")

    # Ship
    ship_parser = subparsers.add_parser("ship", help="Ship changes (merge PR)")
    ship_parser.add_argument("issue_number", help="GitHub issue number")
    ship_parser.add_argument("adw_id", help="ADW ID")

    # Patch
    patch_parser = subparsers.add_parser("patch", help="Create and implement a patch")
    patch_parser.add_argument("issue_number", help="GitHub issue number")
    patch_parser.add_argument("adw_id", nargs="?", help="Optional ADW ID")

    # SDLC (Complete)
    sdlc_parser = subparsers.add_parser("sdlc", help="Run complete SDLC")
    sdlc_parser.add_argument("issue_number", help="GitHub issue number")
    sdlc_parser.add_argument("adw_id", nargs="?", help="Optional ADW ID")
    sdlc_parser.add_argument("--skip-e2e", action="store_true", help="Skip E2E tests")
    sdlc_parser.add_argument("--skip-resolution", action="store_true", help="Skip auto-resolution")

    # SDLC ZTE
    zte_parser = subparsers.add_parser("zte", help="Run Zero Touch Execution (SDLC + Ship)")
    zte_parser.add_argument("issue_number", help="GitHub issue number")
    zte_parser.add_argument("adw_id", nargs="?", help="Optional ADW ID")
    zte_parser.add_argument("--skip-e2e", action="store_true", help="Skip E2E tests")
    zte_parser.add_argument("--skip-resolution", action="store_true", help="Skip auto-resolution")

    # Cron/Trigger
    cron_parser = subparsers.add_parser("monitor", help="Run cron monitor")
    
    # Webhook
    webhook_parser = subparsers.add_parser("webhook", help="Run webhook server")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Map command to module and args
    workflow_args = []
    
    if args.command == "plan":
        workflow_args = [args.issue_number]
        if args.adw_id:
            workflow_args.append(args.adw_id)
        run_workflow("wt.plan_iso", workflow_args)
        
    elif args.command == "build":
        run_workflow("wt.build_iso", [args.issue_number, args.adw_id])
        
    elif args.command == "test":
        workflow_args = [args.issue_number, args.adw_id]
        if args.skip_e2e:
            workflow_args.append("--skip-e2e")
        run_workflow("wt.test_iso", workflow_args)
        
    elif args.command == "review":
        workflow_args = [args.issue_number, args.adw_id]
        if args.skip_resolution:
            workflow_args.append("--skip-resolution")
        run_workflow("wt.review_iso", workflow_args)
        
    elif args.command == "document":
        run_workflow("wt.document_iso", [args.issue_number, args.adw_id])
        
    elif args.command == "ship":
        run_workflow("wt.ship_iso", [args.issue_number, args.adw_id])
        
    elif args.command == "patch":
        workflow_args = [args.issue_number]
        if args.adw_id:
            workflow_args.append(args.adw_id)
        run_workflow("wt.patch_iso", workflow_args)
        
    elif args.command == "sdlc":
        workflow_args = [args.issue_number]
        if args.adw_id:
            workflow_args.append(args.adw_id)
        if args.skip_e2e:
            workflow_args.append("--skip-e2e")
        if args.skip_resolution:
            workflow_args.append("--skip-resolution")
        run_workflow("wt.sdlc_iso", workflow_args)
        
    elif args.command == "zte":
        workflow_args = [args.issue_number]
        if args.adw_id:
            workflow_args.append(args.adw_id)
        if args.skip_e2e:
            workflow_args.append("--skip-e2e")
        if args.skip_resolution:
            workflow_args.append("--skip-resolution")
        run_workflow("wt.sdlc_zte_iso", workflow_args)
        
    elif args.command == "monitor":
        # triggers/trigger_cron.py need to be moved to adw/triggers/ or similar
        # I copied triggers to adw-framework/triggers
        # But they are scripts.
        # I'll need to make them modules or just run them.
        # Let's assume I move triggers to adw.triggers
        try:
            module = importlib.import_module("adw.triggers.trigger_cron")
            if hasattr(module, "main"):
                module.main()
        except ImportError:
            print("Error: adw.triggers.trigger_cron not found.")
            
    elif args.command == "webhook":
        try:
            module = importlib.import_module("adw.triggers.trigger_webhook")
            if hasattr(module, "main"):
                module.main()
        except ImportError:
            print("Error: adw.triggers.trigger_webhook not found.")

if __name__ == "__main__":
    main()


