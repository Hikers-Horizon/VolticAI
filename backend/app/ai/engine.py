"""
AI Trading Engine for Indian Intraday Markets

Multi-factor analysis producing BUY / SELL / WAIT with confidence,
entry, stop-loss, targets, and risk-reward. Never recommends when:
  - confidence < 75%
  - risk-reward < 1:2
  - low volume / high spread / choppy market
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
import pandas as pd
from app.indicators.core import TechnicalIndicators
from app.schemas.signal import AnalysisResult, FactorScore
from app.core.config import settings


DISCLAIMER = (
    "AI recommendations are probabilistic and not guaranteed. "
    "Past performance does not guarantee future results. Trade at your own risk. "
    "This is not financial advice."
)


class AITradingEngine:
    """Specialized AI assistant for NSE / NIFTY / BANKNIFTY / FINNIFTY intraday."""

    MIN_CONFIDENCE = settings.AI_MIN_CONFIDENCE  # 75
    MIN_RR = settings.AI_MIN_RISK_REWARD          # 2.0
    MIN_VOLUME_RATIO = 0.7   # vs 20-bar average
    MAX_SPREAD_PCT = 0.15    # 0.15% max bid-ask spread
    CHOPPY_ADX = 18          # ADX below = choppy

    def analyze(
        self,
        symbol: str,
        df: pd.DataFrame,
        timeframe: str = "5minute",
        bid: Optional[float] = None,
        ask: Optional[float] = None,
    ) -> AnalysisResult:
        """Run full multi-factor analysis and return a recommendation."""
        if df is None or len(df) < 52:
            return self._wait(symbol, timeframe, ["Insufficient historical data"])

        ti = TechnicalIndicators(df)
        snap = ti.snapshot()
        if "error" in snap:
            return self._wait(symbol, timeframe, [snap["error"]])

        factors = self._score_factors(snap)
        total_w = sum(f.weight for f in factors) or 1.0
        avg_score = sum(f.score * f.weight for f in factors) / total_w
        bullish = sum(f.score * f.weight for f in factors if f.score >= 50)
        bearish = sum((100 - f.score) * f.weight for f in factors if f.score < 50)
        net = (bullish - bearish) / total_w

        clarity = min(abs(net) / 40.0, 1.0)
        confidence = avg_score * 0.55 + (50 + abs(net) * 0.55) * 0.45
        confidence = max(0.0, min(99.0, confidence + clarity * 8))

        close = float(snap["close"])
        atr = float(snap["atr"] or (close * 0.005))
        if atr <= 0:
            atr = close * 0.005
        vol_ratio = snap["volume"] / snap["avg_volume_20"] if snap["avg_volume_20"] else 1.0

        if snap["ema_9"] > snap["ema_21"] > snap.get("sma_50", snap["ema_21"]):
            confidence += 4
        if snap["ema_9"] < snap["ema_21"] < snap.get("sma_50", snap["ema_21"]):
            confidence += 4
        if snap["supertrend_dir"] == 1 and snap["ema_9"] > snap["ema_21"]:
            confidence += 3
        if snap["supertrend_dir"] == -1 and snap["ema_9"] < snap["ema_21"]:
            confidence += 3
        if snap["adx"] >= 22:
            confidence += 3
        if vol_ratio >= 1.2:
            confidence += 3
        if 45 <= snap["rsi"] <= 68:
            confidence += 2
        confidence = float(min(99.0, confidence))

        if net > 12:
            bias = "BUY"
        elif net < -12:
            bias = "SELL"
        else:
            bias = "BUY" if net >= 0 else "SELL"
        action = bias if abs(net) > 12 else "WAIT"

        hard: List[str] = []
        soft: List[str] = []
        if vol_ratio < 0.5:
            hard.append(f"Very low volume ({vol_ratio:.2f}x average)")
        elif vol_ratio < self.MIN_VOLUME_RATIO:
            soft.append(f"Low volume ({vol_ratio:.2f}x average)")
        if bid and ask and bid > 0:
            spread_pct = ((ask - bid) / close) * 100
            if spread_pct > 0.35:
                hard.append(f"Excessive spread ({spread_pct:.3f}%)")
            elif spread_pct > self.MAX_SPREAD_PCT:
                soft.append(f"Elevated spread ({spread_pct:.3f}%)")
        if snap["adx"] < 14:
            hard.append(f"No trend (ADX {snap['adx']:.1f})")
        elif snap["adx"] < self.CHOPPY_ADX:
            soft.append(f"Mild chop (ADX {snap['adx']:.1f})")

        entry, sl, t1, t2, t3, rr = self._levels(bias, close, atr, snap)
        if action != "WAIT" and rr is not None and rr < self.MIN_RR:
            hard.append(f"Risk-reward {rr:.2f} < {self.MIN_RR}")
        if confidence < self.MIN_CONFIDENCE:
            soft.append(f"Confidence {confidence:.1f}% < {self.MIN_CONFIDENCE}%")

        is_tradeable = (
            action in ("BUY", "SELL")
            and not hard
            and confidence >= self.MIN_CONFIDENCE
            and rr is not None
            and rr >= self.MIN_RR
        )
        all_rej = hard + soft
        final_action = action
        if not is_tradeable and abs(net) <= 12:
            final_action = "WAIT"

        if is_tradeable and confidence >= 85 and vol_ratio >= 1.2 and snap["adx"] >= 25:
            grade = "A+"
        elif is_tradeable and confidence >= 80:
            grade = "A"
        elif is_tradeable:
            grade = "B"
        else:
            grade = "C"

        reason = self._build_reason(final_action if final_action != "WAIT" else bias, factors, snap)
        if not is_tradeable and all_rej:
            reason += " | Levels are reference only (filters not fully passed)."

        plan = self._position_plan(
            final_action if final_action != "WAIT" else bias,
            entry, sl, t1, t2, t3, capital=10000.0,
        )
        trade_plan = self._trade_plan_text(
            symbol, final_action, is_tradeable, grade, confidence,
            entry, sl, t1, t2, t3, rr, plan, snap,
        )

        return AnalysisResult(
            symbol=symbol,
            action=final_action,
            confidence=round(confidence, 1),
            entry_price=round(entry, 2) if entry is not None else None,
            stop_loss=round(sl, 2) if sl is not None else None,
            target_1=round(t1, 2) if t1 is not None else None,
            target_2=round(t2, 2) if t2 is not None else None,
            target_3=round(t3, 2) if t3 is not None else None,
            risk_reward=round(rr, 2) if rr is not None else None,
            timeframe=timeframe,
            reason=reason,
            factors=factors,
            analysis={
                **snap,
                "bias": bias,
                "net": round(net, 2),
                "avg_score": round(avg_score, 2),
                "vol_ratio": round(vol_ratio, 2),
                "grade": grade,
                "levels": {
                    "entry": round(entry, 2) if entry is not None else None,
                    "stop_loss": round(sl, 2) if sl is not None else None,
                    "target_1": round(t1, 2) if t1 is not None else None,
                    "target_2": round(t2, 2) if t2 is not None else None,
                    "target_3": round(t3, 2) if t3 is not None else None,
                    "risk_reward": round(rr, 2) if rr is not None else None,
                    "atr": round(atr, 4),
                },
                "position": plan,
            },
            is_tradeable=is_tradeable,
            rejection_reasons=all_rej,
            capital=float(plan.get("capital", 10000)),
            quantity=int(plan.get("quantity", 0)),
            position_value=float(plan.get("position_value", 0)),
            risk_amount=float(plan.get("risk_amount", 0)),
            reward_t1=float(plan.get("reward_t1", 0)),
            reward_t2=float(plan.get("reward_t2", 0)),
            reward_t3=float(plan.get("reward_t3", 0)),
            setup_grade=grade,
            groww_plan=str(plan.get("groww_plan", "")),
            trade_plan=trade_plan,
            disclaimer=DISCLAIMER,
        )

    # ── Factor scoring ───────────────────────────────────────────
    def _score_factors(self, s: Dict[str, Any]) -> List[FactorScore]:
        factors: List[FactorScore] = []
        close = s["close"]

        # Trend (EMA stack + Supertrend)
        trend_score = 50.0
        if s["ema_9"] > s["ema_21"] > s["sma_50"]:
            trend_score = 85
            detail = "Bullish EMA stack (9>21>50)"
        elif s["ema_9"] < s["ema_21"] < s["sma_50"]:
            trend_score = 15
            detail = "Bearish EMA stack (9<21<50)"
        elif s["ema_9"] > s["ema_21"]:
            trend_score = 65
            detail = "Short-term bullish (EMA9>EMA21)"
        else:
            trend_score = 35
            detail = "Short-term bearish (EMA9<EMA21)"
        if s["supertrend_dir"] == 1:
            trend_score = min(trend_score + 10, 100)
            detail += " | Supertrend UP"
        else:
            trend_score = max(trend_score - 10, 0)
            detail += " | Supertrend DOWN"
        factors.append(FactorScore(name="Trend", score=trend_score, weight=1.5, detail=detail))

        # Momentum (RSI + MACD)
        rsi = s["rsi"]
        mom = 50.0
        if 55 <= rsi <= 70:
            mom = 80
            md = f"RSI healthy bullish ({rsi:.1f})"
        elif rsi > 70:
            mom = 40
            md = f"RSI overbought ({rsi:.1f})"
        elif 30 <= rsi <= 45:
            mom = 20
            md = f"RSI weak ({rsi:.1f})"
        elif rsi < 30:
            mom = 60  # potential bounce
            md = f"RSI oversold bounce zone ({rsi:.1f})"
        else:
            mom = 50
            md = f"RSI neutral ({rsi:.1f})"
        if s["macd_hist"] > 0 and s["macd"] > s["macd_signal"]:
            mom = min(mom + 15, 100)
            md += " | MACD bullish"
        elif s["macd_hist"] < 0:
            mom = max(mom - 15, 0)
            md += " | MACD bearish"
        factors.append(FactorScore(name="Momentum", score=mom, weight=1.3, detail=md))

        # Volume
        vol_r = s["volume"] / s["avg_volume_20"] if s["avg_volume_20"] else 1
        vs = min(vol_r * 50, 100) if vol_r >= 1 else max(vol_r * 40, 10)
        factors.append(FactorScore(
            name="Volume", score=vs, weight=1.2,
            detail=f"Volume {vol_r:.2f}x 20-bar avg",
        ))

        # Volatility / ADX
        adx = s["adx"]
        if adx >= 25:
            vs_adx = 80 if s["plus_di"] > s["minus_di"] else 20
            ad = f"Strong trend ADX {adx:.1f}"
        elif adx >= 18:
            vs_adx = 60 if s["plus_di"] > s["minus_di"] else 40
            ad = f"Moderate trend ADX {adx:.1f}"
        else:
            vs_adx = 50
            ad = f"Weak/choppy ADX {adx:.1f}"
        factors.append(FactorScore(name="Volatility", score=vs_adx, weight=1.0, detail=ad))

        # VWAP position
        vwap = s["vwap"]
        if close > vwap * 1.002:
            vw = 75
            vd = f"Above VWAP ({close:.2f} > {vwap:.2f})"
        elif close < vwap * 0.998:
            vw = 25
            vd = f"Below VWAP ({close:.2f} < {vwap:.2f})"
        else:
            vw = 50
            vd = f"At VWAP ({vwap:.2f})"
        factors.append(FactorScore(name="VWAP", score=vw, weight=1.4, detail=vd))

        # Bollinger position
        bb_range = s["bb_upper"] - s["bb_lower"]
        if bb_range > 0:
            bb_pos = (close - s["bb_lower"]) / bb_range
            if bb_pos > 0.8:
                bs, bd = 35, "Near upper BB (overbought risk)"
            elif bb_pos < 0.2:
                bs, bd = 65, "Near lower BB (oversold bounce)"
            else:
                bs, bd = 55, f"BB mid-zone ({bb_pos:.0%})"
        else:
            bs, bd = 50, "BB collapsed"
        factors.append(FactorScore(name="Bollinger", score=bs, weight=0.8, detail=bd))

        # Support / Resistance via pivots
        piv = s.get("pivots", {})
        pp = piv.get("pp", close)
        if close > pp:
            sr, sd = 70, f"Above pivot {pp:.2f}"
        else:
            sr, sd = 30, f"Below pivot {pp:.2f}"
        factors.append(FactorScore(name="S/R", score=sr, weight=1.0, detail=sd))

        return factors

    def _levels(self, action, close, atr, snap):
        """Always return entry / SL / T1-T3 / RR for the given directional bias."""
        import math
        if close is None or (isinstance(close, float) and (math.isnan(close) or close <= 0)):
            return None, None, None, None, None, None
        if atr is None or (isinstance(atr, float) and (math.isnan(atr) or atr <= 0)):
            atr = close * 0.005

        entry = float(close)
        atr = float(atr)
        st = snap.get("supertrend")
        st_dir = snap.get("supertrend_dir")

        # Default to BUY-style levels if unknown
        side = action if action in ("BUY", "SELL") else "BUY"

        if side == "BUY":
            raw_sl = entry - 1.5 * atr
            try:
                if st_dir == 1 and st is not None and not math.isnan(float(st)):
                    raw_sl = min(raw_sl, float(st))
            except Exception:
                pass
            sl = float(raw_sl)
            risk = entry - sl
            if risk <= 0:
                risk = atr
                sl = entry - risk
            t1 = entry + 2.0 * risk
            t2 = entry + 3.0 * risk
            t3 = entry + 4.5 * risk
            rr = (t1 - entry) / risk if risk else 2.0
            return entry, sl, t1, t2, t3, rr

        # SELL
        raw_sl = entry + 1.5 * atr
        try:
            if st_dir == -1 and st is not None and not math.isnan(float(st)):
                raw_sl = max(raw_sl, float(st))
        except Exception:
            pass
        sl = float(raw_sl)
        risk = sl - entry
        if risk <= 0:
            risk = atr
            sl = entry + risk
        t1 = entry - 2.0 * risk
        t2 = entry - 3.0 * risk
        t3 = entry - 4.5 * risk
        rr = (entry - t1) / risk if risk else 2.0
        return entry, sl, t1, t2, t3, rr

    def _build_reason(self, action, factors, snap) -> str:
        top = sorted(factors, key=lambda f: abs(f.score - 50) * f.weight, reverse=True)[:4]
        parts = [f.detail for f in top]
        if action == "BUY":
            return "Bullish setup: " + "; ".join(parts) + f". RSI {snap['rsi']:.0f}, ADX {snap['adx']:.0f}."
        if action == "SELL":
            return "Bearish setup: " + "; ".join(parts) + f". RSI {snap['rsi']:.0f}, ADX {snap['adx']:.0f}."
        return "No high-conviction setup. " + "; ".join(parts) + ". Waiting for clearer signal."

    def _position_plan(self, side, entry, sl, t1, t2, t3, capital=10000.0):
        """Cash equity plan for Groww with ~Rs 10,000 capital."""
        empty = {
            "capital": capital, "quantity": 0, "position_value": 0.0,
            "risk_amount": 0.0, "reward_t1": 0.0, "reward_t2": 0.0, "reward_t3": 0.0,
            "groww_plan": "Insufficient levels for position sizing.",
            "risk_pct_capital": 0.0,
        }
        try:
            entry = float(entry); sl = float(sl)
            t1 = float(t1); t2 = float(t2); t3 = float(t3)
        except Exception:
            return empty
        if entry <= 0:
            return empty
        # Max shares by capital
        qty = int(capital // entry)
        if qty < 1:
            return {
                **empty,
                "groww_plan": (
                    f"Price Rs {entry:.2f} > capital Rs {capital:.0f}. "
                    f"Use a cheaper stock or increase capital. Cannot buy 1 share."
                ),
            }
        risk_ps = abs(entry - sl)
        rew1 = abs(t1 - entry)
        rew2 = abs(t2 - entry)
        rew3 = abs(t3 - entry)
        # Cap risk at ~2% of capital when possible
        max_risk = capital * 0.02
        if risk_ps > 0 and qty * risk_ps > max_risk:
            qty_risk = max(1, int(max_risk // risk_ps))
            qty = min(qty, qty_risk)
        pos_val = qty * entry
        risk_amt = qty * risk_ps
        r1, r2, r3 = qty * rew1, qty * rew2, qty * rew3
        side_txt = "BUY" if side == "BUY" else "SELL"
        plan = (
            f"GROWW CASH PLAN (capital Rs {capital:.0f})\n"
            f"1) {side_txt} {qty} shares of stock near Rs {entry:.2f} (value ~Rs {pos_val:.0f})\n"
            f"2) Place SL immediately at Rs {sl:.2f} (risk ~Rs {risk_amt:.0f} / {100*risk_amt/capital:.1f}% capital)\n"
            f"3) Book 50% qty near T1 Rs {t1:.2f} (~Rs {r1:.0f})\n"
            f"4) Book 30% near T2 Rs {t2:.2f} (~Rs {r2:.0f})\n"
            f"5) Trail rest to T3 Rs {t3:.2f} (~Rs {r3:.0f}) or exit EOD\n"
            f"NOTE: Rs 2000 target on Rs 10000 needs ~20% move — rare intraday. "
            f"Realistic day goal: protect capital; scale only if T1/T2 hit."
        )
        return {
            "capital": capital,
            "quantity": qty,
            "position_value": round(pos_val, 2),
            "risk_amount": round(risk_amt, 2),
            "reward_t1": round(r1, 2),
            "reward_t2": round(r2, 2),
            "reward_t3": round(r3, 2),
            "risk_pct_capital": round(100 * risk_amt / capital, 2) if capital else 0,
            "groww_plan": plan,
        }

    def _trade_plan_text(self, symbol, action, is_tradeable, grade, conf,
                         entry, sl, t1, t2, t3, rr, plan, snap):
        status = "TRADEABLE" if is_tradeable else "WATCH / REFERENCE"
        qty = plan.get("quantity", 0)
        return (
            f"{symbol} {action} | Grade {grade} | {status} | Conf {conf:.0f}%\n"
            f"Entry {entry} | SL {sl} | T1 {t1} | T2 {t2} | T3 {t3} | RR 1:{rr}\n"
            f"Qty (Rs10k): {qty} | Risk Rs {plan.get('risk_amount', 0)} | "
            f"T1 Rs {plan.get('reward_t1', 0)} / T2 Rs {plan.get('reward_t2', 0)} / T3 Rs {plan.get('reward_t3', 0)}\n"
            f"RSI {snap.get('rsi', 0):.0f} ADX {snap.get('adx', 0):.0f} "
            f"EMA9/21 {snap.get('ema_9', 0):.1f}/{snap.get('ema_21', 0):.1f}\n"
            f"Execute manually on Groww. No auto orders."
        )

    def _wait(self, symbol, timeframe, reasons) -> AnalysisResult:
        return AnalysisResult(
            symbol=symbol, action="WAIT", confidence=0.0, timeframe=timeframe,
            reason="; ".join(reasons), is_tradeable=False,
            rejection_reasons=reasons, disclaimer=DISCLAIMER,
            setup_grade="C", capital=10000.0,
        )
