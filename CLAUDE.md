# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Taskwarrior MCP — a Claude Code plugin that integrates Taskwarrior via two components in a monorepo:

1. **MCP Server** (`mcp-server/`) — Python backend, published as PyPI package `taskwarrior-mcp`, invoked via `uvx`
2. **Claude Code Plugin** (`plugin/`) — Commands, Agents, Skills, Hooks, `.mcp.json`
3. **Marketplace Metadata** (`.claude-plugin/`) — `marketplace.json` for Claude Code plugin registry

## Build & Development Commands

All commands run from `mcp-server/`:

```bash
uv sync                                          # Install dependencies
uv run pytest                                    # All tests
uv run pytest tests/unit/                        # Unit tests only
uv run pytest tests/unit/test_models.py::test_x  # Single test
uv run pytest tests/integration/                 # Integration tests (needs Taskwarrior installed)
uv run ruff check .                              # Lint
uv run mcp dev src/taskwarrior_mcp/server.py     # MCP Inspector at localhost:6274
```

Plugin local testing:
```bash
claude --plugin-dir plugin/
```

## Architecture

### MCP Server (`mcp-server/src/taskwarrior_mcp/`)

- **`server.py`** — FastMCP instance with `json_response=True`, lifespan pattern for client init, 11 tools (task_add, task_list, task_get, task_modify, task_done, task_delete, task_start, task_stop, task_projects, task_tags, task_stats)
- **`taskwarrior.py`** — `TaskwarriorClient` class wrapping Taskwarrior CLI via `subprocess.run()`. Handles TW 2.x/3.x differences
- **`models.py`** — Pydantic v2 input validation with shell-injection prevention
- **`config.py`** — `pydantic-settings` BaseSettings, env prefix `TW_MCP_`

### Plugin (`plugin/`)

- **Commands**: `/task-review`, `/task-plan`, `/task-inbox`, `/task-sync`
- **Agents**: `task-manager` (Sonnet, full write access), `task-reviewer` (Haiku, read-only)
- **Skill**: `taskwarrior/SKILL.md` — auto-activates on task/todo/deadline keywords

## Critical Rules

1. **`subprocess.run()` must always use `shell=False`** with list arguments — never shell=True, never string commands
2. **`shlex.split()` for filter parsing** — never `str.split()`, it breaks on quoted strings
3. **Exit code 1 is NOT an error** — Taskwarrior returns 1 for "no matching tasks", only ≥2 is an error
4. **No `print()` in MCP server** — stdio is reserved for the MCP protocol, use `logging` only
5. **Always use UUIDs**, never integer task IDs (IDs change on every mutation)
6. **`task_add` must return UUID** — call `+LATEST export` after adding
7. **Shell-injection prevention** — block `; | & $ \ { }` and backticks in text input fields via Pydantic validation
8. **Agents must run in foreground** — background subagents have no MCP tool access
9. **`${PLUGIN_DIR}` does not exist** in Claude Code — `.mcp.json` must use `uvx` or absolute paths
10. **`pydantic-settings` is a separate package** since Pydantic v2

## Key Dependencies

- Python ≥3.10, `mcp[cli]>=1.25,<2`, `pydantic>=2.0`, `pydantic-settings>=2.0`
- Dev: `pytest>=8.0`, `pytest-asyncio>=0.23`, `ruff>=0.4`
- Build backend: `hatchling`
- Package manager: `uv`

## Testing Patterns

- **Unit tests**: mock `subprocess.run`, verify `shell=False` in every test
- **Integration tests**: real Taskwarrior in isolated environment via `tmp_path` fixture in `conftest.py`
- **Async**: use `pytest-asyncio` for async tool tests

## MCP Tool Naming

In agent configs, tools are referenced as `mcp__taskwarrior__<toolname>` (e.g., `mcp__taskwarrior__task_list`).

## Task Management

Offene Tasks fuer dieses Projekt werden in **Taskwarrior** verwaltet (Projekt: `taskwarrior_mcp`).

```bash
task project:taskwarrior_mcp list    # Alle offenen Tasks
```
