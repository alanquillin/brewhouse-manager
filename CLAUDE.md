# Brewhouse Manager

See [AGENTS.md](./AGENTS.md) for full project documentation: tech stack, project structure, common commands, testing, code style, architecture patterns, and CI.

## Claude Code Rules

**NEVER commit or push changes without explicit user instruction.** The user must review all changes before any git actions are taken.

- Do not run `git commit` unless the user explicitly says to commit.
- Do not run `git push` unless the user explicitly says to push.
- Do not create PRs or take any remote git actions unless explicitly asked.
- After making file edits, stop and wait for user review before any git operations.
