"""AI Signal generation — full research: history + multi-TF + news + levels"""
from __future__ import annotations
import asyncio
import time
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import pandas as pd
from app.ai.engine import AITradingEngine
from app.services.market_data import market_service
from app.services.news import fetch_news, news_aggregate
from app.schemas.signal import AnalysisResult, FactorScore, NewsItem
from app.indicators.core import TechnicalIndicators

DEFAULT_SCAN_LIST = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN",
    "BHARTIARTL", "ITC", "KOTAKBANK", "LT", "WIPRO", "AXISBANK",
    "BAJFINANCE", "MARUTI", "TATAMOTORS", "NIFTY", "BANKNIFTY",
]

DASHBOARD_SCAN = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
    "SBIN", "NIFTY", "BANKNIFTY",
]

RESEARCH_TFS = ("5minute", "15minute", "1hour")


class SignalService:
    def __init__(self):
        self.engine = AITradingEngine()
        self._sem = asyncio.Semaphore(6)

    async def analyze_symbol(
        self,
        symbol: str,
        timeframe: str = "5minute",
        full: bool = True,
    ) -> AnalysisResult:
        """Full signal: multi-TF live history + news + publish package."""
        sym = symbol.upper().strip()

        # Parallel: primary TF hist, quote, news, secondary TFs
        async def _hist(tf: str):
            try:
                return tf, await market_service.get_ohlcv_df(sym, tf)
            except Exception:
                return tf, pd.DataFrame()

        async def _quote():
            try:
                return await market_service.get_quote(sym)
            except Exception:
                return {}

        async def _news():
            try:
                return await fetch_news(sym, limit=8)
            except Exception:
                return []

        tfs = [timeframe] + [t for t in RESEARCH_TFS if t != timeframe]
        hist_tasks = [_hist(tf) for tf in tfs[:3]]

        async def _no_news():
            return []

        hist_pairs, quote, headlines = await asyncio.gather(
            asyncio.gather(*hist_tasks),
            _quote(),
            _news() if full else _no_news(),
        )

        # Map TF -> df
        tf_map: Dict[str, pd.DataFrame] = {}
        for tf, hdf in hist_pairs:
            tf_map[tf] = hdf

        df = tf_map.get(timeframe)
        if df is None or getattr(df, "empty", True):
            for v in tf_map.values():
                if v is not None and not getattr(v, "empty", True):
                    df = v
                    break

        bid = quote.get("bid") if quote else None
        ask = quote.get("ask") if quote else None

        # Multi-TF structure snapshot
        multi_tf = self._multi_tf_summary(tf_map)

        # Core technical analysis on primary TF
        result = self.engine.analyze(
            symbol=sym,
            df=df if df is not None else pd.DataFrame(),
            timeframe=timeframe,
            bid=bid,
            ask=ask,
        )

        # News factor
        news_agg = news_aggregate(headlines or [])
        news_factor = FactorScore(
            name="News",
            score=float(news_agg["score"]),
            weight=float(news_agg["weight"]),
            detail=str(news_agg["detail"]),
        )
        factors = list(result.factors or []) + [news_factor]

        # Multi-TF alignment factor
        mtf_factor = self._mtf_factor(multi_tf, result.action)
        factors.append(mtf_factor)

        # Re-score confidence with news + MTF (transparent weighted blend)
        conf = self._blend_confidence(result.confidence, news_agg, multi_tf, result.action)

        # History summary from primary bars
        history_summary = self._history_summary(sym, df, quote)

        # Rebuild tradeable with updated confidence (still enforce RR + hard filters)
        rejection = list(result.rejection_reasons or [])
        # Replace old confidence rejection if present
        rejection = [r for r in rejection if not r.lower().startswith("confidence")]
        if conf < self.engine.MIN_CONFIDENCE:
            rejection.append(f"Confidence {conf:.1f}% < {self.engine.MIN_CONFIDENCE}%")

        action = result.action
        is_tradeable = (
            action in ("BUY", "SELL")
            and conf >= self.engine.MIN_CONFIDENCE
            and result.risk_reward is not None
            and result.risk_reward >= self.engine.MIN_RR
            and not any(
                x.startswith("Low volume") or x.startswith("High spread") or x.startswith("Choppy")
                for x in rejection
            )
            and conf >= self.engine.MIN_CONFIDENCE
        )
        # Keep residual filter rejections
        if not is_tradeable and conf >= self.engine.MIN_CONFIDENCE:
            # still blocked by volume/choppy/rr etc
            pass
        else:
            rejection = [r for r in rejection if not r.startswith("Confidence")] if is_tradeable else rejection

        # Thesis / publish package
        thesis, invalidation, summary, publish = self._build_publish(
            sym=sym,
            action=action,
            conf=conf,
            result=result,
            news_agg=news_agg,
            headlines=headlines or [],
            history_summary=history_summary,
            multi_tf=multi_tf,
            quote=quote or {},
            is_tradeable=is_tradeable,
            rejection=rejection,
        )

        news_items = [
            NewsItem(
                title=h.get("title", ""),
                link=h.get("link", ""),
                source=h.get("source", ""),
                published=h.get("published", ""),
                sentiment=float(h.get("sentiment") or 0),
                bias=h.get("bias", "NEUTRAL"),
            )
            for h in (headlines or [])[:6]
        ]

        analysis = dict(result.analysis or {})
        analysis["news"] = news_agg
        analysis["multi_tf"] = multi_tf
        analysis["quote"] = quote or {}
        analysis["research"] = {
            "full": full,
            "timeframes": list(tf_map.keys()),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Rebuild position plan after final confidence (still based on levels)
        plan = self.engine._position_plan(
            action if action != "WAIT" else "BUY",
            result.entry_price, result.stop_loss,
            result.target_1, result.target_2, result.target_3,
            capital=10000.0,
        )
        grade = result.setup_grade or (result.analysis or {}).get("grade") or ("B" if is_tradeable else "C")
        if is_tradeable and conf >= 85:
            grade = "A+" if conf >= 88 else "A"
        elif is_tradeable:
            grade = grade if grade in ("A+", "A", "B") else "B"
        else:
            grade = "C"

        trade_plan = self.engine._trade_plan_text(
            sym, action, is_tradeable, grade, conf,
            result.entry_price, result.stop_loss,
            result.target_1, result.target_2, result.target_3,
            result.risk_reward, plan, result.analysis or {},
        )

        # Enrich publish pack with Groww plan
        publish_full = publish + "\n\n" + str(plan.get("groww_plan") or "") + "\n\n" + trade_plan

        return AnalysisResult(
            symbol=sym,
            action=action,
            confidence=round(conf, 1),
            entry_price=result.entry_price,
            stop_loss=result.stop_loss,
            target_1=result.target_1,
            target_2=result.target_2,
            target_3=result.target_3,
            risk_reward=result.risk_reward,
            timeframe=timeframe,
            reason=result.reason,
            factors=factors,
            analysis=analysis,
            is_tradeable=is_tradeable,
            rejection_reasons=rejection,
            summary=summary,
            thesis=thesis,
            invalidation=invalidation,
            history_summary=history_summary,
            news_bias=str(news_agg.get("bias") or "NEUTRAL"),
            news=news_items,
            multi_tf=multi_tf,
            quote=quote or {},
            publish_text=publish_full,
            generated_at=datetime.now(timezone.utc).isoformat(),
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
            disclaimer=result.disclaimer,
        )

    def _multi_tf_summary(self, tf_map: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for tf, df in tf_map.items():
            if df is None or len(df) < 30:
                out[tf] = {"ok": False, "error": "insufficient bars"}
                continue
            try:
                ti = TechnicalIndicators(df)
                snap = ti.snapshot()
                if "error" in snap:
                    out[tf] = {"ok": False, "error": snap["error"]}
                    continue
                trend = "BULL" if snap["ema_9"] > snap["ema_21"] else "BEAR"
                if snap["ema_9"] > snap["ema_21"] > snap.get("sma_50", snap["ema_21"]):
                    trend = "BULL_STRONG"
                elif snap["ema_9"] < snap["ema_21"] < snap.get("sma_50", snap["ema_21"]):
                    trend = "BEAR_STRONG"
                out[tf] = {
                    "ok": True,
                    "close": round(float(snap["close"]), 2),
                    "rsi": round(float(snap["rsi"]), 1),
                    "adx": round(float(snap["adx"]), 1),
                    "supertrend_dir": int(snap["supertrend_dir"]),
                    "ema_9": round(float(snap["ema_9"]), 2),
                    "ema_21": round(float(snap["ema_21"]), 2),
                    "vwap": round(float(snap["vwap"]), 2),
                    "trend": trend,
                    "bars": len(df),
                }
            except Exception as e:
                out[tf] = {"ok": False, "error": str(e)}
        return out

    def _mtf_factor(self, multi_tf: Dict[str, Any], action: str) -> FactorScore:
        ok = [v for v in multi_tf.values() if v.get("ok")]
        if not ok:
            return FactorScore(name="MultiTF", score=50, weight=0.8, detail="Multi-TF data unavailable")
        bull = sum(1 for v in ok if "BULL" in str(v.get("trend", "")))
        bear = sum(1 for v in ok if "BEAR" in str(v.get("trend", "")))
        if bull > bear:
            score, detail = 70 + 10 * (bull - bear), f"MTF bullish alignment {bull}/{len(ok)}"
        elif bear > bull:
            score, detail = 30 - 10 * (bear - bull), f"MTF bearish alignment {bear}/{len(ok)}"
        else:
            score, detail = 50, f"MTF mixed {bull}B/{bear}S of {len(ok)}"
        # bonus if aligns with action
        if action == "BUY" and bull > bear:
            score = min(95, score + 8)
        if action == "SELL" and bear > bull:
            score = max(5, score - 8)
            score = min(score, 30) if score > 40 else score
        return FactorScore(
            name="MultiTF",
            score=float(max(5, min(95, score))),
            weight=1.2,
            detail=detail,
        )

    def _blend_confidence(
        self, base: float, news_agg: Dict[str, Any], multi_tf: Dict[str, Any], action: str
    ) -> float:
        conf = float(base)
        # News nudge ±12
        avg = float(news_agg.get("avg_sentiment") or 0)
        if action == "BUY":
            conf += avg * 12
        elif action == "SELL":
            conf -= avg * 12
        # MTF alignment nudge
        ok = [v for v in multi_tf.values() if v.get("ok")]
        if ok:
            bull = sum(1 for v in ok if "BULL" in str(v.get("trend", "")))
            bear = sum(1 for v in ok if "BEAR" in str(v.get("trend", "")))
            if action == "BUY" and bull > bear:
                conf += 6 * (bull - bear) / len(ok)
            if action == "SELL" and bear > bull:
                conf += 6 * (bear - bull) / len(ok)
            if action == "BUY" and bear > bull:
                conf -= 5
            if action == "SELL" and bull > bear:
                conf -= 5
        return max(0.0, min(99.0, conf))

    def _history_summary(self, sym: str, df: Optional[pd.DataFrame], quote: Dict[str, Any]) -> str:
        if df is None or df.empty or "close" not in df.columns:
            ltp = quote.get("ltp")
            return f"{sym}: live quote only" + (f" LTP ₹{ltp}" if ltp else "")
        closes = df["close"].astype(float)
        vols = df["volume"].astype(float) if "volume" in df.columns else None
        last = float(closes.iloc[-1])
        prev = float(closes.iloc[-2]) if len(closes) > 1 else last
        chg = ((last - prev) / prev * 100) if prev else 0
        hi = float(df["high"].astype(float).tail(20).max())
        lo = float(df["low"].astype(float).tail(20).min())
        # session-ish stats
        day_open = float(quote.get("open") or closes.iloc[0])
        day_chg = ((last - day_open) / day_open * 100) if day_open else 0
        vol_note = ""
        if vols is not None and len(vols) >= 20:
            vr = float(vols.iloc[-1] / max(vols.tail(20).mean(), 1))
            vol_note = f" · vol {vr:.2f}x 20-bar avg"
        return (
            f"{sym} last ₹{last:.2f} ({chg:+.2f}% bar) · day {day_chg:+.2f}% from open ₹{day_open:.2f} · "
            f"20-bar range ₹{lo:.2f}–₹{hi:.2f}{vol_note} · bars={len(df)}"
        )

    def _build_publish(
        self, sym, action, conf, result, news_agg, headlines, history_summary,
        multi_tf, quote, is_tradeable, rejection,
    ):
        e, sl = result.entry_price, result.stop_loss
        t1, t2, t3 = result.target_1, result.target_2, result.target_3
        rr = result.risk_reward
        ltp = quote.get("ltp") or e

        mtf_bits = []
        for tf, v in multi_tf.items():
            if v.get("ok"):
                mtf_bits.append(f"{tf}:{v.get('trend')} RSI {v.get('rsi')}")
        mtf_line = " · ".join(mtf_bits) if mtf_bits else "MTF n/a"

        tops = [h.get("title") for h in (headlines or [])[:3] if h.get("title")]
        news_line = news_agg.get("detail") or "No news"
        if tops:
            news_line += " | " + " // ".join(tops[:2])

        thesis = (
            f"{action} bias on {sym} at ~₹{ltp}. "
            f"Technical: {result.reason} "
            f"Multi-TF: {mtf_line}. "
            f"News: {news_agg.get('bias', 'NEUTRAL')} ({news_agg.get('avg_sentiment', 0):+.2f})."
        )
        if action == "BUY":
            invalidation = f"Thesis invalid below SL ₹{sl} or if 15m/1h structure turns BEAR with rising volume."
        elif action == "SELL":
            invalidation = f"Thesis invalid above SL ₹{sl} or if 15m/1h structure turns BULL with rising volume."
        else:
            invalidation = "No high-conviction directional edge — wait for cleaner structure."

        status = "TRADEABLE SETUP" if is_tradeable else "REFERENCE ONLY (filters not fully passed)"
        filt = (", ".join(rejection[:4]) if rejection else "none")

        summary = (
            f"{sym} {action} · Conf {conf:.0f}% · {status}. "
            f"Entry ₹{e} · SL ₹{sl} · T1 ₹{t1} · T2 ₹{t2} · T3 ₹{t3} · R:R 1:{rr}."
        )

        publish = "\n".join([
            f"#{sym} | {action} | Confidence {conf:.0f}%",
            f"Status: {status}",
            f"LTP: ₹{ltp}",
            f"Entry: ₹{e}",
            f"Stop Loss: ₹{sl}",
            f"Targets: T1 ₹{t1} | T2 ₹{t2} | T3 ₹{t3}",
            f"Risk:Reward: 1:{rr}",
            f"",
            f"History: {history_summary}",
            f"Multi-TF: {mtf_line}",
            f"News: {news_line}",
            f"",
            f"Thesis: {thesis}",
            f"Invalidation: {invalidation}",
            f"Filters: {filt}",
            f"",
            "Disclaimer: Probabilistic AI research — not guaranteed, not SEBI advice. "
            "You are solely responsible for trades you take or publish.",
        ])

        return thesis, invalidation, summary, publish

    async def _safe_analyze(self, symbol: str, timeframe: str) -> Optional[AnalysisResult]:
        async with self._sem:
            try:
                # Scans stay lighter (no full news fetch storm)
                return await self.analyze_symbol(symbol, timeframe, full=False)
            except Exception:
                return None

    async def scan(
        self,
        symbols: Optional[List[str]] = None,
        timeframe: str = "5minute",
        tradeable_only: bool = False,
    ) -> List[AnalysisResult]:
        symbols = symbols or DEFAULT_SCAN_LIST
        tasks = [self._safe_analyze(sym, timeframe) for sym in symbols]
        raw = await asyncio.gather(*tasks)
        results = [r for r in raw if r is not None]
        if tradeable_only:
            results = [r for r in results if r.is_tradeable]
        results.sort(key=lambda x: (x.is_tradeable, x.confidence), reverse=True)
        return results


signal_service = SignalService()
