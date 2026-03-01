# DevAlpha MCP Server

An [MCP](https://modelcontextprotocol.io) server that gives AI agents access to builder intelligence — ecosystem metrics, developer activity, hackathons, bounties, grants, and demand signals across 50+ ecosystems (blockchains + AI platforms).

Powered by [DevAlpha](https://devalpha.dev).

## Quick Start

### Claude Desktop / Claude Code

Add to your Claude config (`claude_desktop_config.json`):

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

### Install

```bash
pip install devalpha-mcp
```

Or clone and run directly:

```bash
git clone https://github.com/LibruaryNFT/devalpha-mcp.git
cd devalpha-mcp
pip install -e .
python -m devalpha_mcp
```

## Tools

| Tool | Description | Example Query |
|------|-------------|---------------|
| `compare_chains` | Rank blockchains by TVL, fees, dev activity | "Which L2s have the most TVL?" |
| `get_chain` | Detailed metrics for a specific chain | "Tell me about Solana" |
| `search_opportunities` | Search hackathons, bounties, grants, signals | "Active hackathons on Ethereum" |
| `discover` | Curated feed: money, trends, proven gaps | "What should I build in Web3?" |
| `recommend_chain` | Best chain for your use case | "Best chain to build a DEX?" |
| `get_developer_activity` | Dev activity trends over time | "Is Base developer activity growing?" |
| `get_sectors` | Web3 sectors with opportunity counts | "What DeFi sub-sectors exist?" |
| `get_stats` | Platform-wide statistics | "How much data does DevAlpha have?" |
| `get_chain_slugs` | All valid chain identifiers | "What chains are tracked?" |
| `search_text` | Full-text search across all data | "Find everything about zk rollups" |
| `get_mcp_usage` | Your local MCP usage analytics | "How am I using DevAlpha?" |

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `DEVALPHA_API_URL` | `https://devalpha.dev/api` | API base URL |

## How It Works

This MCP server is a thin client over the [DevAlpha REST API](https://devalpha.dev). It translates MCP tool calls into API requests and formats responses for LLM consumption. No database or API keys required.

## License

MIT
