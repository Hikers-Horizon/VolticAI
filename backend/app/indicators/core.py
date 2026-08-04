"""
Technical Indicators - EMA, SMA, RSI, MACD, Supertrend, ATR, ADX,
VWAP, Bollinger Bands, Fibonacci, Pivot Points, Ichimoku, Volume Profile, OBV
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, List, Tuple


class TechnicalIndicators:
    """Compute technical indicators from OHLCV DataFrame.

    Expected columns: open, high, low, close, volume
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        for col in ("open", "high", "low", "close", "volume"):
            if col not in self.df.columns:
                raise ValueError(f"Missing column: {col}")

    # ── Moving Averages ──────────────────────────────────────────
    def sma(self, period: int = 20, col: str = "close") -> pd.Series:
        return self.df[col].rolling(window=period).mean()

    def ema(self, period: int = 20, col: str = "close") -> pd.Series:
        return self.df[col].ewm(span=period, adjust=False).mean()

    # ── RSI ──────────────────────────────────────────────────────
    def rsi(self, period: int = 14) -> pd.Series:
        delta = self.df["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))

    # ── MACD ─────────────────────────────────────────────────────
    def macd(self, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        ema_fast = self.ema(fast)
        ema_slow = self.ema(slow)
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return {"macd": macd_line, "signal": signal_line, "histogram": histogram}

    # ── ATR ──────────────────────────────────────────────────────
    def atr(self, period: int = 14) -> pd.Series:
        high, low, close = self.df["high"], self.df["low"], self.df["close"]
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs(),
        ], axis=1).max(axis=1)
        return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    # ── Supertrend (numpy-fast loop) ─────────────────────────────
    def supertrend(self, period: int = 10, multiplier: float = 3.0) -> Dict[str, pd.Series]:
        atr = self.atr(period).to_numpy(dtype=float)
        high = self.df["high"].to_numpy(dtype=float)
        low = self.df["low"].to_numpy(dtype=float)
        close = self.df["close"].to_numpy(dtype=float)
        hl2 = (high + low) / 2.0
        upper = hl2 + multiplier * atr
        lower = hl2 - multiplier * atr
        n = len(close)
        st = np.empty(n, dtype=float)
        direction = np.empty(n, dtype=int)
        st[0] = upper[0]
        direction[0] = 1
        for i in range(1, n):
            if close[i] > upper[i - 1]:
                direction[i] = 1
            elif close[i] < lower[i - 1]:
                direction[i] = -1
            else:
                direction[i] = direction[i - 1]
            st[i] = lower[i] if direction[i] == 1 else upper[i]
        idx = self.df.index
        return {
            "supertrend": pd.Series(st, index=idx),
            "direction": pd.Series(direction, index=idx),
        }

    # ── ADX ──────────────────────────────────────────────────────
    def adx(self, period: int = 14) -> Dict[str, pd.Series]:
        high, low = self.df["high"], self.df["low"]
        plus_dm = high.diff().clip(lower=0)
        minus_dm = (-low.diff()).clip(lower=0)
        plus_dm[plus_dm < minus_dm] = 0
        minus_dm[minus_dm < plus_dm] = 0
        atr = self.atr(period)
        plus_di = 100 * (plus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr)
        minus_di = 100 * (minus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr)
        dx = (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)) * 100
        adx = dx.ewm(alpha=1 / period, adjust=False).mean()
        return {"adx": adx, "plus_di": plus_di, "minus_di": minus_di}

    # ── VWAP ─────────────────────────────────────────────────────
    def vwap(self) -> pd.Series:
        tp = (self.df["high"] + self.df["low"] + self.df["close"]) / 3
        return (tp * self.df["volume"]).cumsum() / self.df["volume"].cumsum().replace(0, np.nan)

    # ── Bollinger Bands ──────────────────────────────────────────
    def bollinger(self, period: int = 20, std_dev: float = 2.0) -> Dict[str, pd.Series]:
        mid = self.sma(period)
        std = self.df["close"].rolling(window=period).std()
        return {"upper": mid + std_dev * std, "middle": mid, "lower": mid - std_dev * std}

    # ── Fibonacci Retracement ────────────────────────────────────
    def fibonacci(self, lookback: int = 50) -> Dict[str, float]:
        recent = self.df.tail(lookback)
        high, low = recent["high"].max(), recent["low"].min()
        diff = high - low
        levels = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
        return {f"fib_{int(l*1000)}": high - diff * l for l in levels}

    # ── Pivot Points ─────────────────────────────────────────────
    def pivot_points(self) -> Dict[str, float]:
        h = self.df["high"].iloc[-1]
        l = self.df["low"].iloc[-1]
        c = self.df["close"].iloc[-1]
        pp = (h + l + c) / 3
        return {
            "pp": pp,
            "r1": 2 * pp - l, "r2": pp + (h - l), "r3": h + 2 * (pp - l),
            "s1": 2 * pp - h, "s2": pp - (h - l), "s3": l - 2 * (h - pp),
        }

    # ── Ichimoku ─────────────────────────────────────────────────
    def ichimoku(self) -> Dict[str, pd.Series]:
        high, low = self.df["high"], self.df["low"]
        tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2
        kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2
        senkou_a = ((tenkan + kijun) / 2).shift(26)
        senkou_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
        chikou = self.df["close"].shift(-26)
        return {
            "tenkan": tenkan, "kijun": kijun,
            "senkou_a": senkou_a, "senkou_b": senkou_b, "chikou": chikou,
        }

    # ── OBV ──────────────────────────────────────────────────────
    def obv(self) -> pd.Series:
        direction = np.sign(self.df["close"].diff()).fillna(0)
        return (direction * self.df["volume"]).cumsum()

    # ── Volume Profile (simplified) ──────────────────────────────
    def volume_profile(self, bins: int = 20) -> Dict[str, Any]:
        prices = (self.df["high"] + self.df["low"]) / 2
        hist, edges = np.histogram(prices, bins=bins, weights=self.df["volume"])
        poc_idx = int(np.argmax(hist))
        return {
            "poc": float((edges[poc_idx] + edges[poc_idx + 1]) / 2),
            "bins": edges.tolist(),
            "volumes": hist.tolist(),
        }

    # ── Full Snapshot ────────────────────────────────────────────
    def snapshot(self) -> Dict[str, Any]:
        """Latest values of all key indicators for AI analysis."""
        if len(self.df) < 52:
            return {"error": "Insufficient data (need >= 52 bars)"}

        rsi = self.rsi()
        macd = self.macd()
        st = self.supertrend()
        adx = self.adx()
        bb = self.bollinger()
        atr = self.atr()
        vwap = self.vwap()
        ema9 = self.ema(9)
        ema21 = self.ema(21)
        sma50 = self.sma(50)

        last = -1
        close = float(self.df["close"].iloc[last])
        return {
            "close": close,
            "volume": int(self.df["volume"].iloc[last]),
            "avg_volume_20": float(self.df["volume"].tail(20).mean()),
            "rsi": float(rsi.iloc[last]),
            "macd": float(macd["macd"].iloc[last]),
            "macd_signal": float(macd["signal"].iloc[last]),
            "macd_hist": float(macd["histogram"].iloc[last]),
            "supertrend": float(st["supertrend"].iloc[last]),
            "supertrend_dir": int(st["direction"].iloc[last]),
            "adx": float(adx["adx"].iloc[last]),
            "plus_di": float(adx["plus_di"].iloc[last]),
            "minus_di": float(adx["minus_di"].iloc[last]),
            "atr": float(atr.iloc[last]),
            "vwap": float(vwap.iloc[last]) if not np.isnan(vwap.iloc[last]) else close,
            "bb_upper": float(bb["upper"].iloc[last]),
            "bb_middle": float(bb["middle"].iloc[last]),
            "bb_lower": float(bb["lower"].iloc[last]),
            "ema_9": float(ema9.iloc[last]),
            "ema_21": float(ema21.iloc[last]),
            "sma_50": float(sma50.iloc[last]),
            "pivots": self.pivot_points(),
            "fibonacci": self.fibonacci(),
            "obv": float(self.obv().iloc[last]),
            "volume_profile": self.volume_profile(),
        }
