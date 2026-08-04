"""Portfolio — analysis only (no trading)"""
from fastapi import APIRouter
from app.services.dhan_live import dhan_client

router = APIRouter()


@router.get("/")
async def get_portfolio():
    st = await dhan_client.status()
    return {
        "trading_enabled": False,
        "message": "Analysis-only. No positions.",
        "total_capital": 0,
        "available_capital": 0,
        "invested": 0,
        "today_pnl": 0,
        "today_pnl_percent": 0,
        "total_pnl": 0,
        "open_positions": 0,
        "live_data": st.get("configured", False),
        "data_provider": "dhan",
        "positions": [],
    }


@router.get("/positions")
async def get_positions():
    return {"positions": [], "trading_enabled": False}


@router.get("/performance")
async def get_performance():
    return {"trading_enabled": False, "today_pnl": 0, "total_pnl": 0}
