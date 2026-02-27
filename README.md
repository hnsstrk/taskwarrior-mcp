# Taskwarrior MCP

A complete [Taskwarrior](https://taskwarrior.org/) integration for [Claude Code](https://claude.ai/code) — MCP server with 11 tools, slash commands, specialized agents, and an auto-invoked skill.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-%3E%3D3.10-blue.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)

## Features

- **11 MCP Tools** -- Create, list, modify, complete, delete, start/stop tasks, query projects, tags, and statistics
- **4 Slash Commands** -- `/task-review`, `/task-plan`, `/task-inbox`, `/task-sync`
- **2 Specialized Agents** -- `task-manager` (full write access) and `task-reviewer` (read-only analysis)
- **Auto-Skill** -- Activates automatically when context involves tasks, todos, or deadlines
- **Hooks** -- Visual feedback after write operations
- **Shell-Injection Prevention** -- Pydantic validation on all inputs, `subprocess` with `shell=False`
- **Taskwarrior 2.x and 3.x** -- Supports both major versions

## Prerequisites

- [Taskwarrior](https://taskwarrior.org/) 2.x or 3.x (must be in `$PATH`)
- Python >= 3.10
- [uv](https://docs.astral.sh/uv/)
- [Claude Code](https://claude.ai/code)

## Installation

### 1. Clone and Install the MCP Server

```bash
git clone https://github.com/hnsstrk/taskwarrior-mcp.git
cd taskwarrior-mcp
uv tool install -e ./mcp-server
```

This installs `taskwarrior-mcp` as an editable tool. Code changes take effect immediately.

### 2. Register the MCP Server in Claude Code

```bash
claude mcp add --transport stdio --scope user taskwarrior \
  --env TW_MCP_LOG_LEVEL=WARNING \
  -- taskwarrior-mcp
```

### 3. Load the Plugin

```bash
claude --plugin-dir /path/to/taskwarrior-mcp/plugin
```

For persistent access, add a shell alias to your `~/.zshrc` or `~/.bashrc`:

```bash
alias claude='claude --plugin-dir /path/to/taskwarrior-mcp/plugin'
```

## Quick Start

Once installed, you can interact with Taskwarrior directly through Claude Code:

```
> What are my open tasks?
> Create a task "Review PR #42" with high priority, due end of week, in project Dev
> Mark task a1b2c3d4 as done
> /task-review
```

The skill activates automatically whenever you mention tasks, todos, or deadlines. You can also use the slash commands for structured workflows.

## Configuration

All settings are configured via environment variables with the prefix `TW_MCP_`:

| Variable | Default | Description |
|----------|---------|-------------|
| `TW_MCP_TASK_BINARY` | `task` | Path to the Taskwarrior binary |
| `TW_MCP_TASK_DATA` | -- | Override for `rc.data.location` |
| `TW_MCP_TASKRC` | -- | Path to an alternative `.taskrc` |
| `TW_MCP_DEFAULT_LIMIT` | `50` | Default limit for task listings |
| `TW_MCP_COMMAND_TIMEOUT` | `30` | Timeout in seconds |
| `TW_MCP_LOG_LEVEL` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR) |
| `TW_MCP_AUTO_SYNC` | `false` | Automatic `task sync` after write operations |

Set environment variables when registering the MCP server:

```bash
claude mcp add --transport stdio --scope user taskwarrior \
  --env TW_MCP_LOG_LEVEL=WARNING \
  --env TW_MCP_TASK_DATA=/path/to/data \
  -- taskwarrior-mcp
```

## Available Tools

### Read Tools

| Tool | Description |
|------|-------------|
| `task_list` | List tasks with filters (project, tags, status, custom filter expressions) |
| `task_get` | Retrieve a single task by UUID (supports UUID prefixes, min. 8 chars) |
| `task_projects` | List all projects with task counts |
| `task_tags` | List all tags |
| `task_stats` | Return Taskwarrior statistics (task counts, velocity, etc.) |

### Write Tools

| Tool | Description |
|------|-------------|
| `task_add` | Add a new task with optional project, priority, due date, tags, recurrence |
| `task_modify` | Modify task attributes (add/remove tags, change priority, due date, etc.) |
| `task_done` | Mark a task as completed |
| `task_delete` | Permanently delete a task |
| `task_start` | Start time tracking on a task (set to active) |
| `task_stop` | Stop time tracking on an active task |

### Filter Syntax

The `filter_expr` parameter in `task_list` supports native Taskwarrior filter syntax:

```
project:Work              # Filter by project
+urgent +OVERDUE          # Tags and virtual tags
due.before:eow            # Due before end of week
priority:H                # High priority
description.contains:meeting
status:pending            # Status (pending/completed/deleted/waiting)
```

### Date Formats

```
today, tomorrow, eow, eom, eoq, +2d, +1w, +3m, 2025-03-15
```

## Plugin Features

### Slash Commands

| Command | Description |
|---------|-------------|
| `/task-review` | Daily task review workflow |
| `/task-plan [project]` | Weekly planning session |
| `/task-inbox` | GTD inbox processing |
| `/task-sync` | Sync with server and show status |

### Agents

| Agent | Model | Access | Use Case |
|-------|-------|--------|----------|
| `task-manager` | Sonnet | Full read/write | Creating, modifying, and completing tasks |
| `task-reviewer` | Haiku | Read-only | Project overviews, progress reports, workload analysis |

### Skill

The Taskwarrior skill auto-activates when conversation context involves tasks, todos, deadlines, project planning, or reviews. It provides Claude with complete knowledge of all available tools, filter syntax, date formats, and best practices.

### Hooks

Post-tool-use hooks provide visual confirmation after write operations (`task_add`, `task_modify`, `task_done`, `task_delete`, `task_start`, `task_stop`).

## Development

All commands run from the `mcp-server/` directory:

```bash
cd mcp-server
uv sync                                          # Install dependencies
uv run pytest                                    # Run all tests
uv run pytest tests/unit/                        # Unit tests only
uv run pytest tests/integration/                 # Integration tests (requires Taskwarrior)
uv run ruff check .                              # Lint
uv run mcp dev src/taskwarrior_mcp/server.py     # MCP Inspector at localhost:6274
```

After changes to `pyproject.toml`, reinstall (run from the repo root):

```bash
uv tool install -e ./mcp-server --force
```

### Testing

- **Unit tests** mock `subprocess.run` and verify `shell=False` in every test
- **Integration tests** use a real Taskwarrior instance in an isolated environment via `tmp_path`
- **Async tests** use `pytest-asyncio` for async tool handlers

### Plugin Testing

```bash
claude --plugin-dir plugin/
```

Verify: MCP connection, slash commands, agent availability, and automatic skill activation.

## Architecture

This project is a monorepo with two components:

```
taskwarrior-mcp/
├── .claude-plugin/                 # Marketplace metadata
│   └── marketplace.json           # Claude Code plugin registry entry
├── mcp-server/                    # Python MCP server (PyPI: taskwarrior-mcp)
│   ├── src/taskwarrior_mcp/
│   │   ├── server.py              # FastMCP instance, 11 tool handlers
│   │   ├── taskwarrior.py         # CLI wrapper (subprocess, shell=False)
│   │   ├── models.py              # Pydantic v2 input validation
│   │   └── config.py              # pydantic-settings, env prefix TW_MCP_
│   └── tests/
│       ├── unit/                   # Mocked subprocess tests
│       └── integration/            # Real Taskwarrior tests
│
└── plugin/                         # Claude Code plugin
    ├── .claude-plugin/plugin.json  # Plugin manifest
    ├── .mcp.json                   # MCP server registration (uvx)
    ├── commands/                    # Slash commands
    ├── agents/                     # Specialized agents
    ├── skills/taskwarrior/         # Auto-invoked skill
    └── hooks/                      # Post-tool-use hooks
```

### Key Design Decisions

- **UUIDs only** -- Integer task IDs change on every mutation; all operations use UUIDs
- **`shell=False` enforced** -- All subprocess calls use list arguments, never shell execution
- **`shlex.split()` for filters** -- Properly handles quoted strings in filter expressions
- **Exit code 1 is not an error** -- Taskwarrior returns 1 for "no matching tasks"
- **No `print()` in MCP server** -- stdio is reserved for the MCP protocol; logging goes to stderr

## Contributing

Contributions are welcome. Please ensure:

1. All tests pass (`uv run pytest`)
2. Code passes linting (`uv run ruff check .`)
3. `subprocess.run()` calls use `shell=False` with list arguments
4. Input validation uses Pydantic models with shell-injection prevention

## License

[MIT](LICENSE)
