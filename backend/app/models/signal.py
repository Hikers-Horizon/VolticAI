"""
AI Signal model
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(20), default="NSE")
    action = Column(String(10), nullable=False)  # BUY | SELL | WAIT
    confidence = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    target_1 = Column(Float, nullable=True)
    target_2 = Column(Float, nullable=True)
    target_3 = Column(Float, nullable=True)
    risk_reward = Column(Float, nullable=True)
    timeframe = Column(String(20), default="5minute")
    reason = Column(Text, nullable=True)
    analysis = Column(JSON, default=dict)  # detailed factor scores
    status = Column(String(20), default="ACTIVE")  # ACTIVE|HIT_T1|HIT_T2|HIT_T3|SL_HIT|EXPIRED
    is_valid = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
