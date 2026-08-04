"""
Trading journal model
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=True)
    symbol = Column(String(50), nullable=True)
    title = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)
    emotion = Column(String(50), nullable=True)  # confident|fearful|greedy|disciplined|fomo
    setup_type = Column(String(100), nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5 self rating
    lessons = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    pnl = Column(Float, nullable=True)
    screenshots = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
