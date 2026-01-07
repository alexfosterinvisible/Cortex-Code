#!/usr/bin/env -S uv run
# /// script
# dependencies = ["fastapi", "uvicorn", "python-dotenv"]
# ///

"""
GitHub Webhook Trigger - Cortex Code (CXC)

FastAPI webhook endpoint that receives GitHub issue events and triggers CXC workflows.
Responds immediately to meet GitHub's 10-second timeout by launching workflows
in the background. Supports both standard and isolated workflows.

Usage: uv run trigger_webhook.py

Environment Requirements:
- PORT: Server port (default: 8001)
- All workflow requirements (GITHUB_PAT, ANTHROPIC_API_KEY, etc.)
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request
from dotenv import load_dotenv
import uvicorn

from cxc.core.utils import make_cxc_id, setup_logger, get_safe_subprocess_env
from cxc.core.health import run_health_check
from cxc.integrations.github import make_issue_comment, CXC_BOT_IDENTIFIER
from cxc.integrations.workflow_ops import extract_cxc_info, AVAILABLE_CXC_WORKFLOWS
from cxc.core.state import CxcState

# Load environment variables
load_dotenv()

# Configuration
PORT = int(os.getenv("PORT", "8001"))

# Dependent workflows that require existing worktrees
# These cannot be triggered directly via webhook
DEPENDENT_WORKFLOWS = [
    "cxc_build_iso",
    "cxc_test_iso",
    "cxc_review_iso",
    "cxc_document_iso",
    "cxc_ship_iso",
]

# Create FastAPI app
app = FastAPI(
    title="CXC Webhook Trigger", description="GitHub webhook endpoint for CXC"
)

print(f"Starting CXC Webhook Trigger on port {PORT}")


@app.post("/gh-webhook")
async def github_webhook(request: Request):
    """Handle GitHub webhook events."""
    try:
        # Get event type from header
        event_type = request.headers.get("X-GitHub-Event", "")

        # Parse webhook payload
        payload = await request.json()

        # Extract event details
        action = payload.get("action", "")
        issue = payload.get("issue", {})
        issue_number = issue.get("number")

        print(
            f"Received webhook: event={event_type}, action={action}, issue_number={issue_number}"
        )

        workflow = None
        provided_cxc_id = None
        model_set = None
        trigger_reason = ""
        content_to_check = ""

        # Check if this is an issue opened event
        if event_type == "issues" and action == "opened" and issue_number:
            issue_body = issue.get("body", "")
            content_to_check = issue_body

            # Ignore issues from CXC bot to prevent loops
            if CXC_BOT_IDENTIFIER in issue_body:
                print(f"Ignoring CXC bot issue to prevent loop")
                workflow = None
            # Check if body contains "cxc_"
            elif "cxc_" in issue_body.lower():
                # Use temporary ID for classification
                temp_id = make_cxc_id()
                extraction_result = extract_cxc_info(issue_body, temp_id)
                if extraction_result.has_workflow:
                    workflow = extraction_result.workflow_command
                    provided_cxc_id = extraction_result.cxc_id
                    model_set = extraction_result.model_set
                    trigger_reason = f"New issue with {workflow} workflow"

        # Check if this is an issue comment
        elif event_type == "issue_comment" and action == "created" and issue_number:
            comment = payload.get("comment", {})
            comment_body = comment.get("body", "")
            content_to_check = comment_body

            print(f"Comment body: '{comment_body}'")

            # Ignore comments from CXC bot to prevent loops
            if CXC_BOT_IDENTIFIER in comment_body:
                print(f"Ignoring CXC bot comment to prevent loop")
                workflow = None
            # Check if comment contains "cxc_"
            elif "cxc_" in comment_body.lower():
                # Use temporary ID for classification
                temp_id = make_cxc_id()
                extraction_result = extract_cxc_info(comment_body, temp_id)
                if extraction_result.has_workflow:
                    workflow = extraction_result.workflow_command
                    provided_cxc_id = extraction_result.cxc_id
                    model_set = extraction_result.model_set
                    trigger_reason = f"Comment with {workflow} workflow"

        # Validate workflow constraints
        if workflow in DEPENDENT_WORKFLOWS:
            if not provided_cxc_id:
                print(
                    f"{workflow} is a dependent workflow that requires an existing CXC ID"
                )
                print(f"Cannot trigger {workflow} directly via webhook without CXC ID")
                workflow = None
                # Post error comment to issue
                try:
                    make_issue_comment(
                        str(issue_number),
                        f"❌ Error: `{workflow}` is a dependent workflow that requires an existing CXC ID.\n\n"
                        f"To run this workflow, you must provide the CXC ID in your comment, for example:\n"
                        f"`{workflow} cxc-12345678`\n\n"
                        f"The CXC ID should come from a previous workflow run (like `cxc_plan_iso` or `cxc_patch_iso`).",
                    )
                except Exception as e:
                    print(f"Failed to post error comment: {e}")

        if workflow:
            # Use provided CXC ID or generate a new one
            cxc_id = provided_cxc_id or make_cxc_id()

            # If CXC ID was provided, update/create state file
            if provided_cxc_id:
                # Try to load existing state first
                state = CxcState.load(provided_cxc_id)
                if state:
                    # Update issue_number and model_set if state exists
                    state.update(issue_number=str(issue_number), model_set=model_set)
                else:
                    # Only create new state if it doesn't exist
                    state = CxcState(provided_cxc_id)
                    state.update(
                        cxc_id=provided_cxc_id,
                        issue_number=str(issue_number),
                        model_set=model_set,
                    )
                state.save("webhook_trigger")
            else:
                # Create new state for newly generated CXC ID
                state = CxcState(cxc_id)
                state.update(
                    cxc_id=cxc_id, issue_number=str(issue_number), model_set=model_set
                )
                state.save("webhook_trigger")

            # Set up logger
            logger = setup_logger(cxc_id, "webhook_trigger")
            logger.info(
                f"Detected workflow: {workflow} from content: {content_to_check[:100]}..."
            )
            if provided_cxc_id:
                logger.info(f"Using provided CXC ID: {provided_cxc_id}")

            # Post comment to issue about detected workflow
            try:
                make_issue_comment(
                    str(issue_number),
                    f"🤖 CXC Webhook: Detected `{workflow}` workflow request\n\n"
                    f"Starting workflow with ID: `{cxc_id}`\n"
                    f"Workflow: `{workflow}` 🏗️\n"
                    f"Model Set: `{model_set}` ⚙️\n"
                    f"Reason: {trigger_reason}\n\n"
                    f"Logs will be available at: `agents/{cxc_id}/{workflow}/`",
                )
            except Exception as e:
                logger.warning(f"Failed to post issue comment: {e}")

            # Build command to run the appropriate workflow
            # Use current working directory (where server was started from)
            # This works both in dev and when installed as a package
            repo_root = os.getcwd()
            module_name = workflow.replace("cxc_", "")
            cmd = [
                "uv",
                "run",
                "python",
                "-m",
                f"cxc.workflows.wt.{module_name}",
                str(issue_number),
                cxc_id,
            ]

            print(f"Launching {workflow} for issue #{issue_number}")
            print(f"Command: {' '.join(cmd)} (reason: {trigger_reason})")
            print(f"Working directory: {repo_root}")

            # Launch in background using Popen with filtered environment
            process = subprocess.Popen(
                cmd,
                cwd=repo_root,  # Run from repository root where .claude/commands/ is located
                env=get_safe_subprocess_env(),  # Pass only required environment variables
                start_new_session=True,
            )

            print(
                f"Background process started for issue #{issue_number} with CXC ID: {cxc_id}"
            )
            print(f"Logs will be written to: agents/{cxc_id}/{workflow}/execution.log")

            # Return immediately
            return {
                "status": "accepted",
                "issue": issue_number,
                "cxc_id": cxc_id,
                "workflow": workflow,
                "message": f"CXC {workflow} triggered for issue #{issue_number}",
                "reason": trigger_reason,
                "logs": f"agents/{cxc_id}/{workflow}/",
            }
        else:
            print(
                f"Ignoring webhook: event={event_type}, action={action}, issue_number={issue_number}"
            )
            return {
                "status": "ignored",
                "reason": f"Not a triggering event (event={event_type}, action={action})",
            }

    except Exception as e:
        print(f"Error processing webhook: {e}")
        # Always return 200 to GitHub to prevent retries
        return {"status": "error", "message": "Internal error processing webhook"}


@app.get("/health")
async def health():
    """Health check endpoint - runs comprehensive system health check."""
    try:
        # Run health check directly using the core module
        result = run_health_check()

        return {
            "status": "healthy" if result.success else "unhealthy",
            "service": "cxc-webhook-trigger",
            "health_check": {
                "success": result.success,
                "warnings": result.warnings,
                "errors": result.errors,
            },
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "cxc-webhook-trigger",
            "error": f"Health check failed: {str(e)}",
        }


def main():
    """Run the webhook server."""
    print(f"Starting server on http://0.0.0.0:{PORT}")
    print(f"Webhook endpoint: POST /gh-webhook")
    print(f"Health check: GET /health")
    uvicorn.run(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
