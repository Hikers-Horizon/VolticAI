"""Market Data Engine — LIVE Dhan Data APIs only (fast + no fake prices)"""
from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import datetime
import pandas as pd
from loguru import logger
from app.services.dhan_live import dhan_client
from app.services.upstox_live import upstox_client

DEFAULT_UNIVERSE = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN",
    "BHARTIARTL", "ITC", "KOTAKBANK", "LT", "WIPRO", "AXISBANK",
    "BAJFINANCE", "MARUTI", "TATAMOTORS",
]
# Higher day-range / momentum names (mid/small + beta large) for explosive scanners
# 10-20% days are rare even here — scanner ranks POTENTIAL, not guarantees.
MOMENTUM_UNIVERSE = [
    "IDEA", "YESBANK", "SUZLON", "IREDA", "IRFC", "PAYTM", "ZOMATO", "NYKAA",
    "POLICYBZR", "DELHIVERY", "RVNL", "IRCTC", "HAL", "BEL", "BHEL", "NBCC",
    "HUDCO", "IREDA", "JIOFIN", "TATAELXSI", "DIXON", "KALYANKJIL", "TRENT",
    "ADANIENT", "ADANIPOWER", "ADANIGREEN", "TATAMOTORS", "BHEL", "PNB",
    "BANKBARODA", "CANBK", "IDFCFIRSTB", "FEDERALBNK", "RBLBANK", "AUBANK",
    "GMRAIRPORT", "IRB", "NCC", "KEC", "HFCL", "TEJASNET", "RPOWER",
    "JPPOWER", "NHPC", "SJVN", "NTPCGREEN", "SOLARINDS", "POLYCAB",
    "COCHINSHIP", "MAZAGON", "GRSE", "DATAPATTNS", "MIDHANI",
    "ANGELONE", "IIFL", "MANAPPURAM", "MUTHOOTFIN", "CDSL", "BSE",
    "MCX", "INDIAMART", "AFFLE", "LATENTVIEW", "KPITTECH", "PERSISTENT",
    "COFORGE", "MPHASIS", "LTTS", "OFSS", "NAUKRI", "INDIACEM", "SAIL",
    "HINDCOPPER", "NATIONALUM", "VEDL", "JINDALSTEL", "JSWSTEEL", "TATASTEEL",
    "NMDC", "MOIL", "GMDCLTD", "IOC", "BPCL", "HINDPETRO", "ONGC",
    "OIL", "GAIL", "PETRONET", "IGL", "MGL", "GUJGASLTD",
]
INDEX_SYMBOLS = ["NIFTY", "BANKNIFTY", "FINNIFTY"]


