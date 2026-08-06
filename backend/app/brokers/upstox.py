"""
Upstox API Broker Adapter
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.brokers.base import BaseBroker, BrokerQuote, BrokerOrderResult, BrokerFactory
from app.core.config import settings
from loguru import logger


from app.services.upstox_live import upstox_client


class UpstoxBroker(BaseBroker):
    name = "upstox"

    def __init__(self, credentials: Dict[str, Any] | None = None):
        super().__init__(credentials)
        c = credentials or {}
        self.api_key = c.get("api_key") or settings.UPSTOX_API_KEY
        self.api_secret = c.get("api_secret") or settings.UPSTOX_API_SECRET
        self.access_token = c.get("access_token") or settings.UPSTOX_ACCESS_TOKEN

    async def connect(self) -> bool:
        if upstox_client.configured:
            self.connected = True
            logger.info("Upstox adapter connected successfully.")
            return True
        logger.warning("Upstox Access Token missing")
        return False

    async def disconnect(self) -> None:
        self.connected = False

    async def get_quote(self, symbol: str, exchange: str = "NSE") -> BrokerQuote:
        q = await upstox_client.get_quote(symbol)
        return BrokerQuote(
            symbol=symbol.upper(),
            ltp=q.get("ltp", 0.0),
            open=q.get("open", 0.0),
            high=q.get("high", 0.0),
            low=q.get("low", 0.0),
            close=q.get("close", 0.0),
            volume=q.get("volume", 0),
            change=q.get("change", 0.0),
            change_percent=q.get("change_percent", 0.0),
            timestamp=datetime.utcnow(),
        )

    async def get_quotes(self, symbols: List[str], exchange: str = "NSE") -> List[BrokerQuote]:
        raw_quotes = await upstox_client.get_quotes(symbols)
        return [
            BrokerQuote(
                symbol=q.get("symbol", "").upper(),
                ltp=q.get("ltp", 0.0),
                open=q.get("open", 0.0),
                high=q.get("high", 0.0),
                low=q.get("low", 0.0),
                close=q.get("close", 0.0),
                volume=q.get("volume", 0),
                change=q.get("change", 0.0),
                change_percent=q.get("change_percent", 0.0),
                timestamp=datetime.utcnow(),
            )
            for q in raw_quotes
        ]

    async def get_historical(self, symbol, interval="5minute", from_date=None, to_date=None, exchange="NSE"):
        return await upstox_client.get_historical(symbol, interval)

    async def place_order(self, symbol, side, quantity, order_type="MARKET",
                          price=None, trigger_price=None, exchange="NSE", product="INTRADAY"):
        return BrokerOrderResult(success=False, message="Order placement disabled in analysis mode", status="REJECTED")

    async def cancel_order(self, order_id: str) -> BrokerOrderResult:
        return BrokerOrderResult(success=False, message="Not connected", status="REJECTED")

    async def get_positions(self):
        return []

    async def get_orders(self):
        return []


BrokerFactory.register("upstox", UpstoxBroker)
