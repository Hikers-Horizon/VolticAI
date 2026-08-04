"""
Portfolio schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class OrderCreate(BaseModel):
    symbol: str
    exchange: str = "NSE"
    side: str  # BUY | SELL
    order_type: str = "MARKET"
    quantity: int = Field(..., gt=0)
    price: Optional[float] = None
    trigger_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target: Optional[float] = None
    is_paper: bool = True


class OrderResponse(BaseModel):
    id: int
    symbol: str
    side: str
    order_type: str
    quantity: int
    price: Optional[float] = None
    status: str
    filled_quantity: int = 0
    avg_fill_price: float = 0.0
    is_paper: bool = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PositionResponse(BaseModel):
    id: int
    symbol: str
    exchange: str = "NSE"
    side: str
    quantity: int
    avg_price: float
    ltp: float = 0.0
    pnl: float = 0.0
    pnl_percent: float = 0.0
    stop_loss: Optional[float] = None
    target: Optional[float] = None
    is_open: bool = True
    is_paper: bool = True
    opened_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TradeResponse(BaseModel):
    id: int
    symbol: str
    side: str
    quantity: int
    price: float
    pnl: float = 0.0
    fees: float = 0.0
    is_paper: bool = True
    executed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PortfolioSummary(BaseModel):
    total_capital: float
    available_capital: float
    invested: float
    today_pnl: float
    today_pnl_percent: float
    total_pnl: float
    open_positions: int
    win_rate: float = 0.0
    total_trades: int = 0
    is_paper: bool = True
    positions: List[PositionResponse] = []
