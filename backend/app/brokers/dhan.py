"""
Dhan API Broker Adapter
Requires: dhanhq package and valid client_id + access_token
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.brokers.base import BaseBroker, BrokerQuote, BrokerOrderResult, BrokerFactory
from app.core.config import settings
from loguru import logger


class DhanBroker(BaseBroker):
    """Dhan HQ API integration."""

    name = "dhan"

    def __init__(self, credentials: Dict[str, Any] | None = None):
        super().__init__(credentials)
        self.client_id = (credentials or {}).get("client_id") or settings.DHAN_CLIENT_ID
        self.access_token = (credentials or {}).get("access_token") or settings.DHAN_ACCESS_TOKEN
        self._client = None

    async def connect(self) -> bool:
        if not self.client_id or not self.access_token:
            logger.warning("Dhan credentials missing")
            return False
        try:
            from dhanhq import dhanhq
            self._client = dhanhq(self.client_id, self.access_token)
            self.connected = True
            logger.info("Dhan broker connected")
            return True
        except Exception as e:
            logger.error(f"Dhan connect failed: {e}")
            return False

    async def disconnect(self) -> None:
        self._client = None
        self.connected = False

    async def get_quote(self, symbol: str, exchange: str = "NSE") -> BrokerQuote:
        # Map to Dhan security id via instruments master in production
        # Placeholder structure — wire security_id lookup when live
        if not self._client:
            raise RuntimeError("Dhan not connected")
        # Example: self._client.ohlc_data(...)
        return BrokerQuote(symbol=symbol.upper(), ltp=0.0, timestamp=datetime.utcnow())

    async def get_quotes(self, symbols: List[str], exchange: str = "NSE") -> List[BrokerQuote]:
        return [await self.get_quote(s, exchange) for s in symbols]

    async def get_historical(
        self, symbol: str, interval: str, from_date: str, to_date: str, exchange: str = "NSE"
    ) -> List[Dict[str, Any]]:
        if not self._client:
            return []
        # self._client.intraday_minute_data / historical_daily_data
        return []

    async def place_order(
        self, symbol: str, side: str, quantity: int, order_type: str = "MARKET",
        price: Optional[float] = None, trigger_price: Optional[float] = None,
        exchange: str = "NSE", product: str = "INTRADAY",
    ) -> BrokerOrderResult:
        if not self._client:
            return BrokerOrderResult(success=False, message="Dhan not connected", status="REJECTED")
        try:
            # Wire dhanhq place_order with security_id, transaction_type, etc.
            return BrokerOrderResult(success=False, message="Configure security_id mapping for live orders", status="REJECTED")
        except Exception as e:
            return BrokerOrderResult(success=False, message=str(e), status="REJECTED")

    async def cancel_order(self, order_id: str) -> BrokerOrderResult:
        if not self._client:
            return BrokerOrderResult(success=False, message="Not connected", status="REJECTED")
        try:
            self._client.cancel_order(order_id)
            return BrokerOrderResult(success=True, order_id=order_id, status="CANCELLED")
        except Exception as e:
            return BrokerOrderResult(success=False, message=str(e), status="REJECTED")

    async def get_positions(self) -> List[Dict[str, Any]]:
        if not self._client:
            return []
        try:
            return self._client.get_positions() or []
        except Exception:
            return []

    async def get_orders(self) -> List[Dict[str, Any]]:
        if not self._client:
            return []
        try:
            return self._client.get_order_list() or []
        except Exception:
            return []


BrokerFactory.register("dhan", DhanBroker)
