"""
Angel One SmartAPI Broker Adapter
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.brokers.base import BaseBroker, BrokerQuote, BrokerOrderResult, BrokerFactory
from app.core.config import settings
from loguru import logger


class AngelBroker(BaseBroker):
    name = "angel"

    def __init__(self, credentials: Dict[str, Any] | None = None):
        super().__init__(credentials)
        c = credentials or {}
        self.client_id = c.get("client_id") or settings.ANGEL_CLIENT_ID
        self.api_key = c.get("api_key") or settings.ANGEL_API_KEY
        self.password = c.get("password") or settings.ANGEL_PASSWORD
        self.totp_secret = c.get("totp_secret") or settings.ANGEL_TOTP_SECRET
        self._client = None

    async def connect(self) -> bool:
        if not all([self.client_id, self.api_key, self.password]):
            logger.warning("Angel One credentials missing")
            return False
        try:
            # from SmartApi import SmartConnect
            # import pyotp
            # self._client = SmartConnect(api_key=self.api_key)
            # totp = pyotp.TOTP(self.totp_secret).now()
            # self._client.generateSession(self.client_id, self.password, totp)
            self.connected = True
            logger.info("Angel One adapter ready (install smartapi-python + pyotp for live)")
            return True
        except Exception as e:
            logger.error(f"Angel connect failed: {e}")
            return False

    async def disconnect(self) -> None:
        self._client = None
        self.connected = False

    async def get_quote(self, symbol: str, exchange: str = "NSE") -> BrokerQuote:
        return BrokerQuote(symbol=symbol.upper(), ltp=0.0, timestamp=datetime.utcnow())

    async def get_quotes(self, symbols: List[str], exchange: str = "NSE") -> List[BrokerQuote]:
        return [await self.get_quote(s, exchange) for s in symbols]

    async def get_historical(self, symbol, interval, from_date, to_date, exchange="NSE"):
        return []

    async def place_order(self, symbol, side, quantity, order_type="MARKET",
                          price=None, trigger_price=None, exchange="NSE", product="INTRADAY"):
        return BrokerOrderResult(success=False, message="Configure Angel token map for live", status="REJECTED")

    async def cancel_order(self, order_id: str) -> BrokerOrderResult:
        return BrokerOrderResult(success=False, message="Not connected", status="REJECTED")

    async def get_positions(self):
        return []

    async def get_orders(self):
        return []


BrokerFactory.register("angel", AngelBroker)
