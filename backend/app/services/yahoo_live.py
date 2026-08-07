"""
Yahoo Finance Live Data Fallback Client
Provides free, real-time quotes and multi-timeframe OHLCV historical candle data for Indian market symbols (NSE equity + Indices).
Used as an automatic seamless fallback when broker API tokens (Upstox/Dhan) expire or fail.
"""
from __future__ import annotations
import asyncio
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from loguru import logger

YAHOO_SYMBOL_MAP: Dict[str, str] = {
    "NIFTY": "^NSEI",
    "NIFTY 50": "^NSEI",
    "NIFTY50": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "NIFTY BANK": "^NSEBANK",
    "FINNIFTY": "NIFTY_FIN_SERVICE.NS",
    "NIFTY FIN SERVICE": "NIFTY_FIN_SERVICE.NS",
    "INDIA VIX": "^INDIAVIX",
    "INDIAVIX": "^INDIAVIX",
}

INTERVAL_MAP = {
    "1minute": "1m",
    "3minute": "2m",
    "5minute": "5m",
    "15minute": "15m",
    "30minute": "30m",
    "1hour": "60m",
    "60minute": "60m",
    "day": "1d",
}


class YahooLiveClient:
    """Yahoo Finance client for backup market data streaming & indicator calculations."""

    def __init__(self):
        self.name = "yahoo"
        self._quote_cache: Dict[str, Tuple[float, dict]] = {}
        self._hist_cache: Dict[str, Tuple[float, List[dict]]] = {}
        self._cache_ttl = 3.0   # 3s quote cache
        self._hist_ttl = 30.0   # 30s historical candle cache

    @property
    def configured(self) -> bool:
        return True  # Always available without API key

    def get_ticker(self, symbol: str) -> str:
        sym_clean = symbol.upper().strip()
        if sym_clean in YAHOO_SYMBOL_MAP:
            return YAHOO_SYMBOL_MAP[sym_clean]
        if sym_clean.startswith("^") or sym_clean.endswith(".NS") or sym_clean.endswith(".BO"):
            return sym_clean
        return f"{sym_clean}.NS"

    async def status(self) -> dict:
        return {
            "configured": True,
            "provider": "yahoo",
            "token_set": True,
            "status": "ready (fallback)",
        }

    def _fetch_yahoo_chart_sync(self, ticker: str, interval: str, range_str: str) -> dict:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(ticker)}?interval={interval}&range={range_str}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=7) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                results = data.get("chart", {}).get("result")
                if results and len(results) > 0:
                    return results[0]
        except Exception as e:
            logger.debug(f"Yahoo chart fetch error for {ticker}: {e}")
        return {}

    async def get_historical(self, symbol: str, interval: str = "5minute") -> List[Dict[str, Any]]:
        """Fetch historical candles from Yahoo Finance."""
        sym_clean = symbol.upper().strip()
        cache_key = f"{sym_clean}_{interval}"
        now = time.monotonic()

        if cache_key in self._hist_cache:
            ts, val = self._hist_cache[cache_key]
            if now - ts < self._hist_ttl:
                return val

        ticker = self.get_ticker(sym_clean)
        y_interval = INTERVAL_MAP.get(interval, "5m")
        y_range = "5d" if y_interval in ("1m", "2m", "5m", "15m", "30m", "60m") else "1mo"

        chart_data = await asyncio.to_thread(self._fetch_yahoo_chart_sync, ticker, y_interval, y_range)
        if not chart_data:
            return []

        timestamps = chart_data.get("timestamp", [])
        quote = (chart_data.get("indicators", {}).get("quote") or [{}])[0]
        opens = quote.get("open", [])
        highs = quote.get("high", [])
        lows = quote.get("low", [])
        closes = quote.get("close", [])
        vols = quote.get("volume", [])

        rows: List[Dict[str, Any]] = []
        for i in range(len(timestamps)):
            if i < len(closes) and closes[i] is not None and i < len(opens) and opens[i] is not None:
                ts_dt = pd.to_datetime(timestamps[i], unit="s", utc=True).tz_convert("Asia/Kolkata")
                rows.append({
                    "timestamp": ts_dt.isoformat(),
                    "open": float(opens[i]),
                    "high": float(highs[i]) if i < len(highs) and highs[i] is not None else float(closes[i]),
                    "low": float(lows[i]) if i < len(lows) and lows[i] is not None else float(closes[i]),
                    "close": float(closes[i]),
                    "volume": int(vols[i]) if i < len(vols) and vols[i] is not None else 0,
                })

        self._hist_cache[cache_key] = (now, rows)
        return rows

    async def get_ohlcv_df(self, symbol: str, interval: str = "5minute") -> pd.DataFrame:
        """Return pandas DataFrame for technical indicators."""
        rows = await self.get_historical(symbol, interval)
        if not rows:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
        return df[["open", "high", "low", "close", "volume"]]

    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Fetch real-time quote for a single symbol from Yahoo Finance."""
        sym_clean = symbol.upper().strip()
        now = time.monotonic()
        if sym_clean in self._quote_cache:
            ts, q = self._quote_cache[sym_clean]
            if now - ts < self._cache_ttl:
                return q

        ticker = self.get_ticker(sym_clean)
        chart_data = await asyncio.to_thread(self._fetch_yahoo_chart_sync, ticker, "1m", "1d")
        if not chart_data:
            # Fallback to 5m/5d if 1d is off-hours empty
            chart_data = await asyncio.to_thread(self._fetch_yahoo_chart_sync, ticker, "5m", "5d")

        meta = chart_data.get("meta", {})
        ltp = float(meta.get("regularMarketPrice") or 0.0)
        prev_close = float(meta.get("chartPreviousClose") or meta.get("previousClose") or 0.0)

        quote = (chart_data.get("indicators", {}).get("quote") or [{}])[0]
        closes = [c for c in quote.get("close", []) if c is not None]
        if closes:
            if ltp <= 0:
                ltp = float(closes[-1])

        if prev_close <= 0 and len(closes) > 1:
            prev_close = float(closes[0])

        change = round(ltp - prev_close, 2) if prev_close else 0.0
        change_pct = round((change / prev_close) * 100.0, 2) if prev_close else 0.0

        q = {
            "symbol": sym_clean,
            "ltp": ltp,
            "open": float(meta.get("regularMarketDayLow") or meta.get("dayLow") or ltp),
            "high": float(meta.get("regularMarketDayHigh") or meta.get("dayHigh") or ltp),
            "low": float(meta.get("regularMarketDayLow") or meta.get("dayLow") or ltp),
            "close": prev_close or ltp,
            "change": change,
            "change_percent": change_pct,
            "volume": int(meta.get("regularMarketVolume") or 0),
            "timestamp": datetime.utcnow().isoformat(),
            "source": "yahoo",
        }
        self._quote_cache[sym_clean] = (now, q)
        return q

    async def get_quotes(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Batch fetch quotes concurrently."""
        tasks = [self.get_quote(s) for s in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        valid = []
        for r in results:
            if isinstance(r, dict) and r.get("symbol"):
                valid.append(r)
        return valid


yahoo_client = YahooLiveClient()
