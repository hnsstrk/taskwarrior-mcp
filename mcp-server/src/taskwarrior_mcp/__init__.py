"""Taskwarrior MCP Server — Python-Backend für Claude Code und andere MCP-Clients."""

from taskwarrior_mcp.server import mcp


def main() -> None:
    """Entry-Point für `taskwarrior-mcp` CLI und `uvx taskwarrior-mcp`."""
    mcp.run()


__all__ = ["main", "mcp"]
