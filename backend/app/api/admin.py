"""
Admin endpoints for managing API credentials
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal
import os
from pathlib import Path

router = APIRouter()

class CredentialsInput(BaseModel):
    provider: str = "upstox"
    dhan_client_id: str = ""
    dhan_access_token: str = ""
    dhan_api_key: str = ""
    dhan_api_secret: str = ""
    upstox_api_key: str = ""
    upstox_api_secret: str = ""
    upstox_access_token: str = ""
    angelone_api_key: str = ""
    angelone_client_code: str = ""
    angelone_access_token: str = ""

@router.post("/credentials")
async def save_credentials(creds: CredentialsInput):
    """Save API credentials to .env file"""
    try:
        env_path = Path(__file__).parent.parent.parent / ".env"
        
        # Read current .env
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()
        else:
            lines = []
        
        # Update credentials
        env_dict = {}
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_dict[key] = value
        
        # Update based on provider
        env_dict['MARKET_PROVIDER'] = creds.provider.upper()
        
        # Always update credentials if provided
        if creds.upstox_api_key:
            env_dict['UPSTOX_API_KEY'] = creds.upstox_api_key
        if creds.upstox_api_secret:
            env_dict['UPSTOX_API_SECRET'] = creds.upstox_api_secret
        if creds.upstox_access_token:
            env_dict['UPSTOX_ACCESS_TOKEN'] = creds.upstox_access_token
            from app.core.config import settings
            from app.services.upstox_live import upstox_client
            settings.UPSTOX_ACCESS_TOKEN = creds.upstox_access_token
            upstox_client.reset_auth_status()

        if creds.angelone_api_key:
            env_dict['ANGELONE_API_KEY'] = creds.angelone_api_key
        if creds.angelone_client_code:
            env_dict['ANGELONE_CLIENT_CODE'] = creds.angelone_client_code
        if creds.angelone_access_token:
            env_dict['ANGELONE_ACCESS_TOKEN'] = creds.angelone_access_token

        if creds.dhan_client_id:
            env_dict['DHAN_CLIENT_ID'] = creds.dhan_client_id
        if creds.dhan_access_token:
            env_dict['DHAN_ACCESS_TOKEN'] = creds.dhan_access_token
            from app.core.config import settings
            settings.DHAN_ACCESS_TOKEN = creds.dhan_access_token
        
        # Write back to .env
        with open(env_path, 'w') as f:
            for key, value in env_dict.items():
                f.write(f"{key}={value}\n")
        
        return {
            "success": True,
            "message": "Credentials saved and updated live successfully.",
            "provider": creds.provider
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save credentials: {str(e)}")

@router.get("/credentials")
async def get_credentials():
    """Get current credentials (masked)"""
    try:
        env_path = Path(__file__).parent.parent.parent / ".env"
        
        if not env_path.exists():
            return {"provider": "dhan", "configured": False}
        
        env_dict = {}
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_dict[key] = value
        
        provider = env_dict.get('MARKET_PROVIDER', 'DHAN').lower()
        
        def mask(s: str) -> str:
            if not s or len(s) < 8:
                return "***"
            return s[:4] + "***" + s[-4:]
        
        return {
            "provider": provider,
            "configured": True,
            "dhan": {
                "client_id": env_dict.get('DHAN_CLIENT_ID', ''),
                "access_token_set": bool(env_dict.get('DHAN_ACCESS_TOKEN')),
                "api_key": mask(env_dict.get('DHAN_API_KEY', '')),
                "api_secret_set": bool(env_dict.get('DHAN_API_SECRET')),
            },
            "upstox": {
                "api_key": mask(env_dict.get('UPSTOX_API_KEY', '')),
                "api_secret_set": bool(env_dict.get('UPSTOX_API_SECRET')),
                "access_token_set": bool(env_dict.get('UPSTOX_ACCESS_TOKEN')),
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get credentials: {str(e)}")
