"""
Live Upstox API Client (v2) — Real-time quotes, batch market data & multi-timeframe historical candles.
"""
from __future__ import annotations
import asyncio
import time
import urllib.parse
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import httpx
import pandas as pd
from loguru import logger
from app.core.config import settings

BASE_URL = "https://api.upstox.com/v2"

# Upstox Instrument Keys mapping for top NSE liquid stocks & indices
UPSTOX_INSTRUMENT_MAP: Dict[str, str] = {
    # Indices
    "NIFTY": "NSE_INDEX|Nifty 50",
    "NIFTY 50": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "NIFTY BANK": "NSE_INDEX|Nifty Bank",
    "FINNIFTY": "NSE_INDEX|Nifty Fin Service",
    "INDIA VIX": "NSE_INDEX|India Vix",
    "INDIAVIX": "NSE_INDEX|India Vix",
    
    # Top Nifty 50 & Liquid Stocks
    "RELIANCE": "NSE_EQ|INE002A01018",
    "TCS": "NSE_EQ|INE467B01029",
    "INFY": "NSE_EQ|INE009A01021",
    "HDFCBANK": "NSE_EQ|INE040A01034",
    "ICICIBANK": "NSE_EQ|INE090A01021",
    "SBIN": "NSE_EQ|INE062A01020",
    "BHARTIARTL": "NSE_EQ|INE397D01024",
    "ITC": "NSE_EQ|INE154A01025",
    "KOTAKBANK": "NSE_EQ|INE237A01028",
    "LT": "NSE_EQ|INE018A01030",
    "WIPRO": "NSE_EQ|INE075A01022",
    "AXISBANK": "NSE_EQ|INE238A01034",
    "BAJFINANCE": "NSE_EQ|INE296A01024",
    "MARUTI": "NSE_EQ|INE585B01010",
    "TATAMOTORS": "NSE_EQ|INE155A01022",
    "SUNPHARMA": "NSE_EQ|INE044A01036",
    "TITAN": "NSE_EQ|INE280A01028",
    "HINDUNILVR": "NSE_EQ|INE030A01027",
    "ASIANPAINT": "NSE_EQ|INE021A01026",
    "NTPC": "NSE_EQ|INE733E01010",
    "POWERGRID": "NSE_EQ|INE752E01010",
    "ULTRACEMCO": "NSE_EQ|INE481G01011",
    "NESTLEIND": "NSE_EQ|INE239A01024",
    "M&M": "NSE_EQ|INE101A01026",
    "TECHM": "NSE_EQ|INE669C01036",
    "HCLTECH": "NSE_EQ|INE860A01027",
    "ONGC": "NSE_EQ|INE213A01029",
    "TATASTEEL": "NSE_EQ|INE081A01020",
    "ADANIENT": "NSE_EQ|INE423A01024",
    "ADANIPORTS": "NSE_EQ|INE742F01042",
    "JSWSTEEL": "NSE_EQ|INE019A01038",
    "COALINDIA": "NSE_EQ|INE522F01014",
    "INDUSINDBK": "NSE_EQ|INE095A01012",
    "BAJAJFINSV": "NSE_EQ|INE918I01026",
    "ZOMATO": "NSE_EQ|INE758T01015",
    "PAYTM": "NSE_EQ|INE982J01020",
    "SUZLON": "NSE_EQ|INE040H01021",
    "JIOFIN": "NSE_EQ|INE0J1Y01017",
    "TRENT": "NSE_EQ|INE849A01020",
    "HAL": "NSE_EQ|INE066F01020",
    "BEL": "NSE_EQ|INE263A01024",
    "BHEL": "NSE_EQ|INE257A01026",
    "IRCTC": "NSE_EQ|INE00WO01028",
    "RVNL": "NSE_EQ|INE415G01027",
    "PFC": "NSE_EQ|INE134E01011",
    "REC": "NSE_EQ|INE020B01018",
    "DLF": "NSE_EQ|INE271C01023",
    "CDSL": "NSE_EQ|INE735H01010",
    "BSE": "NSE_EQ|INE118H01025",
    "ANGELONE": "NSE_EQ|INE732I01013",
}


