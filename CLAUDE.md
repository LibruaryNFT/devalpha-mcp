# DevAlpha MCP Server

## Command Center

This project is part of the LibruaryNFT agent network, coordinated by the command center at `c:\Code\command-center`.

| Resource | Path |
|----------|------|
| Task list | `c:\Code\command-center\TODO.md` |
| Deployment log | `c:\Code\command-center\deployments\log.md` |
| Incident log | `c:\Code\command-center\incidents\log.md` |
| Cost tracker | `c:\Code\command-center\costs\tracker.md` |
| Agent registry | `c:\Code\command-center\agents\registry.md` |

**Session start:** Read this repo's CLAUDE.md (especially Current Status). Check TODO.md for active tasks.

**After completing work:**
1. Update this repo's **Current Status** section below (milestones, what's next)
2. Update command center files: mark TODOs done, log deployments, log incidents
3. Follow commit format and conventions in `c:\Code\command-center\CONVENTIONS.md`

## Current Status

| Milestone | Status | Notes |
|-----------|--------|-------|
| MCP server published on PyPI | Done | `devalpha-mcp` package |
| Reads from DevAlpha API | Done | devalpha.dev endpoints |

**Last updated:** 2026-03-05

## What This Is

Public MCP (Model Context Protocol) server that gives AI agents access to DevAlpha's opportunity data. Published on PyPI as `devalpha-mcp`.

## Stack
- Python
- MCP protocol (stdio transport)
- Reads from DevAlpha API at devalpha.dev

## Parent Project
- Main repo: `c:\Code\devalpha` — the full DevAlpha platform
- This is a lightweight client that queries the DevAlpha API

## Publishing
```bash
# Build and publish to PyPI
python -m build
twine upload dist/*
```
