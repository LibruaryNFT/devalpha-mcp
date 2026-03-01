# DevAlpha — AI Agent Integration

## What is DevAlpha?

DevAlpha is a decision engine for Web3 builders: **"Which chain should I build on, and what should I build there?"**

It tracks 25+ blockchains with real-time metrics (TVL, fees, dev activity) and aggregates hackathons, bounties, grants, and demand signals from Reddit, HN, GitHub, and Web3 platforms.

## MCP Server

This repository provides an MCP (Model Context Protocol) server that gives AI agents direct access to DevAlpha's intelligence.

### Available Tools

- **compare_chains** — Rank blockchains by TVL, fees, developer activity, protocols
- **get_chain** — Deep dive into a specific chain's metrics and ecosystem
- **search_opportunities** — Find hackathons, bounties, grants, and demand signals
- **discover** — Curated feed of money opportunities, trends, and proven gaps
- **recommend_chain** — Get chain recommendations scored by your priorities
- **get_developer_activity** — Developer activity trends over time
- **get_sectors** — Web3 sector intelligence (DeFi, NFT, gaming, etc.)
- **get_stats** — Platform statistics and data coverage
- **get_chain_slugs** — Valid chain identifiers for other tools
- **search_text** — Full-text search across all signals
- **get_mcp_usage** — Your local usage analytics

### Setup

```bash
pip install devalpha-mcp
```

Configure your MCP client (Claude Desktop, Cursor, etc.):

```json
{
  "mcpServers": {
    "devalpha": {
      "command": "python",
      "args": ["-m", "devalpha_mcp"]
    }
  }
}
```

### API

All data is served from `https://devalpha.dev/api`. No authentication required.

### Links

- Website: https://devalpha.dev
- Dashboard: https://devalpha.dev/for-agents
- GitHub: https://github.com/LibruaryNFT/devalpha-mcp
