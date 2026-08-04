"""
User model
"""
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Trading preferences
    paper_trading = Column(Boolean, default=True)
    paper_capital = Column(Float, default=100000.0)
    live_trading_enabled = Column(Boolean, default=False)
    risk_per_trade = Column(Float, default=1.0)  # % of capital

    # Broker connections (encrypted credentials stored as JSON)
    broker_config = Column(JSON, default=dict)
    active_broker = Column(String(50), nullable=True)  # dhan|angel|zerodha|upstox|paper

    # Settings
    settings = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
