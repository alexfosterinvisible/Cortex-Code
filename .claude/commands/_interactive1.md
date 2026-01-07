---
name: Interactive Issue Workflow
description: >
  Guides the user through selecting a GitHub issue/PR and manages a full end-to-end interactive workflow including planning, implementation, automated review, and iterative progress reporting.
argument-hints:
  - No arguments required; interaction is fully guided.
---
1. PRIME            [EXECUTE] ./.claude/commands/prime.md to init your context window.

2. LIST GH ISSUES    `gh issue list --state open --web && 1a. gh pr list --state open --web` # gh get list of open issues / PRs and output them to user with numbering and urls. 
3. ASK FOR ISSUE #   [ASK] user which ISSUE to focus on.
<WAIT FOR USER INPUT.>

1. ASK FOR WORKFLOW   [ASK] Immediately give user a list of workflow options in full in a numbered list. Ask which to use.
   - make a suggestion of which makes the most sense given the issue and situation.

Now - think. Are you ready to begin planning? This is your chance to clarify anything with user that is GENUINELY ambiguous and can't be inferred from the repo.

If ready - inform user you are starting in BIG TEXT:

------------------------------
STARTING CxC WORKFLOW
------------------------------

5. uv run cxc [workflow] (eg zte) [issue-number] (eg 29) in  background terminal. The two variables are from ABOVE.
6. then sleep for 5 minutes at a time, report on progress, output any major artifacts like plans / reports in full to chat, then sleep for 5 minutes again. 
   - The review report (near the end) should be the WHOLE VERBATIM review report before and after remediation bug fixing.
   - Start with a task list with 20 sleep/check loops in it.
   - Check once after workflow has started in bg task that there shouldn't be git conflicts when the workflow tries to merge (if ZTE workflow) and inform user if so.

Exceptions to loop:
1 Once the plan is complete, checkout to branch and open the plan in the active cursor window.
2 Once implementation is complete, begin your OWN review process and report to user on what you find, later compare contrast with the workflows own review process.

--- Break loop once workflow completes or user gives a new instruction.