"""Settings / Dhan credentials (data only, no trading)"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from pathlib import Path
import re
from app.core.config import settings
from app.services.dhan_live import dhan_client

router = APIRouter()
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


class DhanConfigBody(BaseModel):
    client_id: str = Field(..., min_length=3)
    access_token: str = Field(..., min_length=20)


def _upsert_env(key: str, value: str):
    text = ENV_PATH.read_text(encoding="utf-8") if ENV_PATH.exists() else ""
    pattern = re.compile(rf"^{re.escape(key)}=.*$", re.M)
    line = f"{key}={value}"
    if pattern.search(text):
        text = pattern.sub(line, text)
    else:
        text = text.rstrip() + f"\n{line}\n"
    ENV_PATH.write_text(text, encoding="utf-8")


@router.get("/dhan")
async def get_dhan_status():
    st = await dhan_client.status()
    return {
        **st,
        "client_id_preview": (settings.DHAN_CLIENT_ID[:4] + "…") if settings.DHAN_CLIENT_ID else None,
        "token_preview": (settings.DHAN_ACCESS_TOKEN[:12] + "…") if settings.DHAN_ACCESS_TOKEN else None,
        "trading_enabled": False,
        "note": "Analysis-only. Paste full Access Token from Dhan web → API → Access Token.",
    }


@router.post("/dhan")
async def set_dhan_credentials(body: DhanConfigBody):
    """Save Dhan Data API credentials and hot-reload client."""
    client_id = body.client_id.strip()
    token = body.access_token.strip()
    if token.count(".") < 2 and len(token) < 40:
        raise HTTPException(400, "Access token looks truncated. Paste the FULL JWT from Dhan.")

    _upsert_env("DHAN_CLIENT_ID", client_id)
    _upsert_env("DHAN_ACCESS_TOKEN", token)

    settings.DHAN_CLIENT_ID = client_id
    settings.DHAN_ACCESS_TOKEN = token
    dhan_client.client_id = client_id
    dhan_client.access_token = token
    dhan_client._quote_cache.clear()

    try:
        q = await dhan_client.get_quote("RELIANCE")
        return {
            "success": True,
            "message": "Dhan live data connected",
            "sample": {"symbol": q.get("symbol"), "ltp": q.get("ltp"), "source": q.get("source")},
            "trading_enabled": False,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Credentials saved but quote test failed: {e}",
            "hint": "Confirm Client ID + full Access Token. Token expires ~24h — regenerate on Dhan.",
            "trading_enabled": False,
        }
