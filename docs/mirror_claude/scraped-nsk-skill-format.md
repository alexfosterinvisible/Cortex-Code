# github.com/numman-ali/n-skills
https://raw.githubusercontent.com/numman-ali/n-skills/main/docs/skill-format.md

# SKILL.md Format Specification Summary

The SKILL.md format is a markdown-based standard for documenting agent skills, following the agentskills.io specification.

## Key Components

**Required frontmatter** includes a skill name (lowercase with hyphens), description with trigger phrases, and structured metadata.

**Optional metadata** encompasses version numbers, licensing information, author details, keywords, and compatibility flags for different platforms.

The document structure recommends including a description section, setup instructions, usage guidelines, practical examples, and references to advanced documentation.

**Skills can bundle resources** in organized subdirectories: extended documentation in `references/`, executable code in `scripts/`, and templates or output files in `assets/`.

## Best Practices

The specification emphasizes keeping the main SKILL.md file concise—"Under 500 lines"—while placing detailed documentation elsewhere. It recommends foregrounding trigger phrases in descriptions, providing concrete copy-pasteable examples, clearly documenting API key and dependency requirements, and using the references folder for comprehensive technical details.

This approach balances accessibility for quick skill discovery with depth for users needing implementation details.
