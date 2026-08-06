"""
Application configuration
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Union
import json


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DATABASE_URL: str = "postgresql://trading_user:trading_pass@localhost:5432/trading_platform"
    DB_ECHO: bool = False

    REDIS_URL: str = "redis://localhost:6379"
    REDIS_DB: int = 0

    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:4000",
        "http://127.0.0.1:4000",
    ]

    DHAN_CLIENT_ID: str = ""
    DHAN_ACCESS_TOKEN: str = ""
    ANGEL_CLIENT_ID: str = ""
    ANGEL_API_KEY: str = ""
    ANGEL_PASSWORD: str = ""
    ANGEL_TOTP_SECRET: str = ""
    ZERODHA_API_KEY: str = ""
    ZERODHA_API_SECRET: str = ""
    UPSTOX_API_KEY: str = ""
    UPSTOX_API_SECRET: str = ""
    UPSTOX_ACCESS_TOKEN: str = ""

    PAPER_TRADING_ENABLED: bool = True
    PAPER_TRADING_CAPITAL: float = 100000.0

    AI_MIN_CONFIDENCE: float = 75.0
    AI_MIN_RISK_REWARD: float = 2.0

    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/trading.log"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [o.strip() for o in v.split(",") if o.strip()]
        return v


settings = Settings()
