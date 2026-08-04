"""
Market data schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Quote(BaseModel):
    symbol: str
    exchange: str = "NSE"
    ltp: float = 0.0
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: int = 0
    change: float = 0.0
    change_percent: float = 0.0
    vwap: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    bid_qty: Optional[int] = None
    ask_qty: Optional[int] = None
    oi: Optional[int] = None
    timestamp: Optional[datetime] = None


class OHLCV(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    oi: Optional[int] = None


class MarketStatus(BaseModel):
    is_open: bool
    status: str
    current_time: str
    market_open: str = "09:15"
    market_close: str = "15:30"
    india_vix: Optional[float] = None


class OptionStrike(BaseModel):
    strike: float
    ce_ltp: Optional[float] = None
    ce_oi: Optional[int] = None
    ce_volume: Optional[int] = None
    ce_iv: Optional[float] = None
    pe_ltp: Optional[float] = None
    pe_oi: Optional[int] = None
    pe_volume: Optional[int] = None
    pe_iv: Optional[float] = None


class OptionsChain(BaseModel):
    symbol: str
    expiry: str
    spot: float
    strikes: List[OptionStrike] = []
    pcr: Optional[float] = None
    max_pain: Optional[float] = None
