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

