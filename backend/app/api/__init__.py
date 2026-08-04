"""
API Routes
"""
from fastapi import APIRouter
from app.api import auth, market, signals, watchlist, portfolio, orders, ws, admin
from app.api import settings as settings_api

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(market.router, prefix="/market", tags=["Market Data"])
api_router.include_router(signals.router, prefix="/signals", tags=["AI Signals"])
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["Watchlist"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
api_router.include_router(ws.router, prefix="/ws", tags=["WebSocket"])
api_router.include_router(settings_api.router, prefix="/settings", tags=["Settings"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