class MarketDataService:
    def _active_client(self):
        if upstox_client.configured:
            return upstox_client
        if dhan_client.configured:
            return dhan_client
        return upstox_client

    async def provider_status(self) -> dict:
        client = self._active_client()
        return await client.status()

    async def get_status(self) -> Dict[str, Any]:
        now = datetime.now()
        is_open = now.weekday() < 5 and (
            (now.hour == 9 and now.minute >= 15)
            or (10 <= now.hour < 15)
            or (now.hour == 15 and now.minute < 30)
        )
        vix = None
        client = self._active_client()
        if client.configured:
            try:
                q = await client.get_quote("INDIA VIX")
                vix = q.get("ltp")
            except Exception:
                pass
        return {
            "is_open": is_open,
            "current_time": now.isoformat(),
            "market_open": "09:15",
            "market_close": "15:30",
            "status": "OPEN" if is_open else "CLOSED",
            "india_vix": vix,
            "data_source": getattr(client, "name", "upstox") if client.configured else "unconfigured",
            "live": client.configured,
        }

    async def get_quote(self, symbol: str, exchange: str = "NSE") -> Dict[str, Any]:
        client = self._active_client()
        if not client.configured:
            logger.warning(f"No configured provider, returning default quote for {symbol}")
            return {"symbol": symbol.upper(), "ltp": 0.0, "change": 0.0, "change_percent": 0.0}
        return await client.get_quote(symbol)

    async def get_quotes(self, symbols: List[str], exchange: str = "NSE") -> List[Dict]:
        client = self._active_client()
        if not client.configured:
            return []
        return await client.get_quotes(symbols)

    async def get_historical(
        self, symbol: str, interval: str = "5minute",
        from_date: Optional[str] = None, to_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        client = self._active_client()
        data = await client.get_historical(symbol, interval)
        return {"symbol": symbol.upper(), "interval": interval, "data": data, "source": "upstox" if client == upstox_client else "dhan"}

    async def get_ohlcv_df(self, symbol: str, interval: str = "5minute") -> pd.DataFrame:
        client = self._active_client()
        return await client.get_ohlcv_df(symbol, interval)

    async def top_gainers(self, limit: int = 10) -> List[Dict]:
        # Prefer momentum universe for real day-movers
        try:
            quotes = await self.get_quotes(list(dict.fromkeys(MOMENTUM_UNIVERSE + DEFAULT_UNIVERSE))[:40])
        except Exception:
            quotes = await self.get_quotes(DEFAULT_UNIVERSE)
        quotes = [q for q in quotes if q.get("ltp")]
        for q in quotes:
            q["day_range_pct"] = self._day_range_pct(q)
        quotes.sort(key=lambda x: x.get("change_percent") or 0, reverse=True)
        return quotes[:limit]

    async def top_losers(self, limit: int = 10) -> List[Dict]:
        try:
            quotes = await self.get_quotes(list(dict.fromkeys(MOMENTUM_UNIVERSE + DEFAULT_UNIVERSE))[:40])
        except Exception:
            quotes = await self.get_quotes(DEFAULT_UNIVERSE)
        quotes = [q for q in quotes if q.get("ltp")]
        for q in quotes:
            q["day_range_pct"] = self._day_range_pct(q)
        quotes.sort(key=lambda x: x.get("change_percent") or 0)
        return quotes[:limit]

    @staticmethod
    def _day_range_pct(q: Dict) -> float:
        try:
            hi = float(q.get("high") or 0)
            lo = float(q.get("low") or 0)
            cl = float(q.get("close") or q.get("ltp") or 0)
            if cl <= 0 or hi <= 0 or lo <= 0:
                return 0.0
            return round(((hi - lo) / cl) * 100.0, 2)
        except Exception:
            return 0.0

    async def explosive_movers(self, limit: int = 15) -> Dict[str, Any]:
        """Rank stocks by day-move + range potential for aggressive intraday.

        Truth: 10-20% days are rare. This ranks for HIGH VOLATILITY POTENTIAL
        (large day range / strong % change / volume), not guaranteed 10-20%.
        """
        universe = list(dict.fromkeys(MOMENTUM_UNIVERSE))[:45]
        quotes = await self.get_quotes(universe)
        scored = []
        for q in quotes:
            ltp = float(q.get("ltp") or 0)
            if ltp <= 0:
                continue
            # Prefer tradeable cash range for Rs10k accounts
            if ltp < 15 or ltp > 3500:
                continue
            chg = abs(float(q.get("change_percent") or 0))
            rng = self._day_range_pct(q)
            vol = float(q.get("volume") or 0)
            # Volume score rough log-ish
            vol_s = min(30.0, (vol / 1_000_000.0) * 3.0) if vol else 0.0
            # Explosive score: range + abs day change + volume
            score = rng * 1.4 + chg * 1.8 + vol_s
            # Bonus if already expanding range
            if rng >= 4:
                score += 8
            if chg >= 3:
                score += 10
            if chg >= 5:
                score += 12
            if rng >= 8:
                score += 15
            direction = "UP" if (q.get("change_percent") or 0) >= 0 else "DOWN"
            q2 = {
                **q,
                "day_range_pct": rng,
                "abs_change_pct": round(chg, 2),
                "explosive_score": round(score, 2),
                "direction": direction,
                "potential_tag": (
                    "EXTREME" if rng >= 8 or chg >= 7
                    else "HIGH" if rng >= 4 or chg >= 3
                    else "MODERATE" if rng >= 2 or chg >= 1.5
                    else "LOW"
                ),
            }
            scored.append(q2)
        scored.sort(key=lambda x: x["explosive_score"], reverse=True)
        top = scored[:limit]
        return {
            "movers": top,
            "count": len(top),
            "scanned": len(quotes),
            "note": (
                "Ranked for HIGH day-range / momentum potential. "
                "10-20% single-day moves are uncommon and high-risk. "
                "Not a guarantee of profit."
            ),
            "source": "dhan",
        }

    async def indices(self) -> List[Dict]:
        return await self.get_quotes(INDEX_SYMBOLS)

    async def options_chain(self, symbol: str, expiry: Optional[str] = None) -> dict:
        return await dhan_client.option_chain(symbol, expiry)

    async def breadth(self) -> dict:
        try:
            quotes = await self.get_quotes(DEFAULT_UNIVERSE)
            adv = sum(1 for q in quotes if (q.get("change_percent") or 0) > 0)
            dec = sum(1 for q in quotes if (q.get("change_percent") or 0) < 0)
            unch = len(quotes) - adv - dec
            return {
                "advances": adv,
                "declines": dec,
                "unchanged": unch,
                "advance_decline_ratio": round(adv / dec, 2) if dec else float(adv),
                "universe_size": len(quotes),
                "source": "dhan",
            }
        except Exception as e:
            logger.warning(f"breadth error: {e}")
            return {"advances": 0, "declines": 0, "unchanged": 0, "error": str(e)}


market_service = MarketDataService()
