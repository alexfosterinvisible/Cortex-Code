# github.com/numman-ali/cc-mirror/docs
https://raw.githubusercontent.com/numman-ali/cc-mirror/main/docs/features/team-mode.md

# Team Mode Documentation Summary

This documentation explains a multi-agent collaboration system for Claude Code called Team Mode. Here are the key points:

## Core Functionality

Team Mode enables multiple Claude agents to work together on shared projects through coordinated task management. Agents can create, claim, and complete tasks from a centralized queue stored locally in JSON format.

## Key Components

The system provides four primary tools:
- **TaskCreate**: Initiate new work items
- **TaskGet**: Retrieve specific task details
- **TaskUpdate**: Modify status, add notes, establish dependencies
- **TaskList**: View all tasks with summaries

## Orchestration Philosophy

When enabled, the system installs an "orchestration skill" that positions Claude as "The Conductor"—someone who transforms complex requests into coordinated execution. The principle emphasized is: "Absorb complexity, radiate simplicity."

## Task Dependencies

Tasks support blocking relationships, allowing sequential work planning. For example, task #2 might require task #1's completion before beginning, preventing workers from attempting impossible dependencies.

## Environment Configuration

Teams can be isolated using environment variables like `CLAUDE_CODE_AGENT_ID` and `CLAUDE_CODE_AGENT_TYPE`. As of version 1.2.0, team names automatically scope by project folder, simplifying multi-team setups in shared directories.

## CLI Management

Command-line tools allow direct task manipulation without agent involvement, including creating, archiving, and visualizing dependency graphs.
