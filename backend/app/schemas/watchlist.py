"""
Watchlist schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.schemas.market import Quote


class WatchlistItemCreate(BaseModel):
    symbol: str
    exchange: str = "NSE"
    instrument_type: str = "EQ"


class WatchlistItemResponse(BaseModel):
    id: int
    symbol: str
    exchange: str = "NSE"
    instrument_type: str = "EQ"
    sort_order: int = 0
    quote: Optional[Quote] = None

    class Config:
        from_attributes = True


class WatchlistCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class WatchlistResponse(BaseModel):
    id: int
    name: str
    is_default: bool = False
    items: List[WatchlistItemResponse] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
