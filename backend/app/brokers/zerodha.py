"""
Zerodha Kite Connect Broker Adapter
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.brokers.base import BaseBroker, BrokerQuote, BrokerOrderResult, BrokerFactory
from app.core.config import settings
from loguru import logger


class ZerodhaBroker(BaseBroker):
    name = "zerodha"

    def __init__(self, credentials: Dict[str, Any] | None = None):
        super().__init__(credentials)
        c = credentials or {}
        self.api_key = c.get("api_key") or settings.ZERODHA_API_KEY
        self.api_secret = c.get("api_secret") or settings.ZERODHA_API_SECRET
        self.access_token = c.get("access_token", "")
        self._kite = None

    async def connect(self) -> bool:
        if not self.api_key:
            logger.warning("Zerodha API key missing")
            return False
        try:
            # from kiteconnect import KiteConnect
            # self._kite = KiteConnect(api_key=self.api_key)
            # if self.access_token:
            #     self._kite.set_access_token(self.access_token)
            self.connected = True
            logger.info("Zerodha adapter ready (install kiteconnect for live)")
            return True
        except Exception as e:
            logger.error(f"Zerodha connect failed: {e}")
            return False

    async def disconnect(self) -> None:
        self._kite = None
        self.connected = False

    async def get_quote(self, symbol: str, exchange: str = "NSE") -> BrokerQuote:
        return BrokerQuote(symbol=symbol.upper(), ltp=0.0, timestamp=datetime.utcnow())

    async def get_quotes(self, symbols: List[str], exchange: str = "NSE") -> List[BrokerQuote]:
        return [await self.get_quote(s, exchange) for s in symbols]

    async def get_historical(self, symbol, interval, from_date, to_date, exchange="NSE"):
        return []

    async def place_order(self, symbol, side, quantity, order_type="MARKET",
                          price=None, trigger_price=None, exchange="NSE", product="INTRADAY"):
        return BrokerOrderResult(success=False, message="Complete Kite login + instrument token", status="REJECTED")

    async def cancel_order(self, order_id: str) -> BrokerOrderResult:
        return BrokerOrderResult(success=False, message="Not connected", status="REJECTED")

    async def get_positions(self):
        return []

    async def get_orders(self):
        return []


BrokerFactory.register("zerodha", ZerodhaBroker)
