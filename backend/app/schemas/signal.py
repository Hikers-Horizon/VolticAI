"""
AI Signal schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class FactorScore(BaseModel):
    name: str
    score: float  # 0-100
    weight: float
    detail: str


class NewsItem(BaseModel):
    title: str
    link: str = ""
    source: str = ""
    published: str = ""
    sentiment: float = 0.0
    bias: str = "NEUTRAL"


class AnalysisResult(BaseModel):
    symbol: str
    action: str  # BUY | SELL | WAIT
    confidence: float
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target_1: Optional[float] = None
    target_2: Optional[float] = None
    target_3: Optional[float] = None
    risk_reward: Optional[float] = None
    timeframe: str = "5minute"
    reason: str = ""
    factors: List[FactorScore] = []
    analysis: Dict[str, Any] = {}
    is_tradeable: bool = False
    rejection_reasons: List[str] = []
    # Full research package (publish-ready)
    summary: str = ""
    thesis: str = ""
    invalidation: str = ""
    history_summary: str = ""
    news_bias: str = "NEUTRAL"
    news: List[NewsItem] = []
    multi_tf: Dict[str, Any] = {}
    quote: Dict[str, Any] = {}
    publish_text: str = ""
    generated_at: Optional[str] = None
    capital: float = 10000.0
    quantity: int = 0
    position_value: float = 0.0
    risk_amount: float = 0.0
    reward_t1: float = 0.0
    reward_t2: float = 0.0
    reward_t3: float = 0.0
    setup_grade: str = ""
    groww_plan: str = ""
    trade_plan: str = ""
    disclaimer: str = (
        "AI recommendations are probabilistic and not guaranteed. "
        "Past performance does not guarantee future results. "
        "Rs 2000/day profit is NOT guaranteed with Rs 10000 capital. "
        "This is not SEBI-registered advice. You are solely responsible for trades you take or publish."
    )


class SignalCreate(BaseModel):
    symbol: str
    action: str
    confidence: float
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target_1: Optional[float] = None
    target_2: Optional[float] = None
    target_3: Optional[float] = None
    risk_reward: Optional[float] = None
    timeframe: str = "5minute"
    reason: Optional[str] = None
    analysis: Dict[str, Any] = {}


class SignalResponse(BaseModel):
    id: int
    symbol: str
    exchange: str = "NSE"
    action: str
    confidence: float
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target_1: Optional[float] = None
    target_2: Optional[float] = None
    target_3: Optional[float] = None
    risk_reward: Optional[float] = None
    timeframe: str
    reason: Optional[str] = None
    analysis: Dict[str, Any] = {}
    status: str
    is_valid: bool
    created_at: Optional[datetime] = None
    disclaimer: str = (
        "AI recommendations are probabilistic and not guaranteed. Trade at your own risk."
    )

    class Config:
        from_attributes = True
