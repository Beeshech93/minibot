"""
Technical Indicators and Quantitative Price Action Engine.
Pure, high-performance NumPy implementation of EMA, RSI, MACD, Bollinger Bands, ATR,
Support/Resistance, and Candlestick Price Action Patterns.
"""
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from .candle_detector import Candle


class TechnicalIndicators:
    """Computes all required technical indicators from reconstructed candle objects."""

    @staticmethod
    def calc_ema(series: List[float], period: int) -> List[float]:
        """Exponential Moving Average (EMA)."""
        if not series:
            return []
        k = 2.0 / (period + 1.0)
        ema = [series[0]]
        for val in series[1:]:
            ema.append(val * k + ema[-1] * (1.0 - k))
        return ema

    @staticmethod
    def calc_rsi(prices: List[float], period: int = 14) -> float:
        """Wilder's Smoothed Relative Strength Index (RSI)."""
        if len(prices) < 2:
            return 50.0
        deltas = np.diff(prices)
        gains = np.maximum(deltas, 0.0)
        losses = np.maximum(-deltas, 0.0)

        if len(deltas) < period:
            avg_gain = float(np.mean(gains)) if len(gains) > 0 else 0.0
            avg_loss = float(np.mean(losses)) if len(losses) > 0 else 0.0
        else:
            avg_gain = float(np.mean(gains[:period]))
            avg_loss = float(np.mean(losses[:period]))
            for g, l in zip(gains[period:], losses[period:]):
                avg_gain = (avg_gain * (period - 1) + g) / period
                avg_loss = (avg_loss * (period - 1) + l) / period

        if avg_loss == 0.0:
            return 100.0 if avg_gain > 0.0 else 50.0
        rs = avg_gain / avg_loss
        return round(float(100.0 - (100.0 / (1.0 + rs))), 1)

    @staticmethod
    def calc_macd(
        prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9
    ) -> Dict[str, float]:
        """Moving Average Convergence Divergence (MACD)."""
        if len(prices) < 3:
            return {"macd": 0.0, "signal": 0.0, "hist": 0.0, "hist_prev": 0.0, "strengthening": False}

        ema_fast = TechnicalIndicators.calc_ema(prices, fast)
        ema_slow = TechnicalIndicators.calc_ema(prices, slow)
        macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
        signal_line = TechnicalIndicators.calc_ema(macd_line, signal)

        hist = [m - s for m, s in zip(macd_line, signal_line)]
        curr_hist = hist[-1]
        prev_hist = hist[-2] if len(hist) > 1 else 0.0
        strengthening = abs(curr_hist) >= abs(prev_hist)

        return {
            "macd": round(macd_line[-1], 2),
            "signal": round(signal_line[-1], 2),
            "hist": round(curr_hist, 2),
            "hist_prev": round(prev_hist, 2),
            "strengthening": strengthening
        }

    @staticmethod
    def calc_bollinger(prices: List[float], period: int = 20, num_std: float = 2.0) -> Tuple[float, float, float]:
        """Bollinger Bands (Upper, Middle, Lower)."""
        p_sub = prices[-period:] if len(prices) >= period else prices
        mid = float(np.mean(p_sub))
        std = float(np.std(p_sub)) if len(p_sub) > 1 else 1.0
        upper = mid + num_std * std
        lower = mid - num_std * std
        return upper, mid, lower

    @staticmethod
    def calc_atr(candles: List[Candle], period: int = 14) -> float:
        """Average True Range (ATR)."""
        if len(candles) < 2:
            return 1.0
        trs = []
        for i in range(1, len(candles)):
            c_curr = candles[i]
            c_prev = candles[i - 1]
            tr = max(
                c_curr.high - c_curr.low,
                abs(c_curr.high - c_prev.close),
                abs(c_curr.low - c_prev.close)
            )
            trs.append(tr)
        sub = trs[-period:] if len(trs) >= period else trs
        return round(float(np.mean(sub)), 2)

    @staticmethod
    def detect_price_action_patterns(candles: List[Candle]) -> Dict[str, Any]:
        """
        Detect confirmed candlestick patterns:
        - Bullish / Bearish Engulfing
        - Hammer / Shooting Star / Pin Bar
        - Strong Bullish / Bearish Candle (Marubozu)
        """
        if len(candles) < 2:
            return {"pattern": "Ninguno", "bias": "NEUTRO", "is_confirmed": False}

        c = candles[-1]
        prev = candles[-2]
        rng = max(1.0, c.range_size)
        lw_ratio = c.lower_wick / rng
        uw_ratio = c.upper_wick / rng
        body_ratio = c.body_size / rng

        # 1. Hammer (Martillo alcista)
        if lw_ratio >= 0.48 and body_ratio <= 0.38 and uw_ratio <= 0.18:
            return {"pattern": "Hammer (Martillo Alcista)", "bias": "CALL", "is_confirmed": True}

        # 2. Shooting Star (Estrella fugaz bajista)
        if uw_ratio >= 0.48 and body_ratio <= 0.38 and lw_ratio <= 0.18:
            return {"pattern": "Shooting Star (Estrella Fugaz)", "bias": "PUT", "is_confirmed": True}

        # 3. Pin Bar
        if (lw_ratio >= 0.50 or uw_ratio >= 0.50) and body_ratio <= 0.35:
            bias = "CALL" if lw_ratio > uw_ratio else "PUT"
            return {"pattern": f"Pin Bar ({'Alcista' if bias == 'CALL' else 'Bajista'})", "bias": bias, "is_confirmed": True}

        # 4. Bullish Engulfing (Envolvente Alcista)
        if prev.color == -1 and c.color == 1 and c.close >= prev.open and c.body_size > prev.body_size * 1.10:
            return {"pattern": "Bullish Engulfing (Envolvente Alcista)", "bias": "CALL", "is_confirmed": True}

        # 5. Bearish Engulfing (Envolvente Bajista)
        if prev.color == 1 and c.color == -1 and c.close <= prev.open and c.body_size > prev.body_size * 1.10:
            return {"pattern": "Bearish Engulfing (Envolvente Bajista)", "bias": "PUT", "is_confirmed": True}

        # 6. Strong Bullish Candle (Marubozu)
        if c.color == 1 and prev.color == 1 and body_ratio >= 0.65 and uw_ratio <= 0.15:
            return {"pattern": "Marubozu Alcista (Impulso)", "bias": "CALL", "is_confirmed": True}

        # 7. Strong Bearish Candle (Marubozu)
        if c.color == -1 and prev.color == -1 and body_ratio >= 0.65 and lw_ratio <= 0.15:
            return {"pattern": "Marubozu Bajista (Impulso)", "bias": "PUT", "is_confirmed": True}

        return {"pattern": "Vela Normal", "bias": "NEUTRO", "is_confirmed": False}

    @staticmethod
    def detect_support_resistance(candles: List[Candle]) -> Dict[str, Any]:
        """
        Locate local swing highs, swing lows, and measure distance to boundary walls.
        """
        if len(candles) < 3:
            return {
                "resistance": 0.0, "support": 0.0,
                "dist_to_res_pct": 50.0, "dist_to_sup_pct": 50.0,
                "is_near_resistance": False, "is_near_support": False
            }

        highs = [cd.high for cd in candles]
        lows = [cd.low for cd in candles]
        curr_price = candles[-1].close

        res = max(highs)
        sup = min(lows)
        total_rng = max(1.0, res - sup)

        dist_to_res = (res - curr_price) / total_rng
        dist_to_sup = (curr_price - sup) / total_rng

        return {
            "resistance": round(res, 2),
            "support": round(sup, 2),
            "dist_to_res_pct": round(dist_to_res * 100.0, 1),
            "dist_to_sup_pct": round(dist_to_sup * 100.0, 1),
            "is_near_resistance": dist_to_res < 0.04,  # Within 4% of ceiling
            "is_near_support": dist_to_sup < 0.04      # Within 4% of floor
        }

