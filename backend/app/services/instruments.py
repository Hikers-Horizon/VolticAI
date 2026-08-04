"""
Dhan instrument master — symbol → security_id resolution
"""
from __future__ import annotations
import csv
import io
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import httpx
from loguru import logger

SCRIP_MASTER_URL = "https://images.dhan.co/api-data/api-scrip-master.csv"
CACHE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "scrip_master.csv"

# Well-known fallbacks (used if CSV download fails)
FALLBACK: Dict[str, Tuple[str, str, str]] = {
    # symbol: (security_id, exchange_segment, instrument)
    "RELIANCE": ("2885", "NSE_EQ", "EQUITY"),
    "TCS": ("11536", "NSE_EQ", "EQUITY"),
    "INFY": ("1594", "NSE_EQ", "EQUITY"),
    "HDFCBANK": ("1333", "NSE_EQ", "EQUITY"),
    "ICICIBANK": ("4963", "NSE_EQ", "EQUITY"),
    "SBIN": ("3045", "NSE_EQ", "EQUITY"),
    "BHARTIARTL": ("10604", "NSE_EQ", "EQUITY"),
    "ITC": ("1660", "NSE_EQ", "EQUITY"),
    "KOTAKBANK": ("1922", "NSE_EQ", "EQUITY"),
    "LT": ("11483", "NSE_EQ", "EQUITY"),
    "WIPRO": ("3787", "NSE_EQ", "EQUITY"),
    "AXISBANK": ("5900", "NSE_EQ", "EQUITY"),
    "BAJFINANCE": ("317", "NSE_EQ", "EQUITY"),
    "MARUTI": ("10999", "NSE_EQ", "EQUITY"),
    "TATAMOTORS": ("3456", "NSE_EQ", "EQUITY"),
    "SUNPHARMA": ("3351", "NSE_EQ", "EQUITY"),
    "TITAN": ("3506", "NSE_EQ", "EQUITY"),
    "HINDUNILVR": ("1394", "NSE_EQ", "EQUITY"),
    "ASIANPAINT": ("236", "NSE_EQ", "EQUITY"),
    "NTPC": ("11630", "NSE_EQ", "EQUITY"),
    "POWERGRID": ("14977", "NSE_EQ", "EQUITY"),
    "ULTRACEMCO": ("11532", "NSE_EQ", "EQUITY"),
    "NESTLEIND": ("17963", "NSE_EQ", "EQUITY"),
    "M&M": ("2031", "NSE_EQ", "EQUITY"),
    "TECHM": ("13538", "NSE_EQ", "EQUITY"),
    "HCLTECH": ("7229", "NSE_EQ", "EQUITY"),
    "ONGC": ("2475", "NSE_EQ", "EQUITY"),
    "TATASTEEL": ("3499", "NSE_EQ", "EQUITY"),
    "ADANIENT": ("25", "NSE_EQ", "EQUITY"),
    "ADANIPORTS": ("15083", "NSE_EQ", "EQUITY"),
    "JSWSTEEL": ("11723", "NSE_EQ", "EQUITY"),
    "COALINDIA": ("20374", "NSE_EQ", "EQUITY"),
    "INDUSINDBK": ("5258", "NSE_EQ", "EQUITY"),
    "BAJAJFINSV": ("16675", "NSE_EQ", "EQUITY"),
    "HDFCLIFE": ("467", "NSE_EQ", "EQUITY"),
    "SBILIFE": ("21808", "NSE_EQ", "EQUITY"),
    "CIPLA": ("694", "NSE_EQ", "EQUITY"),
    "DRREDDY": ("881", "NSE_EQ", "EQUITY"),
    "EICHERMOT": ("910", "NSE_EQ", "EQUITY"),
    "GRASIM": ("1232", "NSE_EQ", "EQUITY"),
    "HINDALCO": ("1363", "NSE_EQ", "EQUITY"),
    "BPCL": ("526", "NSE_EQ", "EQUITY"),
    "BRITANNIA": ("547", "NSE_EQ", "EQUITY"),
    "APOLLOHOSP": ("157", "NSE_EQ", "EQUITY"),
    "DIVISLAB": ("10940", "NSE_EQ", "EQUITY"),
    "HEROMOTOCO": ("1348", "NSE_EQ", "EQUITY"),
    "TATACONSUM": ("3432", "NSE_EQ", "EQUITY"),
    "LTIM": ("17818", "NSE_EQ", "EQUITY"),
    # Indices (IDX_I)
    "NIFTY": ("13", "IDX_I", "INDEX"),
    "NIFTY 50": ("13", "IDX_I", "INDEX"),
    "BANKNIFTY": ("25", "IDX_I", "INDEX"),
    "NIFTY BANK": ("25", "IDX_I", "INDEX"),
    "FINNIFTY": ("27", "IDX_I", "INDEX"),
    "NIFTY FIN SERVICE": ("27", "IDX_I", "INDEX"),
    "MIDCPNIFTY": ("442", "IDX_I", "INDEX"),
    "SENSEX": ("51", "IDX_I", "INDEX"),
    "INDIA VIX": ("21", "IDX_I", "INDEX"),
    "INDIAVIX": ("21", "IDX_I", "INDEX"),
}


