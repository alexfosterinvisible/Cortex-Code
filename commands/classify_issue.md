# Github Issue Command Selection

Based on the `## GITHUB_ISSUE` (see below), follow the `## INSTRUCTIONS` (see below) to select the appropriate command to execute based on the `## COMMAND_MAPPING` (see below).

## INSTRUCTIONS

- Based on the details in the `## GITHUB_ISSUE` (see below), select the appropriate command to execute.
- IMPORTANT: Respond exclusively with '/' followed by the command to execute based on the `## COMMAND_MAPPING` (see below).
- Use the command mapping to help you decide which command to respond with.
- Don't examine the codebase just focus on the `## GITHUB_ISSUE` (see below) and the `## COMMAND_MAPPING` (see below) to determine the appropriate command to execute.

## COMMAND_MAPPING

- Respond with `/chore` if the issue is a chore.
- Respond with `/bug` if the issue is a bug.
- Respond with `/feature` if the issue is a feature.
- Respond with `/patch` if the issue is a patch.
- Respond with `0` if the issue isn't any of the above.

## GITHUB_ISSUE

$ARGUMENTS