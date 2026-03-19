# AGENTS.md

## Project Overview
This project is a Mattermost agent bridge.

It receives requests from Mattermost, processes them via agent workflows,
and stores runtime state in a database.

This repository contains ONLY:
- source code
- configuration templates
- documentation
- SQL schema/migrations

It must NEVER contain:
- personal user data
- raw conversation logs
- API keys or secrets

---

## Goals
- Build a bridge service for Mattermost → Agent execution
- Support Codex-driven development workflow
- Maintain strict separation between code (repo) and data (DB)
- Enable future integration with Codex CLI / Claude Code

---

## Architecture Rules
- Personal data MUST be stored in database only
- Repository is stateless
- All schema changes must go through SQL migrations
- No business logic should depend on file-based memory

---

## Coding Guidelines
- Keep files small and modular
- Prefer clear and explicit naming
- Avoid large refactors unless explicitly requested
- Write tests for new logic
- Do not introduce unnecessary abstractions

---

## Project Structure (expected)
- app/src → application code
- app/tests → test code
- docs/ → architecture and design docs
- sql/ → schema and migrations
- infra/ → docker, deployment configs

---

## Commands (to be maintained)
- Install dependencies: TBD
- Run application: TBD
- Run tests: TBD
- Lint: TBD

---

## Development Rules for Agents (IMPORTANT)
When modifying this repository:

1. Do NOT store any runtime data in files
2. Do NOT add secrets into code
3. Update README.md if setup changes
4. Update docs/architecture.md if architecture changes
5. Keep changes minimal and focused
6. Explain what files were modified after completing work

---

## Done Criteria
A task is complete when:
- Code builds / runs successfully
- Tests pass
- Documentation is updated if behavior changed
