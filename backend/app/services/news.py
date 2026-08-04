"""
Latest market / stock news for AI signal research.
Sources: Google News RSS (no API key) — Indian markets focused.
"""
from __future__ import annotations
import asyncio
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote_plus

import httpx
from loguru import logger

# Simple in-process cache
_CACHE: Dict[str, Tuple[float, List[dict]]] = {}
_CACHE_TTL = 300.0  # 5 minutes

BULLISH = {
    "surge", "rally", "gain", "gains", "jump", "jumps", "rise", "rises", "soar",
    "bull", "bullish", "record high", "all-time high", "breakout", "upgrade",
    "upgraded", "beat", "beats", "profit", "strong", "outperform", "buy",
    "expands", "wins", "order win", "deal", "growth", "positive", "rebound",
    "recovery", "higher", "up ", " leaps", "boost", "inflow", "fii buy",
}
BEARISH = {
    "fall", "falls", "drop", "drops", "plunge", "slump", "crash", "crashs",
    "bear", "bearish", "selloff", "sell-off", "downgrade", "downgraded",
    "miss", "misses", "loss", "losses", "weak", "underperform", "sell",
    "fraud", "probe", "sebi", "raid", "decline", "lower", "down ", "cut",
    "cuts", "warning", "warning", "outflow", "fii sell", "default", "debt",
}


def _score_headline(text: str) -> float:
    """Return sentiment -1.0 .. +1.0 from headline keywords."""
    t = f" {text.lower()} "
    b = sum(1 for w in BULLISH if w in t)
    s = sum(1 for w in BEARISH if w in t)
    if b == 0 and s == 0:
        return 0.0
    return max(-1.0, min(1.0, (b - s) / max(b + s, 1)))


def _strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s or "").strip()


async def fetch_news(symbol: str, limit: int = 8) -> List[Dict[str, Any]]:
    """Fetch latest headlines related to symbol + Indian market context."""
    key = symbol.upper().strip()
    cached = _CACHE.get(key)
    if cached and time.monotonic() - cached[0] < _CACHE_TTL:
        return cached[1][:limit]

    # Company-focused + India market context queries
    queries = [
        f"{key} stock NSE OR BSE",
        f"{key} shares India",
    ]
    items: List[Dict[str, Any]] = []
    seen = set()

    async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
        for q in queries:
            url = (
                "https://news.google.com/rss/search?"
                f"q={quote_plus(q)}&hl=en-IN&gl=IN&ceid=IN:en"
            )
            try:
                r = await client.get(url, headers={"User-Agent": "TradeAI/1.0"})
                if r.status_code != 200:
                    continue
                root = ET.fromstring(r.text)
                for item in root.findall(".//item"):
                    title = _strip_html(item.findtext("title") or "")
                    link = (item.findtext("link") or "").strip()
                    pub = item.findtext("pubDate") or ""
                    source = ""
                    src_el = item.find("source")
                    if src_el is not None and src_el.text:
                        source = src_el.text.strip()
                    if not title or title in seen:
                        continue
                    seen.add(title)
                    sent = _score_headline(title)
                    items.append({
                        "title": title,
                        "link": link,
                        "source": source or "Google News",
                        "published": pub,
                        "sentiment": round(sent, 2),
                        "bias": "BULLISH" if sent > 0.15 else ("BEARISH" if sent < -0.15 else "NEUTRAL"),
                    })
            except Exception as e:
                logger.warning(f"news fetch failed for {q}: {e}")

    # Sort: newest-ish first (pubDate string), then |sentiment|
    items.sort(key=lambda x: (x.get("published") or "", abs(x.get("sentiment") or 0)), reverse=True)
    items = items[: max(limit, 12)]
    _CACHE[key] = (time.monotonic(), items)
    return items[:limit]


def news_aggregate(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate news into a factor score 0-100 and summary."""
    if not items:
        return {
            "score": 50.0,
            "weight": 0.6,
            "bias": "NEUTRAL",
            "detail": "No recent headlines found",
            "headline_count": 0,
            "avg_sentiment": 0.0,
            "top_headlines": [],
        }
    sents = [float(i.get("sentiment") or 0) for i in items]
    avg = sum(sents) / len(sents)
    # Map -1..1 → 0..100
    score = max(0.0, min(100.0, 50.0 + avg * 45.0))
    bull = sum(1 for s in sents if s > 0.15)
    bear = sum(1 for s in sents if s < -0.15)
    bias = "BULLISH" if avg > 0.15 else ("BEARISH" if avg < -0.15 else "NEUTRAL")
    detail = f"News {bias}: {bull} bullish / {bear} bearish / {len(items)} headlines (avg {avg:+.2f})"
    return {
        "score": round(score, 1),
        "weight": 1.1,
        "bias": bias,
        "detail": detail,
        "headline_count": len(items),
        "avg_sentiment": round(avg, 3),
        "top_headlines": items[:5],
    }
