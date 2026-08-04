"""
AI Trading Signals endpoints
"""
from fastapi import APIRouter, Query
from typing import List, Optional
from datetime import datetime
from app.services.signal_service import signal_service, DEFAULT_SCAN_LIST
from app.services.options_signals import options_signal_service

router = APIRouter()

DISCLAIMER = (
    "AI recommendations are probabilistic and not guaranteed. "
    "Past performance does not guarantee future results. Trade at your own risk."
)


@router.get("/")
async def get_signals(
    timeframe: str = "5minute",
    tradeable_only: bool = False,
    fast: bool = True,
):
    """Get AI trading signals. fast=true uses 8 liquid symbols for snappy dashboard."""
    symbols = DASHBOARD_SCAN if fast else DEFAULT_SCAN_LIST
    results = await signal_service.scan(
        symbols=symbols, timeframe=timeframe, tradeable_only=tradeable_only
    )
    return {
        "signals": [r.model_dump() for r in results],
        "count": len(results),
        "tradeable_count": sum(1 for r in results if r.is_tradeable),
        "fast": fast,
        "timestamp": datetime.now().isoformat(),
        "disclaimer": DISCLAIMER,
    }


@router.get("/analyze/{symbol}")
async def analyze_symbol(symbol: str, timeframe: str = "5minute"):
    """Deep AI analysis for a specific symbol"""
    result = await signal_service.analyze_symbol(symbol, timeframe)
    return result.model_dump()


@router.get("/scanner/scan")
async def run_market_scan(
    symbols: Optional[List[str]] = Query(None),
    timeframe: str = "5minute",
    tradeable_only: bool = True,
):
    """Run market scanner to find high-conviction opportunities"""
    scan_list = symbols or DEFAULT_SCAN_LIST
    results = await signal_service.scan(scan_list, timeframe, tradeable_only)
    return {
        "results": [r.model_dump() for r in results],
        "scanned_count": len(scan_list),
        "signals_found": len(results),
        "timestamp": datetime.now().isoformat(),
        "disclaimer": DISCLAIMER,
    }


@router.get("/scanner/momentum")
async def momentum_intraday_scan(
    timeframe: str = "5minute",
    limit: int = 8,
    tradeable_only: bool = False,
):
    """Analyze top explosive/momentum names for intraday (high-risk).

    Picks live high day-range / %change stocks, then runs full AI research.
    10-20% days are rare — this surfaces candidates with larger RANGE potential.
    """
    from app.services.market_data import market_service

    movers = await market_service.explosive_movers(limit=max(limit, 12))
    # Prefer names already moving UP for long-biased day trades
    pool = movers.get("movers") or []
    up = [m["symbol"] for m in pool if (m.get("change_percent") or 0) >= 0]
    down = [m["symbol"] for m in pool if (m.get("change_percent") or 0) < 0]
    # Long-first then short candidates
    scan_list = (up + down)[: max(6, min(limit + 4, 12))]

    results = await signal_service.scan(scan_list, timeframe, tradeable_only=False)
    if tradeable_only:
        results = [r for r in results if r.is_tradeable]

    # Attach mover meta
    meta = {m["symbol"]: m for m in pool}
    payload = []
    for r in results:
        d = r.model_dump()
        m = meta.get(r.symbol, {})
        d["day_change_percent"] = m.get("change_percent")
        d["day_range_pct"] = m.get("day_range_pct")
        d["explosive_score"] = m.get("explosive_score")
        d["potential_tag"] = m.get("potential_tag")
        d["ltp"] = m.get("ltp") or (d.get("quote") or {}).get("ltp")
        payload.append(d)

    # Sort tradeable first, then explosive score / confidence
    payload.sort(
        key=lambda x: (
            bool(x.get("is_tradeable")),
            float(x.get("explosive_score") or 0),
            float(x.get("confidence") or 0),
        ),
        reverse=True,
    )
    payload = payload[:limit]

    return {
        "results": payload,
        "scanned_count": len(scan_list),
        "signals_found": len(payload),
        "tradeable_count": sum(1 for x in payload if x.get("is_tradeable")),
        "movers_preview": pool[:10],
        "timestamp": datetime.now().isoformat(),
        "warning": (
            "HIGH RISK intraday momentum scan. "
            "10-20% single-day moves are uncommon. "
            "Losses can be large and fast. Use tight SL. Not guaranteed."
        ),
        "disclaimer": DISCLAIMER,
    }


@router.get("/scanner/options")
async def scan_options(
    underlying: Optional[str] = None,
    limit: int = 6,
):
    """
    High-probability Options Scanner (NIFTY / BANKNIFTY CE/PE)
    Returns top intraday options signals based on spot momentum + chain analysis
    """
    return await options_signal_service.scan_options(underlying, limit)
