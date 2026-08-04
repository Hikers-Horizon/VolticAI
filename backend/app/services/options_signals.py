"""
Options Signal Scanner — High-probability NIFTY/BANKNIFTY options trades
Finds explosive CE/PE opportunities based on spot momentum + chain analysis
"""
from __future__ import annotations
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from loguru import logger
from app.services.market_data import market_service
from app.services.dhan_live import dhan_client


class OptionsSignalService:
    """Scan options chain for high-probability intraday CE/PE setups"""
    
    UNDERLYINGS = ["NIFTY", "BANKNIFTY"]  # Index options only
    
    async def scan_options(
        self,
        underlying: Optional[str] = None,
        limit: int = 6,
    ) -> Dict[str, Any]:
        """
        Find best options for intraday (CE/PE signals)
        Returns top signals sorted by conviction score
        """
        symbols = [underlying.upper()] if underlying else self.UNDERLYINGS
        
        async def _scan_one(sym: str):
            try:
                return await self._analyze_underlying(sym, limit=limit)
            except Exception as e:
                logger.warning(f"Options scan failed for {sym}: {e}")
                return []
        
        tasks = [_scan_one(sym) for sym in symbols]
        results = await asyncio.gather(*tasks)
        
        # Flatten and sort by conviction
        all_signals = []
        for signals in results:
            all_signals.extend(signals)
        
        all_signals.sort(key=lambda x: x.get("conviction_score", 0), reverse=True)
        
        return {
            "signals": all_signals[:limit],
            "underlyings_scanned": symbols,
            "total_candidates": len(all_signals),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "disclaimer": (
                "Options carry HIGH RISK and can lose 100% quickly. "
                "Use small position size. Signals are probabilistic, not guaranteed. "
                "Set stop-loss immediately after entry."
            ),
        }
    
    async def _analyze_underlying(self, symbol: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Analyze one index (NIFTY/BANKNIFTY) and return top CE/PE candidates"""
        
        # Get spot quote + momentum
        quote = await market_service.get_quote(symbol)
        spot = quote.get("ltp")
        if not spot:
            return []
        
        day_change_pct = quote.get("change_percent", 0)
        
        # Get options chain (nearest expiry)
        chain = await market_service.options_chain(symbol, expiry=None)
        strikes = chain.get("strikes", [])
        if not strikes:
            return []
        
        expiry = chain.get("expiry", "UNKNOWN")
        
        # Filter ATM ±5 strikes
        atm = round(spot / 50) * 50 if symbol == "NIFTY" else round(spot / 100) * 100
        step = 50 if symbol == "NIFTY" else 100
        strike_range = [atm + i * step for i in range(-5, 6)]
        
        candidates = []
        for st_data in strikes:
            strike = st_data.get("strike")
            if strike not in strike_range:
                continue
            
            # CE analysis
            ce_ltp = st_data.get("ce_ltp")
            ce_vol = st_data.get("ce_volume") or 0
            ce_oi = st_data.get("ce_oi") or 0
            
            if ce_ltp and ce_ltp > 5 and ce_vol > 100:  # Minimum liquidity
                ce_score = self._score_option(
                    option_type="CE",
                    strike=strike,
                    spot=spot,
                    ltp=ce_ltp,
                    volume=ce_vol,
                    oi=ce_oi,
                    day_change_pct=day_change_pct,
                )
                if ce_score > 50:
                    candidates.append({
                        "underlying": symbol,
                        "strike": strike,
                        "expiry": expiry,
                        "option_type": "CE",
                        "symbol_display": f"{symbol} {expiry[:6]} {int(strike)} CE",
                        "ltp": ce_ltp,
                        "volume": int(ce_vol),
                        "oi": int(ce_oi),
                        "conviction_score": round(ce_score, 1),
                        "day_change_pct": round(day_change_pct, 2),
                        "moneyness": self._moneyness(strike, spot, "CE"),
                        "entry_zone": [ce_ltp * 0.98, ce_ltp * 1.02],
                        "target": ce_ltp * 1.5,
                        "stop_loss": ce_ltp * 0.7,
                    })
            
            # PE analysis
            pe_ltp = st_data.get("pe_ltp")
            pe_vol = st_data.get("pe_volume") or 0
            pe_oi = st_data.get("pe_oi") or 0
            
            if pe_ltp and pe_ltp > 5 and pe_vol > 100:
                pe_score = self._score_option(
                    option_type="PE",
                    strike=strike,
                    spot=spot,
                    ltp=pe_ltp,
                    volume=pe_vol,
                    oi=pe_oi,
                    day_change_pct=day_change_pct,
                )
                if pe_score > 50:
                    candidates.append({
                        "underlying": symbol,
                        "strike": strike,
                        "expiry": expiry,
                        "option_type": "PE",
                        "symbol_display": f"{symbol} {expiry[:6]} {int(strike)} PE",
                        "ltp": pe_ltp,
                        "volume": int(pe_vol),
                        "oi": int(pe_oi),
                        "conviction_score": round(pe_score, 1),
                        "day_change_pct": round(day_change_pct, 2),
                        "moneyness": self._moneyness(strike, spot, "PE"),
                        "entry_zone": [pe_ltp * 0.98, pe_ltp * 1.02],
                        "target": pe_ltp * 1.5,
                        "stop_loss": pe_ltp * 0.7,
                    })

        # Sort by conviction and return top N
        candidates.sort(key=lambda x: x["conviction_score"], reverse=True)
        return candidates[:limit]

    def _score_option(
        self,
        option_type: str,
        strike: float,
        spot: float,
        ltp: float,
        volume: int,
        oi: int,
        day_change_pct: float,
    ) -> float:
        """
        Score CE/PE for intraday potential (0-100)
        Higher score = better setup
        """
        score = 50.0  # Base

        # Moneyness preference (ATM ±1 strike is best for intraday)
        distance_pct = abs((strike - spot) / spot * 100)
        if distance_pct < 1:  # ATM
            score += 20
        elif distance_pct < 2:  # Near ATM
            score += 10
        elif distance_pct > 5:  # Too far OTM/ITM
            score -= 15

        # Spot momentum alignment
        if option_type == "CE" and day_change_pct > 0.5:  # Spot moving up
            score += min(day_change_pct * 5, 15)
        elif option_type == "PE" and day_change_pct < -0.5:  # Spot moving down
            score += min(abs(day_change_pct) * 5, 15)
        elif option_type == "CE" and day_change_pct < -0.3:  # Counter-trend CE
            score -= 10
        elif option_type == "PE" and day_change_pct > 0.3:  # Counter-trend PE
            score -= 10

        # Liquidity (volume > OI is fresh activity)
        vol_oi_ratio = volume / max(oi, 1)
        if vol_oi_ratio > 0.5:  # High activity
            score += 12
        elif vol_oi_ratio > 0.2:
            score += 6
        elif vol_oi_ratio < 0.05:  # Dead option
            score -= 15

        # Premium range (5-200 optimal for intraday)
        if 10 <= ltp <= 150:
            score += 8
        elif ltp < 5:  # Too cheap, lottery ticket
            score -= 20
        elif ltp > 300:  # Too expensive, less leverage
            score -= 10

        return max(0, min(100, score))

    def _moneyness(self, strike: float, spot: float, option_type: str) -> str:
        """Calculate ATM/ITM/OTM label"""
        diff_pct = (strike - spot) / spot * 100
        if option_type == "CE":
            if abs(diff_pct) < 0.5:
                return "ATM"
            elif diff_pct < 0:
                return "ITM"
            else:
                return "OTM"
        else:  # PE
            if abs(diff_pct) < 0.5:
                return "ATM"
            elif diff_pct > 0:
                return "ITM"
            else:
                return "OTM"


options_signal_service = OptionsSignalService()
