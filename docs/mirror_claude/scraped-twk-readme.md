# github.com/Piebald-AI/tweakcc
https://raw.githubusercontent.com/Piebald-AI/tweakcc/main/README.md

# tweakcc

**tweakcc** is a CLI tool that enhances Claude Code by enabling customization of system prompts, themes, toolsets, and UI elements. The tool works by patching Claude Code's `cli.js` file across Windows, macOS, and Linux installations.

## Key Features

The tool allows users to:
- Modify all Claude Code system prompts through markdown files
- Create custom themes with color picker functionality
- Build toolsets that control which tools Claude can access
- Customize thinking verbs and spinner animations
- Style user messages beyond default formatting
- Expand thinking blocks automatically
- Adjust context limits for compatible APIs

## Installation & Usage

Run without installing: `npx tweakcc`

The tool maintains configuration in `~/.tweakcc/` by default, with alternative paths available through environment variables. When Claude Code updates, tweakcc reapplies customizations from saved configuration.

## System Prompts

Rather than one editable file, Claude Code's prompt comprises multiple components stored as markdown files. tweakcc downloads prompt templates from its GitHub repository, creates local files for editing, and applies changes via `tweakcc --apply`. When conflicts arise between user edits and Anthropic updates, the tool generates an HTML diff visualization for resolution.

## Related Tools

The ecosystem includes **clotilde** for session management, **ccstatusline** for custom status displays, and **cc-mirror** for creating isolated Claude Code variants with different providers.

## Compatibility

Verified working with Claude Code version 2.0.69, with support across npm, Homebrew, and native installations using various Node version managers.
