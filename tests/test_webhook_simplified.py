#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv"]
# ///

"""
Test script to verify simplified webhook workflow support.
"""

import os

# Mirror the constants from trigger_webhook.py
DEPENDENT_WORKFLOWS = [
    "cxc_build", "cxc_test", "cxc_review", "cxc_document",
    "cxc_build_iso", "cxc_test_iso", "cxc_review_iso", "cxc_document_iso"
]

def test_workflow_support():
    """Test the simplified workflow support."""
    print("=== Simplified Webhook Workflow Support ===")
    print()
    
    print("Entry Point Workflows (can be triggered via webhook):")
    entry_points = [
        "cxc_plan",
        "cxc_patch", 
        "cxc_plan_build",
        "cxc_plan_build_test",
        "cxc_plan_build_test_review",
        "cxc_plan_build_document",
        "cxc_plan_build_review",
        "cxc_sdlc",
        "cxc_plan_iso",
        "cxc_patch_iso",
        "cxc_plan_build_iso",
        "cxc_plan_build_test_iso",
        "cxc_plan_build_test_review_iso",
        "cxc_plan_build_document_iso",
        "cxc_plan_build_review_iso",
        "cxc_sdlc_iso",
    ]
    
    for workflow in entry_points:
        emoji = "🏗️" if workflow.endswith("_iso") else "🔧"
        print(f"  {workflow:35} {emoji}")
    
    print()
    print("Dependent Workflows (require CXC ID):")
    for workflow in DEPENDENT_WORKFLOWS:
        emoji = "🏗️" if workflow.endswith("_iso") else "🔧"
        print(f"  {workflow:35} {emoji}")
    
    print()
    print("Testing workflow validation logic:")
    
    test_cases = [
        ("cxc_plan", None, True),
        ("cxc_plan_iso", None, True),
        ("cxc_build", None, False),  # Dependent, no ID
        ("cxc_build", "test-123", True),  # Dependent with ID
        ("cxc_build_iso", None, False),  # Dependent, no ID
        ("cxc_build_iso", "test-123", True),  # Dependent with ID
        ("cxc_plan_build", None, True),
        ("cxc_plan_build_iso", None, True),
        ("cxc_test_iso", None, False),  # Dependent, no ID
        ("cxc_sdlc_iso", None, True),
    ]
    
    for workflow, cxc_id, should_work in test_cases:
        if workflow in DEPENDENT_WORKFLOWS and not cxc_id:
            status = "❌ BLOCKED (requires CXC ID)"
        else:
            status = "✅ Can trigger"
        
        id_info = f" (with ID: {cxc_id})" if cxc_id else ""
        print(f"  {workflow:20}{id_info:20} {status}")


if __name__ == "__main__":
    test_workflow_support()