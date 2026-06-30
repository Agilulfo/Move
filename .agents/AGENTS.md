# Custom Agent Rules for Move Project

## Cardinal Order Code Tags

When requested by the user to address tag/task markers in the code, the agent must process and resolve them sequentially in cardinal order (1, 2, 3, etc.).

### Supported Tag Formats

You can use any of the following formats in code comments:

1. **TODO with Parentheses**:
   * Example: `# TODO(1): Implement this function` or `// TODO(1): ...`
2. **Plain Numbered Brackets**:
   * Example: `# [1] Implement this function` or `// [1] ...`
3. **Step Prefix**:
   * Example: `# STEP-1: Implement this function` or `// STEP-1: ...`

### Agent Instructions
When the user asks to address these tags:
1. Search the codebase for any matching comments.
2. Sort them in ascending cardinal order (e.g., `1` -> `2` -> `3`).
3. Resolve each task sequentially.
4. **Pause after each item**: Stop execution and ask the user for feedback or approval before proceeding to the next step. Answer any questions and discuss next steps directly in the chat CLI.
