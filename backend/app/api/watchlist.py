"""
Watchlist endpoints (in-memory demo store; persists via DB when auth is wired)
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.services.market_data import market_service

router = APIRouter()

# Demo default watchlist (reduced to 3 to avoid rate limits with frequent polling)
_watchlists: Dict[int, Dict[str, Any]] = {
    1: {
        "id": 1,
        "name": "Default",
        "is_default": True,
        "items": [
            {"id": 1, "symbol": "NIFTY", "exchange": "NSE", "instrument_type": "INDEX"},
            {"id": 2, "symbol": "BANKNIFTY", "exchange": "NSE", "instrument_type": "INDEX"},
            {"id": 3, "symbol": "RELIANCE", "exchange": "NSE", "instrument_type": "EQ"},
        ],
    }
}
_next_wl_id = 2
_next_item_id = 10


@router.get("/")
async def get_watchlists():
    result = []
    for wl in _watchlists.values():
        symbols = [i["symbol"] for i in wl["items"]]
        try:
            quotes = await market_service.get_quotes(symbols) if symbols else []
        except Exception:
            quotes = []
        qmap = {q["symbol"]: q for q in quotes if q.get("symbol")}
        items = [{**i, "quote": qmap.get(i["symbol"])} for i in wl["items"]]
        result.append({**wl, "items": items})
    return {"watchlists": result}


@router.post("/")
async def create_watchlist(name: str = "New Watchlist"):
    global _next_wl_id
    wl = {"id": _next_wl_id, "name": name, "is_default": False, "items": []}
    _watchlists[_next_wl_id] = wl
    _next_wl_id += 1
    return wl


@router.get("/{watchlist_id}")
async def get_watchlist(watchlist_id: int):
    wl = _watchlists.get(watchlist_id)
    if not wl:
        raise HTTPException(404, "Watchlist not found")
    symbols = [i["symbol"] for i in wl["items"]]
    quotes = await market_service.get_quotes(symbols) if symbols else []
    qmap = {q["symbol"]: q for q in quotes}
    items = [{**i, "quote": qmap.get(i["symbol"])} for i in wl["items"]]
    return {**wl, "items": items}


@router.post("/{watchlist_id}/symbols")
async def add_symbol(watchlist_id: int, symbol: str, exchange: str = "NSE"):
    global _next_item_id
    wl = _watchlists.get(watchlist_id)
    if not wl:
        raise HTTPException(404, "Watchlist not found")
    sym = symbol.upper()
    if any(i["symbol"] == sym for i in wl["items"]):
        raise HTTPException(400, "Symbol already in watchlist")
    item = {
        "id": _next_item_id, "symbol": sym,
        "exchange": exchange, "instrument_type": "EQ",
    }
    _next_item_id += 1
    wl["items"].append(item)
    quote = await market_service.get_quote(sym, exchange)
    return {"success": True, "item": {**item, "quote": quote}}


@router.delete("/{watchlist_id}/symbols/{symbol}")
async def remove_symbol(watchlist_id: int, symbol: str):
    wl = _watchlists.get(watchlist_id)
    if not wl:
        raise HTTPException(404, "Watchlist not found")
    wl["items"] = [i for i in wl["items"] if i["symbol"] != symbol.upper()]
    return {"success": True}