class InstrumentMaster:
    def __init__(self):
        # symbol.upper() -> (security_id, segment, instrument)
        self._map: Dict[str, Tuple[str, str, str]] = dict(FALLBACK)
        self._loaded_at: Optional[datetime] = None
        self._security_to_symbol: Dict[str, str] = {
            sid: sym for sym, (sid, _, _) in FALLBACK.items()
        }

    async def ensure_loaded(self, force: bool = False):
        if (
            not force
            and self._loaded_at
            and datetime.utcnow() - self._loaded_at < timedelta(hours=12)
            and len(self._map) > len(FALLBACK)
        ):
            return
        try:
            await self._download_and_parse()
        except Exception as e:
            logger.warning(f"Scrip master download failed, using fallbacks: {e}")
            if CACHE_PATH.exists():
                try:
                    self._parse_csv(CACHE_PATH.read_text(encoding="utf-8", errors="ignore"))
                except Exception:
                    pass
        self._loaded_at = datetime.utcnow()

    async def _download_and_parse(self):
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.get(SCRIP_MASTER_URL)
            r.raise_for_status()
            text = r.text
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(text, encoding="utf-8")
        self._parse_csv(text)
        logger.info(f"Loaded {len(self._map)} instruments from Dhan scrip master")

    def _parse_csv(self, text: str):
        reader = csv.DictReader(io.StringIO(text))
        count = 0
        for row in reader:
            try:
                exch = (row.get("SEM_EXM_EXCH_ID") or row.get("EXCH_ID") or "").upper()
                seg = (row.get("SEM_SEGMENT") or row.get("SEGMENT") or "").upper()
                inst = (row.get("SEM_INSTRUMENT_NAME") or row.get("INSTRUMENT") or "").upper()
                sid = str(row.get("SEM_SMST_SECURITY_ID") or row.get("SECURITY_ID") or "").strip()
                tsym = (row.get("SEM_TRADING_SYMBOL") or row.get("SYMBOL_NAME") or "").upper().strip()
                if not sid or not tsym:
                    continue

                # Equity NSE
                if exch == "NSE" and seg in ("E", "EQ") and inst in ("EQUITY", "ES"):
                    segment = "NSE_EQ"
                    instrument = "EQUITY"
                    # Strip -EQ suffix if present
                    sym = tsym.replace("-EQ", "").split("-")[0]
                    self._map[sym] = (sid, segment, instrument)
                    self._security_to_symbol[sid] = sym
                    count += 1
                # Index
                elif seg in ("I", "IDX") or inst == "INDEX":
                    segment = "IDX_I"
                    instrument = "INDEX"
                    self._map[tsym] = (sid, segment, instrument)
                    # aliases
                    clean = tsym.replace(" ", "")
                    self._map[clean] = (sid, segment, instrument)
                    self._security_to_symbol[sid] = tsym
                    count += 1
            except Exception:
                continue
        # Re-apply critical fallbacks last for stability
        for k, v in FALLBACK.items():
            self._map[k] = v

    def resolve(self, symbol: str) -> Optional[Tuple[str, str, str]]:
        """Return (security_id, exchange_segment, instrument) or None."""
        sym = symbol.upper().strip()
        if sym in self._map:
            return self._map[sym]
        # try without spaces / suffixes
        alt = sym.replace(" ", "").replace("-EQ", "")
        return self._map.get(alt)

    def symbol_for(self, security_id: str) -> Optional[str]:
        return self._security_to_symbol.get(str(security_id))

    def search(self, query: str, limit: int = 12) -> List[Dict[str, str]]:
        """Prefix / contains search over equity + index symbols."""
        q = (query or "").upper().strip()
        if not q or len(q) < 1:
            return []

        # Popular first hits for empty-ish common queries
        popular = [
            "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN",
            "NIFTY", "BANKNIFTY", "FINNIFTY", "BHARTIARTL", "ITC", "LT",
            "WIPRO", "AXISBANK", "BAJFINANCE", "MARUTI", "TATAMOTORS",
        ]

        starts: List[Dict[str, str]] = []
        contains: List[Dict[str, str]] = []
        seen = set()

        def add(sym: str, bucket: List[Dict[str, str]]):
            if sym in seen:
                return
            resolved = self.resolve(sym)
            if not resolved:
                return
            sid, segment, instrument = resolved
            seen.add(sym)
            bucket.append({
                "symbol": sym,
                "security_id": sid,
                "segment": segment,
                "instrument": instrument,
                "exchange": "NSE",
                "type": "INDEX" if instrument == "INDEX" or segment == "IDX_I" else "EQ",
            })

        # Prefer popular symbols that match
        for sym in popular:
            if sym.startswith(q):
                add(sym, starts)
            elif q in sym:
                add(sym, contains)

        # Full master scan
        for sym in self._map.keys():
            if len(starts) + len(contains) >= limit * 3:
                break
            # skip noisy long names
            if len(sym) > 24 or " " in sym and instrument_type_skip(sym):
                continue
            if sym.startswith(q):
                add(sym, starts)
            elif q in sym:
                add(sym, contains)

        results = starts + contains
        return results[:limit]


def instrument_type_skip(sym: str) -> bool:
    return False


instrument_master = InstrumentMaster()
