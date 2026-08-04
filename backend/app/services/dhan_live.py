"""
Live Dhan Data API client (quotes + historical). No order placement.
"""
from __future__ import annotations
import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import httpx
import pandas as pd
from loguru import logger
from app.core.config import settings
from app.services.instruments import instrument_master

BASE = "https://api.dhan.co/v2"

# Map our TF labels → Dhan interval minutes (supported: 1,5,15,25,60)
INTERVAL_MAP = {
    "1minute": "1",
    "3minute": "5",   # closest available
    "5minute": "5",
    "15minute": "15",
    "30minute": "25",  # closest
    "1hour": "60",
}


class DhanLiveClient:
    def __init__(self):
        self.client_id = settings.DHAN_CLIENT_ID
        self.access_token = settings.DHAN_ACCESS_TOKEN
        self._lock = asyncio.Lock()
        self._last_req = 0.0  # soft rate limit for marketfeed
        self._quote_cache: Dict[str, Tuple[float, dict]] = {}
        self._hist_cache: Dict[str, Tuple[float, List[dict]]] = {}
        self._cache_ttl = 2.0       # quote cache — 2s for paid API (fast refresh)
        self._hist_ttl = 30.0       # historical cache
        self._http: Optional[httpx.AsyncClient] = None
        self._auth_bad_until = 0.0
        self._rate_limited_until = 0.0
        self.last_error: Optional[str] = None

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.access_token and len(self.access_token) > 20)

    def _blocked(self) -> Optional[str]:
        now = time.monotonic()
        if now < self._auth_bad_until:
            return "Dhan auth failed — refresh access token in Settings"
        if now < self._rate_limited_until:
            return "Dhan rate-limited — wait a minute and retry"
        return None

    def _headers(self) -> dict:
        return {
            "access-token": self.access_token,
            "client-id": self.client_id,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(
                timeout=httpx.Timeout(12.0, connect=4.0),
                headers=self._headers(),
                http2=False,
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            )
        else:
            # refresh auth headers if credentials hot-reloaded
            self._http.headers.update(self._headers())
        return self._http

    async def _throttle(self, min_interval: float = 0.35):
        """Soft throttle — keep under Dhan limits without 1s hard sleep."""
        async with self._lock:
            now = time.monotonic()
            wait = min_interval - (now - self._last_req)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_req = time.monotonic()

    async def _post(self, path: str, body: dict, throttle: bool = True) -> dict:
        if not self.configured:
            raise RuntimeError("Dhan credentials not configured")
        blocked = self._blocked()
        if blocked:
            raise RuntimeError(blocked)
        if throttle:
            await self._throttle(0.45)
        client = await self._client()
        url = f"{BASE}{path}"
        r = await client.post(url, json=body)
        if r.status_code == 401:
            self._auth_bad_until = time.monotonic() + 120.0
            self.last_error = "auth_failed"
            logger.error(f"Dhan {path} 401: {r.text[:200]}")
            raise RuntimeError("Dhan auth failed — refresh access token")
        if r.status_code == 429:
            self._rate_limited_until = time.monotonic() + 45.0
            self.last_error = "rate_limited"
            logger.error(f"Dhan {path} 429 rate limited")
            raise RuntimeError("Dhan rate-limited — wait and retry")
        if r.status_code >= 400:
            self.last_error = f"http_{r.status_code}"
            logger.error(f"Dhan {path} {r.status_code}: {r.text[:300]}")
            raise RuntimeError(f"Dhan API error {r.status_code}")
        self.last_error = None
        return r.json()

    async def ensure_ready(self):
        await instrument_master.ensure_loaded()

    async def get_quote(self, symbol: str) -> dict:
        await self.ensure_ready()
        sym = symbol.upper()
        cached = self._quote_cache.get(sym)
        if cached and time.monotonic() - cached[0] < self._cache_ttl:
            return cached[1]

        resolved = instrument_master.resolve(sym)
        if not resolved:
            raise ValueError(f"Unknown symbol: {sym}")
        sid, segment, _inst = resolved

        data = await self._post("/marketfeed/quote", {segment: [int(sid)]})
        payload = (data.get("data") or {}).get(segment, {}).get(str(sid)) or {}
        if not payload:
            # try OHLC fallback
            data = await self._post("/marketfeed/ohlc", {segment: [int(sid)]})
            payload = (data.get("data") or {}).get(segment, {}).get(str(sid)) or {}

        ohlc = payload.get("ohlc") or {}
        ltp = float(payload.get("last_price") or 0)
        close = float(ohlc.get("close") or ltp or 0)
        change = float(payload.get("net_change") or (ltp - close if close else 0))
        change_pct = (change / close * 100) if close else 0.0

        depth = payload.get("depth") or {}
        buy = (depth.get("buy") or [{}])[0] if depth.get("buy") else {}
        sell = (depth.get("sell") or [{}])[0] if depth.get("sell") else {}

        q = {
            "symbol": sym,
            "exchange": "NSE",
            "security_id": sid,
            "segment": segment,
            "ltp": ltp,
            "open": float(ohlc.get("open") or 0),
            "high": float(ohlc.get("high") or 0),
            "low": float(ohlc.get("low") or 0),
            "close": close,
            "volume": int(payload.get("volume") or 0),
            "change": round(change, 2),
            "change_percent": round(change_pct, 2),
            "vwap": float(payload.get("average_price") or 0) or None,
            "bid": float(buy.get("price") or 0) or None,
            "ask": float(sell.get("price") or 0) or None,
            "bid_qty": int(buy.get("quantity") or 0) or None,
            "ask_qty": int(sell.get("quantity") or 0) or None,
            "oi": int(payload.get("oi") or 0) or None,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "dhan",
        }
        self._quote_cache[sym] = (time.monotonic(), q)
        return q

    async def get_quotes(self, symbols: List[str]) -> List[dict]:
        await self.ensure_ready()
        # Group by segment
        groups: Dict[str, List[int]] = {}
        meta: Dict[str, Tuple[str, str]] = {}  # sid -> (symbol, segment)
        for s in symbols:
            r = instrument_master.resolve(s.upper())
            if not r:
                continue
            sid, segment, _ = r
            groups.setdefault(segment, []).append(int(sid))
            meta[str(sid)] = (s.upper(), segment)

        if not groups:
            return []

        body = {seg: ids for seg, ids in groups.items()}
        data: dict = {}
        try:
            data = await self._post("/marketfeed/quote", body)
        except Exception as e1:
            # Do not cascade retries on auth/rate-limit — returns empty
            msg = str(e1).lower()
            if "auth" in msg or "rate-limited" in msg or "rate limited" in msg:
                logger.warning(f"get_quotes aborted: {e1}")
                return []
            try:
                data = await self._post("/marketfeed/ohlc", body)
            except Exception as e2:
                logger.warning(f"get_quotes failed: {e2}")
                return []

        results = []
        raw = data.get("data") or {}
        for segment, instruments in raw.items():
            for sid, payload in (instruments or {}).items():
                sym_seg = meta.get(str(sid))
                if not sym_seg:
                    continue
                sym, _ = sym_seg
                ohlc = payload.get("ohlc") or {}
                ltp = float(payload.get("last_price") or 0)
                close = float(ohlc.get("close") or ltp or 0)
                change = float(payload.get("net_change") or (ltp - close if close else 0))
                change_pct = (change / close * 100) if close else 0.0
                depth = payload.get("depth") or {}
                buy = (depth.get("buy") or [{}])[0] if depth.get("buy") else {}
                sell = (depth.get("sell") or [{}])[0] if depth.get("sell") else {}
                q = {
                    "symbol": sym,
                    "exchange": "NSE",
                    "security_id": str(sid),
                    "segment": segment,
                    "ltp": ltp,
                    "open": float(ohlc.get("open") or 0),
                    "high": float(ohlc.get("high") or 0),
                    "low": float(ohlc.get("low") or 0),
                    "close": close,
                    "volume": int(payload.get("volume") or 0),
                    "change": round(change, 2),
                    "change_percent": round(change_pct, 2),
                    "vwap": float(payload.get("average_price") or 0) or None,
                    "bid": float(buy.get("price") or 0) or None,
                    "ask": float(sell.get("price") or 0) or None,
                    "oi": int(payload.get("oi") or 0) or None,
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "dhan",
                }
                self._quote_cache[sym] = (time.monotonic(), q)
                results.append(q)
        # preserve request order
        order = {s.upper(): i for i, s in enumerate(symbols)}
        results.sort(key=lambda x: order.get(x["symbol"], 999))
        return results

    async def get_historical(
        self, symbol: str, interval: str = "5minute", days: int = 5
    ) -> List[dict]:
        await self.ensure_ready()
        sym = symbol.upper()
        dhan_interval = INTERVAL_MAP.get(interval, "5")
        # For AI we only need ~80–120 bars — pull ~2 sessions max
        days = min(days, 3)
        cache_key = f"{sym}:{dhan_interval}:{days}"
        cached = self._hist_cache.get(cache_key)
        if cached and time.monotonic() - cached[0] < self._hist_ttl:
            return cached[1]

        resolved = instrument_master.resolve(sym)
        if not resolved:
            raise ValueError(f"Unknown symbol: {sym}")
        sid, segment, instrument = resolved

        to_dt = datetime.now()
        from_dt = to_dt - timedelta(days=days)
        body = {
            "securityId": str(sid),
            "exchangeSegment": segment,
            "instrument": instrument,
            "interval": dhan_interval,
            "oi": False,
            "fromDate": from_dt.strftime("%Y-%m-%d 09:15:00"),
            "toDate": to_dt.strftime("%Y-%m-%d %H:%M:%S"),
        }
        data = await self._post("/charts/intraday", body, throttle=False)
        opens = data.get("open") or []
        highs = data.get("high") or []
        lows = data.get("low") or []
        closes = data.get("close") or []
        volumes = data.get("volume") or []
        stamps = data.get("timestamp") or []

        rows = []
        # Keep last 120 bars only — enough for indicators, faster parse
        start = max(0, len(closes) - 120)
        for i in range(start, len(closes)):
            ts = stamps[i] if i < len(stamps) else 0
            try:
                tstr = datetime.utcfromtimestamp(int(ts)).isoformat()
            except Exception:
                tstr = datetime.utcnow().isoformat()
            rows.append({
                "timestamp": tstr,
                "open": float(opens[i]) if i < len(opens) else 0,
                "high": float(highs[i]) if i < len(highs) else 0,
                "low": float(lows[i]) if i < len(lows) else 0,
                "close": float(closes[i]),
                "volume": int(volumes[i]) if i < len(volumes) else 0,
            })
        self._hist_cache[cache_key] = (time.monotonic(), rows)
        return rows

    async def get_ohlcv_df(self, symbol: str, interval: str = "5minute") -> pd.DataFrame:
        rows = await self.get_historical(symbol, interval, days=2)
        if not rows:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.set_index("timestamp")
        return df[["open", "high", "low", "close", "volume"]]

    async def option_chain(self, symbol: str, expiry: Optional[str] = None) -> dict:
        await self.ensure_ready()
        resolved = instrument_master.resolve(symbol.upper())
        if not resolved:
            raise ValueError(f"Unknown symbol: {symbol}")
        sid, segment, _ = resolved
        # Underlying for options: indices use IDX_I
        under_seg = "IDX_I" if segment == "IDX_I" else "NSE_EQ"
        # expiry list
        exp_body = {
            "UnderlyingScrip": int(sid),
            "UnderlyingSeg": under_seg,
        }
        try:
            exp_data = await self._post("/optionchain/expirylist", exp_body, throttle=False)
            expiries = exp_data.get("data") or []
            use_expiry = expiry or (expiries[0] if expiries else None)
            if not use_expiry:
                return {"symbol": symbol.upper(), "expiry": None, "spot": 0, "strikes": []}
            chain_body = {
                "UnderlyingScrip": int(sid),
                "UnderlyingSeg": under_seg,
                "Expiry": use_expiry,
            }
            chain = await self._post("/optionchain", chain_body, throttle=False)
            return self._normalize_chain(symbol, use_expiry, chain)
        except Exception as e:
            logger.warning(f"Option chain failed: {e}")
            q = await self.get_quote(symbol)
            return {"symbol": symbol.upper(), "expiry": expiry, "spot": q["ltp"], "strikes": [], "error": str(e)}

    def _normalize_chain(self, symbol: str, expiry: str, chain: dict) -> dict:
        data = chain.get("data") or {}
        spot = float(data.get("last_price") or 0)
        oc = data.get("oc") or data.get("option_chain") or {}
        strikes = []
        # Dhan structure varies; handle common forms
        if isinstance(oc, dict):
            for strike_str, legs in oc.items():
                try:
                    k = float(strike_str)
                except Exception:
                    continue
                ce = legs.get("ce") or legs.get("CE") or {}
                pe = legs.get("pe") or legs.get("PE") or {}
                strikes.append({
                    "strike": k,
                    "ce_ltp": ce.get("last_price") or ce.get("ltp"),
                    "ce_oi": ce.get("oi"),
                    "ce_volume": ce.get("volume"),
                    "ce_iv": ce.get("implied_volatility") or ce.get("iv"),
                    "pe_ltp": pe.get("last_price") or pe.get("ltp"),
                    "pe_oi": pe.get("oi"),
                    "pe_volume": pe.get("volume"),
                    "pe_iv": pe.get("implied_volatility") or pe.get("iv"),
                })
        strikes.sort(key=lambda x: x["strike"])
        return {
            "symbol": symbol.upper(),
            "expiry": expiry,
            "spot": spot,
            "strikes": strikes,
            "source": "dhan",
        }

    def _token_meta(self) -> dict:
        """Decode JWT exp without verification (for UI expiry hint)."""
        try:
            import base64, json as _json
            parts = (self.access_token or "").split(".")
            if len(parts) < 2:
                return {}
            pad = parts[1] + "=" * (-len(parts[1]) % 4)
            payload = _json.loads(base64.urlsafe_b64decode(pad))
            exp = int(payload.get("exp") or 0)
            now = int(time.time())
            return {
                "token_exp": exp,
                "token_expired": bool(exp and exp <= now),
                "token_expires_in_sec": exp - now if exp else None,
                "dhan_client_id_claim": payload.get("dhanClientId"),
            }
        except Exception:
            return {}

    async def status(self) -> dict:
        blocked = self._blocked()
        meta = self._token_meta()
        if not blocked and (self.last_error == "auth_failed" or meta.get("token_expired")):
            blocked = "Dhan access token expired — generate a new JWT on web.dhan.co and paste in Settings"
        return {
            "provider": "dhan",
            "configured": self.configured,
            "client_id": self.client_id,
            "client_id_set": bool(self.client_id),
            "token_set": bool(self.access_token),
            "mode": "live_data_analysis_only",
            "last_error": self.last_error,
            "blocked": blocked,
            "ok": bool(self.configured and not blocked and self.last_error not in ("auth_failed",)),
            **meta,
        }


dhan_client = DhanLiveClient()
