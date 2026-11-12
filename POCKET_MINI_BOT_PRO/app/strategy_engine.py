"""
Pocket Signal Engine — The Six Filters Strategy.
Strict Conservative Multi-Confirmation Trading Strategy (5 of 6 filters required for execution).
"""
from typing import List, Dict, Any, Tuple
import numpy as np
from .candle_detector import Candle
from .indicators import TechnicalIndicators
from .config import FILTER_RULES, MARKET_OTC, MARKET_NORMAL


class StrategyEngine:
    """
    Evaluates market conditions against the 6 quantitative filters:
    1. Trend (EMA 9/21 with slope)
    2. RSI (Call: 50-68, Put: 32-50, no extremes)
    3. MACD (Histogram momentum confirmation)
    4. Candle Pattern (Confirmed closed reversal or continuation pattern)
    5. Support & Resistance (Clearance from ceiling/floor walls)
    6. Volatility / ATR (Stable range, no spikes or flat chop)
    """

    def __init__(self, market_type: str = MARKET_OTC):
        self.market_type = market_type

    def evaluate(self, candles: List[Candle], data_quality: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the 6-filter strategy and return:
        - direction: 'CALL', 'PUT', or 'WAIT'
        - technical_score: Integer percentage (0 - 100) representing rule agreement
        - filters_status: Dict of filter evaluations
        - explanation: Transparent reason for the decision
        """
        if len(candles) < 4 or not data_quality.get("is_reliable", False):
            return {
                "direction": "WAIT",
                "technical_score": 0,
                "filters_status": {},
                "filters_passed_count": 0,
                "reason": f"Calidad de datos insuficiente: {data_quality.get('reason', 'Pocas velas')}",
                "market_type": self.market_type,
                "indicator_values": {}
            }

        prices = [c.close for c in candles]
        c = candles[-1]
        prev = candles[-2]

        # Calculate Indicators
        ema9_series = TechnicalIndicators.calc_ema(prices, FILTER_RULES["ema_fast"])
        ema21_series = TechnicalIndicators.calc_ema(prices, FILTER_RULES["ema_slow"])
        ema50_series = TechnicalIndicators.calc_ema(prices, min(FILTER_RULES["ema_trend"], len(prices)))

        ema9 = ema9_series[-1]
        ema21 = ema21_series[-1]
        ema50 = ema50_series[-1]
        ema9_slope = ema9 - ema9_series[-2] if len(ema9_series) > 1 else 0.0

        rsi = TechnicalIndicators.calc_rsi(prices, FILTER_RULES["rsi_period"])
        macd_res = TechnicalIndicators.calc_macd(prices, FILTER_RULES["macd_fast"], FILTER_RULES["macd_slow"], FILTER_RULES["macd_signal"])
        bb_upper, bb_mid, bb_lower = TechnicalIndicators.calc_bollinger(prices, FILTER_RULES["bb_period"], FILTER_RULES["bb_std"])
        atr = TechnicalIndicators.calc_atr(candles, FILTER_RULES["atr_period"])

        pa = TechnicalIndicators.detect_price_action_patterns(candles)
        sr = TechnicalIndicators.detect_support_resistance(candles)

        # -------------------------------------------------------------
        # FILTER 1 — TREND
        # -------------------------------------------------------------
        bull_trend = (ema9 > ema21) and (ema9_slope >= 0.0)
        bear_trend = (ema9 < ema21) and (ema9_slope <= 0.0)
        f1_call = bull_trend
        f1_put = bear_trend
        f1_status = "Alcista" if bull_trend else "Bajista" if bear_trend else "Lateral"

        # -------------------------------------------------------------
        # FILTER 2 — RSI
        # -------------------------------------------------------------
        # CALL: RSI between 50 and 68. PUT: RSI between 32 and 50.
        f2_call = (rsi >= FILTER_RULES["rsi_call_min"]) and (rsi <= FILTER_RULES["rsi_call_max"])
        f2_put = (rsi >= FILTER_RULES["rsi_put_min"]) and (rsi <= FILTER_RULES["rsi_put_max"])
        f2_status = f"RSI {rsi}"

        # -------------------------------------------------------------
        # FILTER 3 — MACD
        # -------------------------------------------------------------
        # CALL: positive and strengthening histogram.
        # PUT: negative and weakening histogram (or negative and expanding downward).
        hist = macd_res["hist"]
        hist_prev = macd_res["hist_prev"]
        f3_call = (hist > 0.0) and (hist >= hist_prev)
        f3_put = (hist < 0.0) and (hist <= hist_prev)
        f3_status = f"Hist {hist:.2f}"

        # -------------------------------------------------------------
        # FILTER 4 — CANDLE PATTERN
        # -------------------------------------------------------------
        # Confirmed closed reversal or momentum continuation pattern
        f4_call = pa["is_confirmed"] and (pa["bias"] == "CALL")
        f4_put = pa["is_confirmed"] and (pa["bias"] == "PUT")
        f4_status = pa["pattern"]

        # -------------------------------------------------------------
        # FILTER 5 — SUPPORT AND RESISTANCE
        # -------------------------------------------------------------
        # Avoid CALL immediately below strong resistance.
        # Avoid PUT immediately above strong support.
        f5_call = not sr["is_near_resistance"]
        f5_put = not sr["is_near_support"]
        f5_status = f"Techo: {sr['dist_to_res_pct']}% | Piso: {sr['dist_to_sup_pct']}%"

        # -------------------------------------------------------------
        # FILTER 6 — VOLATILITY (ATR & SPIKE SHIELD)
        # -------------------------------------------------------------
        rng = max(1.0, c.range_size)
        lw_ratio = c.lower_wick / rng
        uw_ratio = c.upper_wick / rng
        is_spike = (uw_ratio >= 0.68 or lw_ratio >= 0.68) and c.body_size < 3.5
        is_flat = c.body_size < 2.0 or rng < 3.0

        stable_volatility = (not is_spike) and (not is_flat) and (atr >= 1.2)
        f6_call = stable_volatility
        f6_put = stable_volatility
        f6_status = f"ATR {atr} (Estable)" if stable_volatility else "Volatilidad Anómala"

        # =============================================================
        # CONVERGENCE TALLY (5 of 6 required)
        # =============================================================
        call_score = sum([f1_call, f2_call, f3_call, f4_call, f5_call, f6_call])
        put_score = sum([f1_put, f2_put, f3_put, f4_put, f5_put, f6_put])

        filters_detail = {
            "f1_trend": {"call": f1_call, "put": f1_put, "status": f1_status},
            "f2_rsi": {"call": f2_call, "put": f2_put, "status": f2_status},
            "f3_macd": {"call": f3_call, "put": f3_put, "status": f3_status},
            "f4_candle": {"call": f4_call, "put": f4_put, "status": f4_status},
            "f5_sr": {"call": f5_call, "put": f5_put, "status": f5_status},
            "f6_volatility": {"call": f6_call, "put": f6_put, "status": f6_status}
        }

        min_req = FILTER_RULES["min_required_filters"]  # 5
        direction = "WAIT"
        technical_score = 0
        filters_passed_count = 0
        reason = ""

        if call_score >= min_req:
            direction = "CALL"
            filters_passed_count = call_score
            technical_score = int((call_score / 6.0) * 100.0)
            reason = f"Confluencia Alcista confirmada ({call_score}/6 filtros). {pa['pattern']} + Tendencia {f1_status}."
        elif put_score >= min_req:
            direction = "PUT"
            filters_passed_count = put_score
            technical_score = int((put_score / 6.0) * 100.0)
            reason = f"Confluencia Bajista confirmada ({put_score}/6 filtros). {pa['pattern']} + Tendencia {f1_status}."
        else:
            direction = "WAIT"
            max_score = max(call_score, put_score)
            filters_passed_count = max_score
            technical_score = int((max_score / 6.0) * 100.0)

            # Detail the primary blocker
            blockers = []
            if not f6_call:
                blockers.append("Volatilidad inestable o spike OTC")
            if sr["is_near_resistance"] and call_score > put_score:
                blockers.append("Precio rozando techo de resistencia")
            if sr["is_near_support"] and put_score > call_score:
                blockers.append("Precio rozando piso de soporte")
            if not (f1_call or f1_put):
                blockers.append("Medias móviles entrelazadas (mercado lateral)")
            if not (f4_call or f4_put):
                blockers.append("Sin patrón de velas confirmado")

            block_str = "; ".join(blockers) if blockers else "Filtros insuficientes (se requieren al menos 5 de 6)"
            reason = f"Esperando confluencia ({max_score}/6 filtros). {block_str}."

        indicator_values = {
            "ema9": round(ema9, 2),
            "ema21": round(ema21, 2),
            "ema50": round(ema50, 2),
            "rsi": rsi,
            "macd": macd_res["macd"],
            "macd_signal": macd_res["signal"],
            "macd_hist": macd_res["hist"],
            "atr": atr,
            "bb_upper": round(bb_upper, 2),
            "bb_lower": round(bb_lower, 2),
            "pattern": pa["pattern"],
            "dist_to_res_pct": sr["dist_to_res_pct"],
            "dist_to_sup_pct": sr["dist_to_sup_pct"]
        }

        # Apply data quality confidence multiplier
        conf_multiplier = data_quality.get("confidence_multiplier", 1.0)
        adjusted_score = int(technical_score * conf_multiplier)

        return {
            "direction": direction,
            "technical_score": adjusted_score,
            "filters_status": filters_detail,
            "filters_passed_count": filters_passed_count,
            "reason": reason,
            "market_type": self.market_type,
            "indicator_values": indicator_values
        }
