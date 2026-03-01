"""
DevAlpha MCP Server — AI-native on-chain intelligence infrastructure.

Connects AI agents to DevAlpha's chain intelligence, opportunity discovery,
and developer activity data via the public REST API at https://devalpha.dev.

Usage:
    python -m devalpha_mcp                    # stdio transport (Claude Desktop, Cursor, etc.)
    python -m devalpha_mcp --transport sse    # SSE transport (web clients)

Requires: pip install "mcp[cli]" httpx
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("devalpha-mcp")

import httpx
from mcp.server.fastmcp import FastMCP

# ── Configuration ────────────────────────────────────────

API_BASE = os.environ.get("DEVALPHA_API_URL", "https://devalpha.dev/api")

# ── Usage Logging ────────────────────────────────────────

_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
_LOG_FILE = os.path.join(_LOG_DIR, "mcp_queries.jsonl")


def _log_query(tool_name, params, response_len, latency_ms):
    """Append a query record to the JSONL log file."""
    try:
        os.makedirs(_LOG_DIR, exist_ok=True)
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "tool": tool_name,
            "params": params,
            "response_bytes": response_len,
            "latency_ms": round(latency_ms, 1),
        }
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")
    except Exception:
        pass  # Never let logging break a query


# ── HTTP Client ──────────────────────────────────────────

_client = httpx.Client(base_url=API_BASE, timeout=30.0)


def _api_get(path: str, params: dict | None = None) -> dict:
    """Make a GET request to the DevAlpha API."""
    resp = _client.get(path, params={k: v for k, v in (params or {}).items() if v is not None})
    resp.raise_for_status()
    return resp.json()


# ── MCP Server ───────────────────────────────────────────

mcp = FastMCP(
    "devalpha",
    instructions="DevAlpha — Web3 builder intelligence. Chain metrics, developer activity, hackathons, bounties, grants, and demand signals across 25+ blockchains.",
)


# ── Helpers ──────────────────────────────────────────────

def _compact_usd(value):
    """Format USD value compactly."""
    if value is None:
        return None
    if value >= 1e12:
        return f"${value / 1e12:.1f}T"
    if value >= 1e9:
        return f"${value / 1e9:.1f}B"
    if value >= 1e6:
        return f"${value / 1e6:.1f}M"
    if value >= 1e3:
        return f"${value / 1e3:.0f}K"
    return f"${value:.0f}"


def _format_chain(chain: dict) -> dict:
    """Format API chain response into compact dict for LLM consumption."""
    languages = chain.get("smart_contract_language")
    if isinstance(languages, str):
        try:
            languages = json.loads(languages)
        except (json.JSONDecodeError, TypeError):
            pass

    return {
        "name": chain.get("name"),
        "slug": chain.get("slug"),
        "type": chain.get("chain_type"),
        "evm": bool(chain.get("evm_compatible")),
        "native_token": chain.get("native_token_symbol"),
        "tvl": _compact_usd(chain.get("tvl_usd")),
        "fees_24h": _compact_usd(chain.get("fees_24h_usd")),
        "dex_volume_24h": _compact_usd(chain.get("dex_volume_24h_usd")),
        "stablecoin_mcap": _compact_usd(chain.get("stablecoin_mcap_usd")),
        "token_price": chain.get("native_token_price_usd"),
        "market_cap": _compact_usd(chain.get("native_token_mcap_usd")),
        "protocols": chain.get("protocol_count"),
        "weekly_commits": chain.get("weekly_commits"),
        "total_repos": chain.get("total_repos"),
        "active_repos": chain.get("active_repos"),
        "vm_type": chain.get("vm_type"),
        "languages": languages,
        "website": chain.get("website"),
        "docs": chain.get("docs_url"),
    }


def _json_response(data):
    """Serialize data to a compact JSON string for LLM context."""
    return json.dumps(data, default=str, indent=None, separators=(",", ":"))


# ── Tool 1: Compare Chains ──────────────────────────────

@mcp.tool()
async def compare_chains(
    sort_by: str = "tvl",
    chain_type: str | None = None,
    limit: int = 10,
) -> str:
    """Compare blockchains by key metrics. Returns a ranked list.

    Use this to answer: "Which chains have the most TVL?", "Best L2s by developer activity?",
    "Compare Solana vs Base vs Arbitrum".

    Args:
        sort_by: Metric to sort by. Options: tvl, fees, dex_volume, commits, protocols, name. Default: tvl.
        chain_type: Filter by type. Options: l1, l2, or None for all. Default: None.
        limit: Number of chains to return. Default: 10, max: 25.
    """
    t0 = time.time()
    limit = min(limit, 25)

    data = _api_get("/chains", {"sort": sort_by, "chain_type": chain_type})
    items = data.get("items", [])[:limit]
    chains = [_format_chain(c) for c in items]

    result = _json_response({"chains": chains, "sorted_by": sort_by, "total": len(chains)})
    _log_query("compare_chains", {"sort_by": sort_by, "chain_type": chain_type, "limit": limit}, len(result), (time.time() - t0) * 1000)
    return result


# ── Tool 2: Chain Detail ────────────────────────────────

@mcp.tool()
async def get_chain(slug: str) -> str:
    """Get detailed metrics for a specific blockchain.

    Use this to answer: "Tell me about Solana", "What's Ethereum's TVL?",
    "How active are developers on Base?".

    Args:
        slug: Chain identifier (e.g., 'solana', 'ethereum', 'base', 'arbitrum').
    """
    t0 = time.time()

    try:
        data = _api_get(f"/chains/{slug}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return _json_response({"error": f"Chain '{slug}' not found"})
        raise

    result = _format_chain(data)
    result["opportunity_count"] = data.get("opportunity_count", 0)
    result["cluster_count"] = data.get("cluster_count", 0)

    # Dev activity
    if data.get("weekly_commits"):
        result["dev_activity"] = {
            "commits": data.get("weekly_commits"),
            "repos": data.get("total_repos"),
            "active_repos": data.get("active_repos"),
        }

    # Social
    if data.get("discord_members") or data.get("telegram_members"):
        result["social"] = {
            "discord_members": data.get("discord_members"),
            "telegram_members": data.get("telegram_members"),
            "reddit_subscribers": data.get("reddit_subscribers"),
        }

    # Ecosystem summary
    parts = [result["name"]]
    if result.get("tvl"):
        parts.append(f"{result['tvl']} TVL")
    if result.get("fees_24h"):
        parts.append(f"{result['fees_24h']} daily fees")
    if result.get("weekly_commits"):
        parts.append(f"{result['weekly_commits']} weekly commits")
    if result.get("protocols"):
        parts.append(f"{result['protocols']} protocols")
    if result.get("opportunity_count"):
        parts.append(f"{result['opportunity_count']} active opportunities")
    if result.get("languages"):
        parts.append(f"Languages: {', '.join(result['languages'])}")
    result["ecosystem_summary"] = ". ".join(
        [parts[0] + ": " + ", ".join(parts[1:])] if len(parts) > 1 else parts
    )

    resp = _json_response(result)
    _log_query("get_chain", {"slug": slug}, len(resp), (time.time() - t0) * 1000)
    return resp


# ── Tool 3: Search Opportunities ────────────────────────

@mcp.tool()
async def search_opportunities(
    chain: str | None = None,
    opportunity_type: str | None = None,
    intent: str | None = None,
    sort: str = "newest",
    limit: int = 20,
) -> str:
    """Search hackathons, bounties, grants, and demand signals.

    Use this to answer: "Active hackathons on Solana", "DeFi bounties",
    "What do developers want to build?", "Grants available now".

    Args:
        chain: Filter by chain slug (e.g., 'solana', 'ethereum'). Default: None (all chains).
        opportunity_type: Filter type. Options: hackathon, bounty, grant, pain_point, tool_request, market_signal. Default: None.
        intent: Filter intent. Options: actionable_demand, story, question, discussion. Default: None.
        sort: Sort order. Options: newest, engagement, prize_desc, deadline_asc. Default: newest.
        limit: Number of results. Default: 20, max: 50.
    """
    t0 = time.time()
    limit = min(limit, 50)

    data = _api_get("/opportunities", {
        "chain": chain,
        "opportunity_type": opportunity_type,
        "intent": intent,
        "sort": sort,
        "limit": limit,
    })

    items = []
    for r in data.get("items", [])[:limit]:
        item = {
            "title": r.get("title"),
            "type": r.get("opportunity_type"),
            "url": r.get("url"),
            "source": r.get("source_name"),
            "chain": r.get("chain_name"),
            "intent": r.get("intent_category"),
        }
        if r.get("amount_max"):
            item["prize"] = f"${r['amount_max']:,.0f}" if r["amount_max"] >= 1 else None
        if r.get("deadline"):
            item["deadline"] = r["deadline"]
        engagement = (r.get("upvotes") or 0) + (r.get("num_comments") or 0)
        if engagement > 0:
            item["engagement"] = engagement
        items.append(item)

    result = _json_response({"opportunities": items, "total": len(items), "sort": sort})
    _log_query("search_opportunities", {"chain": chain, "type": opportunity_type, "intent": intent}, len(result), (time.time() - t0) * 1000)
    return result


# ── Tool 4: Discover Feed ───────────────────────────────

@mcp.tool()
async def discover() -> str:
    """Get DevAlpha's curated discovery feed: money opportunities, trending signals, and proven gaps.

    Use this to answer: "What's hot in Web3 right now?", "Any hackathons with prizes?",
    "What should I build?", "Where's the demand?".
    """
    t0 = time.time()

    data = _api_get("/discover")

    result = {
        "money_this_week": [
            {
                "title": r.get("title"),
                "url": r.get("url"),
                "prize": _compact_usd(r.get("amount_max")) if r.get("amount_max") else r.get("prize"),
                "type": r.get("opportunity_type", r.get("type")),
                "deadline": r.get("deadline"),
                "source": r.get("source_name", r.get("source")),
            }
            for r in data.get("money_this_week", [])
        ],
        "trending_signals": [
            {
                "title": r.get("title"),
                "url": r.get("url"),
                "engagement": r.get("engagement", (r.get("upvotes") or 0) + (r.get("num_comments") or 0)),
                "type": r.get("opportunity_type", r.get("type")),
                "intent": r.get("intent_category", r.get("intent")),
                "source": r.get("source_name", r.get("source")),
                "chain": r.get("chain_name", r.get("chain")),
            }
            for r in data.get("trending_signals", [])
        ],
        "proven_gaps": [
            {
                "title": r.get("title"),
                "description": (r.get("description") or "")[:200],
                "signals": r.get("signal_count", r.get("signals")),
                "sources": r.get("source_diversity", r.get("sources")),
                "sector": r.get("sector_name", r.get("sector")),
                "feasibility": r.get("solo_dev_feasibility", r.get("feasibility")),
                "revenue": r.get("revenue_potential", r.get("revenue")),
                "mvp_weeks": r.get("estimated_weeks_to_mvp", r.get("mvp_weeks")),
            }
            for r in data.get("proven_gaps", [])
        ],
    }

    resp = _json_response(result)
    _log_query("discover", {}, len(resp), (time.time() - t0) * 1000)
    return resp


# ── Tool 5: Chain Recommendation ────────────────────────

@mcp.tool()
async def recommend_chain(
    use_case: str,
    priorities: str = "tvl,developers",
) -> str:
    """Recommend the best blockchain for a specific use case.

    Use this to answer: "Best chain to build a DEX?", "Where should I launch an NFT project?",
    "Which L2 has the most developers?".

    Args:
        use_case: What you want to build (e.g., 'DEX aggregator', 'NFT marketplace', 'lending protocol').
        priorities: Comma-separated metrics to prioritize. Options: tvl, fees, developers, protocols, evm. Default: 'tvl,developers'.
    """
    t0 = time.time()
    priority_list = [p.strip() for p in priorities.split(",")]

    data = _api_get("/chains", {"sort": "tvl", "ecosystem_type": "blockchain"})

    chains_data = []
    for r in data.get("items", []):
        score = 0
        tvl = r.get("tvl_usd") or 0
        fees = r.get("fees_24h_usd") or 0
        commits = r.get("weekly_commits") or 0
        protocols = r.get("protocol_count") or 0

        if "tvl" in priority_list:
            score += min(tvl / 1e10, 10)
        if "fees" in priority_list:
            score += min(fees / 1e6, 10)
        if "developers" in priority_list:
            score += min(commits / 500, 10)
        if "protocols" in priority_list:
            score += min(protocols / 100, 10)
        if "evm" in priority_list and r.get("evm_compatible"):
            score += 5

        chains_data.append({
            "chain": _format_chain(r),
            "score": round(score, 2),
            "opportunities": r.get("opportunity_count", 0),
        })

    chains_data.sort(key=lambda x: x["score"], reverse=True)
    top = chains_data[:5]

    resp = _json_response({
        "use_case": use_case,
        "priorities": priority_list,
        "recommendations": top,
        "note": "Scores are relative rankings based on on-chain metrics. Higher = better fit for stated priorities.",
    })
    _log_query("recommend_chain", {"use_case": use_case, "priorities": priorities}, len(resp), (time.time() - t0) * 1000)
    return resp


# ── Tool 6: Developer Activity ──────────────────────────

@mcp.tool()
async def get_developer_activity(slug: str, weeks: int = 12) -> str:
    """Get developer activity trends for a blockchain over time.

    Use this to answer: "Is Solana developer activity growing?",
    "How many commits does Base have?", "Developer trends on Arbitrum".

    Args:
        slug: Chain slug (e.g., 'solana', 'ethereum', 'base').
        weeks: Number of weeks of history. Default: 12, max: 52.
    """
    t0 = time.time()
    weeks = min(weeks, 52)

    try:
        data = _api_get(f"/chains/{slug}/developers", {"weeks": weeks})
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return _json_response({"error": f"Chain '{slug}' not found"})
        raise

    activity = [
        {
            "week": r.get("week_start"),
            "commits": r.get("total_commits"),
            "repos": r.get("total_repos"),
            "active_repos": r.get("active_repos"),
            "contributors": r.get("total_contributors"),
        }
        for r in data.get("items", [])
    ]

    resp = _json_response({
        "chain": data.get("chain", slug),
        "slug": slug,
        "weeks": len(activity),
        "activity": activity,
    })
    _log_query("get_developer_activity", {"slug": slug, "weeks": weeks}, len(resp), (time.time() - t0) * 1000)
    return resp


# ── Tool 7: Sector Intelligence ─────────────────────────

@mcp.tool()
async def get_sectors() -> str:
    """Get all Web3 sectors with cluster counts and market intelligence.

    Use this to answer: "What Web3 sectors exist?", "Which sectors have the most opportunities?",
    "DeFi sub-sectors?".
    """
    t0 = time.time()

    data = _api_get("/sectors")

    sectors = [
        {
            "name": r.get("name"),
            "slug": r.get("slug"),
            "description": r.get("description"),
            "clusters": r.get("cluster_count", r.get("clusters", 0)),
            "ai_disruption": r.get("ai_disruption_potential"),
        }
        for r in data.get("items", data.get("sectors", []))
    ]

    resp = _json_response({"sectors": sectors, "total": len(sectors)})
    _log_query("get_sectors", {}, len(resp), (time.time() - t0) * 1000)
    return resp


# ── Tool 8: Platform Stats ──────────────────────────────

@mcp.tool()
async def get_stats() -> str:
    """Get DevAlpha platform-wide statistics.

    Use this to answer: "How much data does DevAlpha have?", "Platform overview",
    "Database stats".
    """
    t0 = time.time()

    data = _api_get("/stats")

    resp = _json_response(data)
    _log_query("get_stats", {}, len(resp), (time.time() - t0) * 1000)
    return resp


# ── Tool 9: Chain Slugs ─────────────────────────────────

@mcp.tool()
async def get_chain_slugs() -> str:
    """Get all valid chain slugs. Use this to discover valid chain identifiers
    before calling get_chain, search_opportunities, or get_developer_activity.

    Returns a list of all chain slugs with their names and types.
    """
    t0 = time.time()

    data = _api_get("/chains")
    chains = [
        {"name": r.get("name"), "slug": r.get("slug"), "type": r.get("chain_type")}
        for r in data.get("items", [])
    ]

    result = _json_response({"chains": chains, "total": len(chains)})
    _log_query("get_chain_slugs", {}, len(result), (time.time() - t0) * 1000)
    return result


# ── Tool 10: Full-Text Search ───────────────────────────

@mcp.tool()
async def search_text(query: str, limit: int = 20) -> str:
    """Full-text search across all signals, hackathons, bounties, and grants.

    Use this when the user has a specific topic or keyword to search for,
    rather than browsing by filters. Searches titles and descriptions.

    Args:
        query: Search terms (e.g., 'zk rollup', 'cross-chain bridge', 'AI agent').
        limit: Number of results. Default: 20, max: 50.
    """
    t0 = time.time()
    limit = min(limit, 50)

    data = _api_get("/search", {"q": query, "limit": limit})

    # The /search endpoint returns results grouped by type
    items = []
    for group in ["clusters", "signals", "funding", "sectors"]:
        for r in data.get(group, []):
            item = {
                "title": r.get("title", r.get("name")),
                "type": r.get("opportunity_type", r.get("type", group)),
                "url": r.get("url"),
                "chain": r.get("chain_name"),
                "source": r.get("source_name"),
            }
            engagement = (r.get("upvotes") or 0) + (r.get("num_comments") or 0)
            if engagement > 0:
                item["engagement"] = engagement
            items.append(item)

    result = _json_response({"query": query, "results": items[:limit], "total": len(items)})
    _log_query("search_text", {"query": query}, len(result), (time.time() - t0) * 1000)
    return result


# ── Tool 11: MCP Usage Stats ────────────────────────────

@mcp.tool()
async def get_mcp_usage() -> str:
    """Get MCP server usage statistics — query counts, popular tools, recent activity.

    Use this to understand how DevAlpha's MCP server is being used.
    """
    try:
        if not os.path.exists(_LOG_FILE):
            return _json_response({"total_queries": 0, "message": "No queries logged yet"})

        tool_counts: dict[str, int] = {}
        total = 0
        recent: list[dict] = []
        with open(_LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    total += 1
                    tool = record.get("tool", "unknown")
                    tool_counts[tool] = tool_counts.get(tool, 0) + 1
                    if len(recent) < 10:
                        recent.append(record)
                    else:
                        recent.pop(0)
                        recent.append(record)
                except json.JSONDecodeError:
                    continue

        popular = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)
        return _json_response({
            "total_queries": total,
            "tools": {k: v for k, v in popular},
            "recent": recent[-5:],
        })
    except Exception as e:
        return _json_response({"error": str(e)})


# ── Entry Point ──────────────────────────────────────────

def main():
    transport = "stdio"
    if "--transport" in sys.argv:
        idx = sys.argv.index("--transport")
        if idx + 1 < len(sys.argv):
            transport = sys.argv[idx + 1]

    logger.info(f"Starting DevAlpha MCP server (transport={transport}, api={API_BASE})")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
