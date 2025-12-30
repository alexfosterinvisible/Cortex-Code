# Conditional Documentation Guide

This prompt helps you determine what documentation you should read based on the specific changes you need to make in the codebase. Review the conditions below and read the relevant documentation before proceeding with your task.

## INSTRUCTIONS
- Review the task you've been asked to perform
- Check each documentation path in the Conditional Documentation section
- For each path, evaluate if any of the listed conditions apply to your task
  - IMPORTANT: Only read the documentation if any one of the conditions match your task
- IMPORTANT: You don't want to excessively read documentation. Only read the documentation if it's relevant to your task.

## Conditional Documentation

- [README.md]
  - Conditions:
    - When operating on anything under [app/server]
    - When operating on anything under [app/client]
    - When first understanding the project structure
    - When you want to learn the commands to start or stop the server or client

- [app/client/src/style.css]
  - Conditions:
    - When you need to make changes to the client's style

- [commands/classify_adw.md]
  - Conditions:
    - When adding or removing new [adw/workflows/wt/*_iso.py] or [adw/workflows/reg/*.py] files

- [docs/ORCHESTRATOR_GUIDE.md]
  - Conditions:
    - When you're operating in the [adw/workflows/] directory

- [app_docs/feature-*.md]
  - Conditions:
    - When working with specific feature implementations
    - When troubleshooting feature-specific functionality
    - When implementing changes related to documented features

## Customization

Replace bracketed `[items]` with your project-specific paths:
- [app/server] → Your backend directory
- [app/client] → Your frontend directory  
- [app/client/src/style.css] → Your main stylesheet
- [adw/workflows/] → Your ADW workflows directory
- [app_docs/feature-*.md] → Your feature documentation directory
