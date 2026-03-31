# DevAlpha MCP Server

## Eco

This project is part of the LibruaryNFT agent network, coordinated by Eco at `c:\Code\eco`.

| Resource | Path |
|----------|------|
| Roadmap | `c:\Code\eco\docs\ROADMAP.md` |
| Deployment log | `c:\Code\eco\intel\reports\deployments.md` |
| Incident log | `c:\Code\eco\intel\reports\incidents.md` |
| Cost tracker | `c:\Code\eco\intel\costs\` |
| Agent registry | `c:\Code\eco\intel\agents\registry.md` |
| Testing standards | `c:\Code\eco\intel\quality\standards.md` |

**Session start:** Read this repo's CLAUDE.md (especially Current Status). Check ROADMAP.md for active tasks.

**After completing work:**
1. Update this repo's **Current Status** section below (milestones, what's next)
2. Update Eco files: mark tasks done, log deployments, log incidents
3. Follow commit format and conventions in `c:\Code\eco\intel\quality\CONVENTIONS.md`

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