class UpstoxLiveClient:
    def __init__(self):
        self.api_key = settings.UPSTOX_API_KEY
        self.api_secret = settings.UPSTOX_API_SECRET
        self.access_token = settings.UPSTOX_ACCESS_TOKEN
        self._http: Optional[httpx.AsyncClient] = None
        self._quote_cache: Dict[str, Tuple[float, dict]] = {}
        self._hist_cache: Dict[str, Tuple[float, List[dict]]] = {}
        self._cache_ttl = 2.0  # 2 seconds quote cache
        self._hist_ttl = 30.0  # 30 seconds historical candle cache

    @property
    def configured(self) -> bool:
        """Returns True if Upstox credentials / access token are present."""
        return bool(self.access_token and len(self.access_token) > 20)

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _get_client(self) -> httpx.AsyncClient:
        try:
            if self._http is None or self._http.is_closed:
                self._http = httpx.AsyncClient(
                    timeout=httpx.Timeout(10.0, connect=3.0),
                    headers=self._headers(),
                    limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
                )
            else:
                self._http.headers.update(self._headers())
            return self._http
        except Exception:
            self._http = httpx.AsyncClient(
                timeout=httpx.Timeout(10.0, connect=3.0),
                headers=self._headers(),
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            )
            return self._http

    def get_instrument_key(self, symbol: str) -> str:
        """Resolve symbol to Upstox instrument key."""
        sym_clean = symbol.upper().strip()
        if sym_clean in UPSTOX_INSTRUMENT_MAP:
            return UPSTOX_INSTRUMENT_MAP[sym_clean]
        return f"NSE_EQ|{sym_clean}"

    async def status(self) -> dict:
        return {
            "configured": self.configured,
            "provider": "upstox",
            "token_set": bool(self.access_token),
            "status": "ready" if self.configured else "unconfigured",
        }

    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Fetch live quote for a single symbol from Upstox Market Quote API."""
        quotes = await self.get_quotes([symbol])
        if quotes and len(quotes) > 0:
            return quotes[0]
        return {
            "symbol": symbol.upper(),
            "ltp": 0.0,
            "change": 0.0,
            "change_percent": 0.0,
            "open": 0.0,
            "high": 0.0,
            "low": 0.0,
            "close": 0.0,
            "volume": 0,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def get_quotes(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Batch fetch live quotes for multiple symbols from Upstox."""
        if not self.configured or not symbols:
            return []

        now = time.monotonic()
        results: List[Dict[str, Any]] = []
        missing_symbols: List[str] = []

        for sym in symbols:
            s_clean = sym.upper().strip()
            if s_clean in self._quote_cache:
                cached_time, cached_val = self._quote_cache[s_clean]
                if now - cached_time < self._cache_ttl:
                    results.append(cached_val)
                    continue
            missing_symbols.append(s_clean)

        if not missing_symbols:
            return results

        # Build URL-encoded list of instrument keys for Upstox API
        instrument_keys = [urllib.parse.quote(self.get_instrument_key(s)) for s in missing_symbols]
        instrument_str = ",".join(instrument_keys)

        try:
            client = await self._get_client()
            url = f"{BASE_URL}/market-quote/quotes?symbol={instrument_str}"
            response = await client.get(url)

            if response.status_code == 200:
                json_data = response.json()
                data_dict = json_data.get("data", {})

                for sym in missing_symbols:
                    key = self.get_instrument_key(sym)
                    # Upstox dict keys format can be "NSE_EQ:RELIANCE" or "NSE_EQ|INE..."
                    quote_data = data_dict.get(key) or data_dict.get(key.replace("|", ":")) or data_dict.get(sym) or {}
                    
                    ltp = float(quote_data.get("last_price") or 0.0)
                    ohlc = quote_data.get("ohlc") or {}
                    open_p = float(ohlc.get("open") or ltp)
                    high_p = float(ohlc.get("high") or ltp)
                    low_p = float(ohlc.get("low") or ltp)
                    close_p = float(ohlc.get("close") or ltp)
                    change = float(quote_data.get("net_change") or (ltp - close_p if close_p else 0.0))
                    change_pct = (change / close_p * 100.0) if close_p else 0.0
                    volume = int(quote_data.get("volume") or 0)

                    q_item = {
                        "symbol": sym,
                        "ltp": ltp,
                        "open": open_p,
                        "high": high_p,
                        "low": low_p,
                        "close": close_p,
                        "change": round(change, 2),
                        "change_percent": round(change_pct, 2),
                        "volume": volume,
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "upstox",
                    }

                    self._quote_cache[sym] = (now, q_item)
                    results.append(q_item)

            else:
                logger.error(f"Upstox market-quote HTTP {response.status_code}: {response.text[:200]}")

        except Exception as e:
            logger.error(f"Upstox market-quote exception: {e}")

        return results

    async def get_historical(self, symbol: str, interval: str = "5minute") -> List[Dict[str, Any]]:
        """Fetch historical / intraday candle data from Upstox API v2."""
        if not self.configured:
            return []

        sym_clean = symbol.upper().strip()
        cache_key = f"{sym_clean}_{interval}"
        now = time.monotonic()

        if cache_key in self._hist_cache:
            ts, val = self._hist_cache[cache_key]
            if now - ts < self._hist_ttl:
                return val

        raw_key = self.get_instrument_key(sym_clean)
        instrument_key = urllib.parse.quote(raw_key)

        try:
            client = await self._get_client()
            candles_raw = []

            if interval == "day":
                to_date = datetime.now().strftime("%Y-%m-%d")
                from_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
                url_hist = f"{BASE_URL}/historical-candle/{instrument_key}/day/{to_date}/{from_date}"
                res_hist = await client.get(url_hist)
                if res_hist.status_code == 200:
                    candles_raw = res_hist.json().get("data", {}).get("candles") or []
            else:
                # Upstox 1minute intraday endpoint
                url = f"{BASE_URL}/historical-candle/intraday/{instrument_key}/1minute"
                response = await client.get(url)
                if response.status_code == 200:
                    candles_raw = response.json().get("data", {}).get("candles") or []
                
                # Fallback to multi-day candles if intraday is empty
                if not candles_raw:
                    to_date = datetime.now().strftime("%Y-%m-%d")
                    from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                    url_hist = f"{BASE_URL}/historical-candle/{instrument_key}/day/{to_date}/{from_date}"
                    res_hist = await client.get(url_hist)
                    if res_hist.status_code == 200:
                        candles_raw = res_hist.json().get("data", {}).get("candles") or []

            parsed_candles: List[Dict[str, Any]] = []
            # Upstox format: [timestamp, open, high, low, close, volume, open_interest]
            for c in reversed(candles_raw):
                if len(c) >= 5:
                    parsed_candles.append({
                        "timestamp": c[0],
                        "open": float(c[1]),
                        "high": float(c[2]),
                        "low": float(c[3]),
                        "close": float(c[4]),
                        "volume": int(c[5]) if len(c) > 5 else 0,
                    })

            self._hist_cache[cache_key] = (now, parsed_candles)
            return parsed_candles

        except Exception as e:
            logger.error(f"Upstox historical candle error for {sym_clean}: {e}")
            return []

    async def get_ohlcv_df(self, symbol: str, interval: str = "5minute") -> pd.DataFrame:
        """Return pandas DataFrame resampled to target timeframe (e.g. 5min, 15min) for indicators."""
        candles = await self.get_historical(symbol, interval)
        if not candles:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        df = pd.DataFrame(candles)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
        df = df[["open", "high", "low", "close", "volume"]]

        # Resample if needed
        resample_map = {
            "3minute": "3min",
            "5minute": "5min",
            "15minute": "15min",
            "30minute": "30min",
            "1hour": "60min",
            "60minute": "60min",
        }
        rule = resample_map.get(interval)
        if rule and len(df) > 1:
            try:
                df = df.resample(rule).agg({
                    "open": "first",
                    "high": "max",
                    "low": "min",
                    "close": "last",
                    "volume": "sum",
                }).dropna()
            except Exception as e:
                logger.warning(f"Resampling failed for {symbol}: {e}")

        return df


# Global instance
upstox_client = UpstoxLiveClient()
