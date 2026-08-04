"""
Market data endpoints
"""
from fastapi import APIRouter, Query
from typing import List, Optional
from app.services.market_data import market_service

router = APIRouter()


@router.get("/status")
async def get_market_status():
    return await market_service.get_status()


@router.get("/quote/{symbol}")
async def get_quote(symbol: str, exchange: str = "NSE"):
    try:
        return await market_service.get_quote(symbol, exchange)
    except Exception as e:
        return {"symbol": symbol.upper(), "ltp": None, "error": str(e), "source": "dhan"}


@router.get("/quotes")
async def get_quotes(symbols: List[str] = Query(...), exchange: str = "NSE"):
    try:
        quotes = await market_service.get_quotes(symbols, exchange)
    except Exception as e:
        return {"quotes": [], "error": str(e)}
    return {"quotes": quotes}


@router.get("/historical/{symbol}")
async def get_historical_data(
    symbol: str,
    interval: str = "5minute",
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
):
    return await market_service.get_historical(symbol, interval, from_date, to_date)


@router.get("/top-gainers")
async def get_top_gainers(limit: int = 10):
    try:
        return {"gainers": await market_service.top_gainers(limit)}
    except Exception as e:
        return {"gainers": [], "error": str(e)}


@router.get("/top-losers")
async def get_top_losers(limit: int = 10):
    try:
        return {"losers": await market_service.top_losers(limit)}
    except Exception as e:
        return {"losers": [], "error": str(e)}


@router.get("/explosive")
async def explosive_movers(limit: int = 15):
    """High day-range / momentum names for aggressive intraday (not guaranteed 10-20%)."""
    try:
        return await market_service.explosive_movers(limit=limit)
    except Exception as e:
        return {
            "movers": [],
            "count": 0,
            "scanned": 0,
            "error": str(e),
            "note": "Live Dhan quotes unavailable. Refresh access token if auth failed.",
            "source": "dhan",
        }


@router.get("/options-chain/{symbol}")
async def get_options_chain(symbol: str, expiry: Optional[str] = None):
    """Live options chain from Dhan Data API"""
    try:
        return await market_service.options_chain(symbol, expiry)
    except Exception as e:
        return {"symbol": symbol.upper(), "chain": [], "error": str(e)}


@router.get("/indices")
async def get_indices():
    try:
        return {"indices": await market_service.indices()}
    except Exception as e:
        return {"indices": [], "error": str(e)}


@router.get("/breadth")
async def market_breadth():
    try:
        return await market_service.breadth()
    except Exception as e:
        return {"advances": 0, "declines": 0, "unchanged": 0, "error": str(e)}


@router.get("/provider")
async def data_provider():
    """Dhan connection status"""
    return await market_service.provider_status()


@router.get("/search")
async def search_symbols(q: str = Query("", min_length=1), limit: int = 12):
    """Search NSE equities & indices by symbol (Dhan instrument master).

    Returns symbols immediately. LTP is optional and non-blocking so search
    stays fast even when Dhan rate-limits quote calls.
    """
    from app.services.instruments import instrument_master
    import asyncio

    await instrument_master.ensure_loaded()
    results = instrument_master.search(q, limit=limit)

    # Best-effort LTP attach with short timeout (never block search)
    async def _attach_ltp():
        try:
            st = await market_service.provider_status()
            if not st.get("configured") or not results:
                return
            symbols = [r["symbol"] for r in results[:6]]
            quotes = await market_service.get_quotes(symbols)
            qmap = {x["symbol"]: x for x in quotes}
            for r in results:
                qq = qmap.get(r["symbol"])
                if qq:
                    r["ltp"] = qq.get("ltp")
                    r["change_percent"] = qq.get("change_percent")
                    r["change"] = qq.get("change")
        except Exception:
            pass

    try:
        await asyncio.wait_for(_attach_ltp(), timeout=1.5)
    except Exception:
        pass

    return {"query": q.upper().strip(), "count": len(results), "results": results}
