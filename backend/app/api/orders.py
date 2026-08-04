"""
Orders are DISABLED — this platform is analysis-only (no buy/sell).
"""
from fastapi import APIRouter, HTTPException
from app.services.dhan_live import dhan_client

router = APIRouter()

DISABLED_MSG = (
    "Order placement is disabled. This platform provides live market data "
    "and AI analysis only. Users cannot buy or sell stocks here."
)


@router.get("/")
async def list_orders():
    return {"orders": [], "trading_enabled": False, "message": DISABLED_MSG}


@router.post("/")
async def place_order():
    raise HTTPException(status_code=403, detail=DISABLED_MSG)


@router.delete("/{order_id}")
async def cancel_order(order_id: str):
    raise HTTPException(status_code=403, detail=DISABLED_MSG)


@router.get("/brokers")
async def list_brokers():
    st = await dhan_client.status()
    return {
        "data_provider": "dhan",
        "trading_enabled": False,
        "live_data": st.get("configured", False),
        "message": DISABLED_MSG,
    }
