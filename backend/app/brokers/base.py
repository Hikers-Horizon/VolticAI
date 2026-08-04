"""
Abstract broker interface — pluggable for Dhan, Angel One, Zerodha, Upstox
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BrokerQuote:
    symbol: str
    ltp: float
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: int = 0
    bid: float = 0.0
    ask: float = 0.0
    oi: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BrokerOrderResult:
    success: bool
    order_id: Optional[str] = None
    message: str = ""
    filled_qty: int = 0
    avg_price: float = 0.0
    status: str = "PENDING"


class BaseBroker(ABC):
    """Unified broker interface. All brokers implement this contract."""

    name: str = "base"

    def __init__(self, credentials: Dict[str, Any] | None = None):
        self.credentials = credentials or {}
        self.connected = False

    @abstractmethod
    async def connect(self) -> bool:
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        ...

    @abstractmethod
    async def get_quote(self, symbol: str, exchange: str = "NSE") -> BrokerQuote:
        ...

    @abstractmethod
    async def get_quotes(self, symbols: List[str], exchange: str = "NSE") -> List[BrokerQuote]:
        ...

    @abstractmethod
    async def get_historical(
        self, symbol: str, interval: str, from_date: str, to_date: str, exchange: str = "NSE"
    ) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        order_type: str = "MARKET",
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        exchange: str = "NSE",
        product: str = "INTRADAY",
    ) -> BrokerOrderResult:
        ...

    @abstractmethod
    async def cancel_order(self, order_id: str) -> BrokerOrderResult:
        ...

    @abstractmethod
    async def get_positions(self) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    async def get_orders(self) -> List[Dict[str, Any]]:
        ...

    async def get_funds(self) -> Dict[str, float]:
        return {"available": 0.0, "used": 0.0, "total": 0.0}


class BrokerFactory:
    """Factory to instantiate broker adapters."""

    _registry: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str, broker_cls: type):
        cls._registry[name.lower()] = broker_cls

    @classmethod
    def create(cls, name: str, credentials: Dict[str, Any] | None = None) -> BaseBroker:
        key = name.lower()
        if key not in cls._registry:
            raise ValueError(f"Unknown broker: {name}. Available: {list(cls._registry)}")
        return cls._registry[key](credentials)

    @classmethod
    def available(cls) -> List[str]:
        return list(cls._registry.keys())
