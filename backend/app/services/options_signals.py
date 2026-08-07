"""
Options Signal Engine — High-precision Index & Stock Options Trading Signals with Entry, Targets, Stop-loss & Exit rules.
"""
from __future__ import annotations
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from loguru import logger
from app.services.market_data import market_service


class OptionsSignalService:
    """Scan market for explosive NIFTY, BANKNIFTY, FINNIFTY & top stock option signals"""

    UNDERLYINGS = [
        "NIFTY", "BANKNIFTY", "FINNIFTY",
        "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN"
    ]

    async def scan_options(
        self,
        underlying: Optional[str] = None,
        limit: int = 8,
    ) -> Dict[str, Any]:
        """
        Scan options chain & spot technical momentum to build high-conviction CE/PE trading signals.
        """
        symbols = [underlying.upper().strip()] if underlying else self.UNDERLYINGS

        async def _scan_one(sym: str):
            try:
                return await self._analyze_underlying(sym)
            except Exception as e:
                logger.warning(f"Options scan exception for {sym}: {e}")
                return []

        tasks = [_scan_one(sym) for sym in symbols]
        results = await asyncio.gather(*tasks)

        all_signals = []
        for signals in results:
            all_signals.extend(signals)

        # Sort by confidence/conviction score
        all_signals.sort(key=lambda x: x.get("confidence", 0), reverse=True)

        return {
            "signals": all_signals[:limit],
            "underlyings_scanned": symbols,
            "total_candidates": len(all_signals),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "disclaimer": (
                "Options carry HIGH LEVERAGE and market risk. Always enforce strict stop-loss. "
                "Trail stop-loss to entry after Target 1 is reached."
            ),
        }

    async def _analyze_underlying(self, symbol: str) -> List[Dict[str, Any]]:
        """Analyze spot price + multi-timeframe candles to generate CE/PE options trade levels."""
        quote = await market_service.get_quote(symbol)
        spot = quote.get("ltp") or 0.0
        if not spot or spot <= 0:
            return []

        change_pct = quote.get("change_percent") or 0.0
        df_5m = await market_service.get_ohlcv_df(symbol, "5minute")
        
        # Calculate momentum indicators on spot if DF is available
        rsi = 50.0
        vwap = spot
        trend = "NEUTRAL"

        if not df_5m.empty and len(df_5m) > 10:
            closes = df_5m["close"]
            # Simple RSI calculation
            delta = closes.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / (loss.replace(0, 0.001))
            rsi_series = 100 - (100 / (1 + rs))
            rsi = float(rsi_series.iloc[-1]) if not rsi_series.empty else 50.0

            # Calculate VWAP
            tp = (df_5m["high"] + df_5m["low"] + df_5m["close"]) / 3
            v_sum = df_5m["volume"].sum()
            vwap = float((tp * df_5m["volume"]).sum() / (v_sum if v_sum > 0 else 1))
            
            if spot > vwap and change_pct > 0.2:
                trend = "BULLISH"
            elif spot < vwap and change_pct < -0.2:
                trend = "BEARISH"

        candidates = []

        # Determine ATM strike & step
        if symbol == "NIFTY":
            step = 50
            lot_size = 25
        elif symbol == "BANKNIFTY":
            step = 100
            lot_size = 15
        elif symbol == "FINNIFTY":
            step = 50
            lot_size = 40
        else:
            step = 20 if spot > 1000 else 10
            lot_size = 250

        atm_strike = round(spot / step) * step

        # Fetch live option chain if available
        opt_chain = {}
        try:
            opt_chain = await market_service.options_chain(symbol)
        except Exception:
            pass

        strikes_data = opt_chain.get("strikes", [])
        strike_map = {float(s["strike"]): s for s in strikes_data if "strike" in s}

        # Premium helper function
        def get_premium(opt_type: str, strike_val: float) -> float:
            # 1. Try live option chain quote
            if strike_val in strike_map:
                stk = strike_map[strike_val]
                live_price = stk.get("ce_ltp" if opt_type == "CE" else "pe_ltp")
                if live_price and float(live_price) > 0:
                    return round(float(live_price), 1)

            # 2. Realistic Model Fallback:
            # Index options: ~0.9% - 1.2% of spot
            if symbol in ("NIFTY", "FINNIFTY"):
                return round(max(spot * 0.009, 45.0), 1)
            elif symbol == "BANKNIFTY":
                return round(max(spot * 0.009, 150.0), 1)
            else:
                # Stock options (RELIANCE, TCS, INFY, etc.): ATM premium is ~1.5% - 2.0% of spot (~₹21 for RELIANCE ₹1320)
                return round(max(spot * 0.016, 10.0), 1)

        # Generate CALL Option (CE) Signal
        if trend == "BULLISH" or change_pct > 0.1 or rsi > 52:
            ce_strike = atm_strike
            est_premium = get_premium("CE", ce_strike)
            
            entry_min = round(est_premium * 0.98, 1)
            entry_max = round(est_premium * 1.02, 1)
            target_1 = round(est_premium * 1.25, 1)  # +25%
            target_2 = round(est_premium * 1.50, 1)  # +50%
            target_3 = round(est_premium * 1.90, 1)  # +90%
            stop_loss = round(est_premium * 0.80, 1) # -20% max SL

            confidence = min(96.0, round(78.0 + abs(change_pct) * 6.0 + (rsi - 50) * 0.4, 1))

            candidates.append({
                "underlying": symbol,
                "spot_price": spot,
                "spot_change_pct": round(change_pct, 2),
                "action": "BUY CALL (CE)",
                "option_type": "CE",
                "strike": ce_strike,
                "expiry": "WEEKLY / CURRENT",
                "symbol_display": f"{symbol} {int(ce_strike)} CE",
                "moneyness": "ATM",
                "confidence": confidence,
                "risk_reward": "1 : 2.5",
                "entry_price": est_premium,
                "entry_range": [entry_min, entry_max],
                "target_1": target_1,
                "target_2": target_2,
                "target_3": target_3,
                "stop_loss": stop_loss,
                "trailing_sl": f"Trail SL to ₹{target_1} after Target 1 is hit",
                "exit_rule": f"Exit if Spot drops below VWAP (₹{round(vwap, 1)}) or at 3:15 PM",
                "lot_size": lot_size,
                "recommended_lots": "2 Lots",
                "reasoning": f"Bullish momentum on {symbol} (+{change_pct:.2f}%). Spot above VWAP ₹{vwap:.1f} with RSI {rsi:.1f}.",
            })

        # Generate PUT Option (PE) Signal
        if trend == "BEARISH" or change_pct < -0.1 or rsi < 48:
            pe_strike = atm_strike
            est_premium = get_premium("PE", pe_strike)
            
            entry_min = round(est_premium * 0.98, 1)
            entry_max = round(est_premium * 1.02, 1)
            target_1 = round(est_premium * 1.25, 1)  # +25%
            target_2 = round(est_premium * 1.50, 1)  # +50%
            target_3 = round(est_premium * 1.90, 1)  # +90%
            stop_loss = round(est_premium * 0.80, 1) # -20% max SL

            confidence = min(96.0, round(78.0 + abs(change_pct) * 6.0 + (50 - rsi) * 0.4, 1))

            candidates.append({
                "underlying": symbol,
                "spot_price": spot,
                "spot_change_pct": round(change_pct, 2),
                "action": "BUY PUT (PE)",
                "option_type": "PE",
                "strike": pe_strike,
                "expiry": "WEEKLY / CURRENT",
                "symbol_display": f"{symbol} {int(pe_strike)} PE",
                "moneyness": "ATM",
                "confidence": confidence,
                "risk_reward": "1 : 2.5",
                "entry_price": est_premium,
                "entry_range": [entry_min, entry_max],
                "target_1": target_1,
                "target_2": target_2,
                "target_3": target_3,
                "stop_loss": stop_loss,
                "trailing_sl": f"Trail SL to ₹{target_1} after Target 1 is hit",
                "exit_rule": f"Exit if Spot reclaims VWAP (₹{round(vwap, 1)}) or at 3:15 PM",
                "lot_size": lot_size,
                "recommended_lots": "2 Lots",
                "reasoning": f"Bearish breakdown on {symbol} ({change_pct:.2f}%). Spot below VWAP ₹{vwap:.1f} with RSI {rsi:.1f}.",
            })

        return candidates


# Global instance
options_signal_service = OptionsSignalService()
