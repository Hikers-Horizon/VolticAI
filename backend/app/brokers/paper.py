"""
Paper Trading Broker — default safe mode with simulated fills
"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.brokers.base import BaseBroker, BrokerQuote, BrokerOrderResult, BrokerFactory
from app.core.config import settings


# Demo LTP prices for paper trading (updated by market data when available)
DEMO_PRICES: Dict[str, float] = {
    "RELIANCE": 3082.0, "TCS": 4125.0, "INFY": 1850.0, "HDFCBANK": 1680.0,
    "ICICIBANK": 1250.0, "SBIN": 820.0, "BHARTIARTL": 1580.0, "ITC": 475.0,
    "KOTAKBANK": 1780.0, "LT": 3650.0, "NIFTY": 24500.0, "BANKNIFTY": 52000.0,
    "FINNIFTY": 23500.0, "WIPRO": 295.0, "AXISBANK": 1150.0, "BAJFINANCE": 7200.0,
    "MARUTI": 12500.0, "TATAMOTORS": 980.0, "SUNPHARMA": 1750.0, "TITAN": 3400.0,
}


class PaperBroker(BaseBroker):
    """Simulated broker for paper trading. No real orders are placed."""

    name = "paper"

    def __init__(self, credentials: Dict[str, Any] | None = None):
        super().__init__(credentials)
        self.capital = float(
            (credentials or {}).get("capital", settings.PAPER_TRADING_CAPITAL)
        )
        self.available = self.capital
        self._orders: List[Dict[str, Any]] = []
        self._positions: Dict[str, Dict[str, Any]] = {}
        self._prices = dict(DEMO_PRICES)

    async def connect(self) -> bool:
        self.connected = True
        return True

    async def disconnect(self) -> None:
        self.connected = False

    def set_price(self, symbol: str, price: float):
        self._prices[symbol.upper()] = price

    async def get_quote(self, symbol: str, exchange: str = "NSE") -> BrokerQuote:
        sym = symbol.upper()
        ltp = self._prices.get(sym, 1000.0)
        # Synthetic OHLC
        return BrokerQuote(
            symbol=sym, ltp=ltp, open=ltp * 0.995, high=ltp * 1.01,
            low=ltp * 0.99, close=ltp * 0.998, volume=1_000_000,
            bid=ltp - 0.05, ask=ltp + 0.05, timestamp=datetime.utcnow(),
        )

    async def get_quotes(self, symbols: List[str], exchange: str = "NSE") -> List[BrokerQuote]:
        return [await self.get_quote(s, exchange) for s in symbols]

    async def get_historical(
        self, symbol: str, interval: str, from_date: str, to_date: str, exchange: str = "NSE"
    ) -> List[Dict[str, Any]]:
        """Generate synthetic OHLCV for paper/demo charts."""
        import numpy as np
        import pandas as pd
        sym = symbol.upper()
        base = self._prices.get(sym, 1000.0)
        periods = {"1minute": 375, "3minute": 125, "5minute": 75, "15minute": 25,
                   "30minute": 13, "1hour": 7}.get(interval, 75)
        np.random.seed(hash(sym) % 2**31)
        rets = np.random.normal(0, 0.002, periods)
        closes = base * np.cumprod(1 + rets)
        data = []
        now = pd.Timestamp.now().floor("min")
        delta = pd.Timedelta(minutes=int(interval.replace("minute", "").replace("hour", "60") or 5))
        for i, c in enumerate(closes):
            o = c * (1 + np.random.uniform(-0.001, 0.001))
            h = max(o, c) * (1 + abs(np.random.normal(0, 0.001)))
            l = min(o, c) * (1 - abs(np.random.normal(0, 0.001)))
            data.append({
                "timestamp": (now - delta * (periods - i)).isoformat(),
                "open": round(float(o), 2), "high": round(float(h), 2),
                "low": round(float(l), 2), "close": round(float(c), 2),
                "volume": int(np.random.randint(50000, 500000)),
            })
        self._prices[sym] = float(closes[-1])
        return data

    async def place_order(
        self, symbol: str, side: str, quantity: int, order_type: str = "MARKET",
        price: Optional[float] = None, trigger_price: Optional[float] = None,
        exchange: str = "NSE", product: str = "INTRADAY",
    ) -> BrokerOrderResult:
        sym = symbol.upper()
        q = await self.get_quote(sym, exchange)
        fill_price = price if order_type == "LIMIT" and price else q.ltp
        cost = fill_price * quantity
        if side.upper() == "BUY" and cost > self.available:
            return BrokerOrderResult(success=False, message="Insufficient paper capital", status="REJECTED")

        oid = f"PAPER-{uuid.uuid4().hex[:10].upper()}"
        order = {
            "order_id": oid, "symbol": sym, "side": side.upper(), "quantity": quantity,
            "price": fill_price, "status": "COMPLETE", "filled_qty": quantity,
            "avg_price": fill_price, "timestamp": datetime.utcnow().isoformat(),
        }
        self._orders.append(order)

        # Update positions
        pos = self._positions.get(sym)
        if side.upper() == "BUY":
            self.available -= cost
            if pos and pos["side"] == "BUY":
                total_qty = pos["quantity"] + quantity
                pos["avg_price"] = (pos["avg_price"] * pos["quantity"] + fill_price * quantity) / total_qty
                pos["quantity"] = total_qty
            else:
                self._positions[sym] = {
                    "symbol": sym, "side": "BUY", "quantity": quantity,
                    "avg_price": fill_price, "ltp": fill_price,
                }
        else:  # SELL
            if pos and pos["side"] == "BUY":
                pnl = (fill_price - pos["avg_price"]) * min(quantity, pos["quantity"])
                self.available += fill_price * min(quantity, pos["quantity"])
                pos["quantity"] -= quantity
                if pos["quantity"] <= 0:
                    del self._positions[sym]
            else:
                self._positions[sym] = {
                    "symbol": sym, "side": "SELL", "quantity": quantity,
                    "avg_price": fill_price, "ltp": fill_price,
                }

        return BrokerOrderResult(
            success=True, order_id=oid, message="Paper order filled",
            filled_qty=quantity, avg_price=fill_price, status="COMPLETE",
        )

    async def cancel_order(self, order_id: str) -> BrokerOrderResult:
        return BrokerOrderResult(success=False, message="Paper market orders fill instantly", status="REJECTED")

    async def get_positions(self) -> List[Dict[str, Any]]:
        result = []
        for sym, pos in self._positions.items():
            q = await self.get_quote(sym)
            pos["ltp"] = q.ltp
            mult = 1 if pos["side"] == "BUY" else -1
            pos["pnl"] = (q.ltp - pos["avg_price"]) * pos["quantity"] * mult
            pos["pnl_percent"] = ((q.ltp - pos["avg_price"]) / pos["avg_price"]) * 100 * mult
            result.append(pos)
        return result

    async def get_orders(self) -> List[Dict[str, Any]]:
        return list(self._orders)

    async def get_funds(self) -> Dict[str, float]:
        used = self.capital - self.available
        return {"available": self.available, "used": used, "total": self.capital}


# Register paper broker
BrokerFactory.register("paper", PaperBroker)
