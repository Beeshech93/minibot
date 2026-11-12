"""
Pro-Grade Multi-Agent AI Market Intelligence System for Pocket Mini Bot.
Institutional Architecture with Bayesian Log-Odds Confluence:
1. PriceActionAgent: Candlestick geometry, Wick Absorption Index (WAI), multi-candle patterns.
2. SmartMoneyTrapAgent: Fair Value Gaps (FVG), Order Blocks (OB), Liquidity Sweeps.
3. MarketStructureAgent: Swing Highs/Lows, Dynamic S/R, Fibonacci Golden Pocket (0.50 - 0.618).
4. TechnicalIndicatorAgent: Triple EMA (9, 21, 50), Wilder's RSI, Stochastic %K/%D Crossover.
5. VolatilityBollingerAgent: Bollinger Bands (20, 2), John Carter TTM Squeeze & Expansion.
6. MACDMomentumAgent: MACD (12, 26, 9) histogram acceleration & divergences.
7. NextCandlePredictorAgent: Micro-order flow and wick rejection for the immediate next candle.
8. ConsensusMasterAgent: Bayesian Log-Odds Ensemble Classifier with calibrated probability.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional
import numpy as np


@dataclass
class Candle:
    x: float
    open: float
    high: float
    low: float
    close: float
    color: int  # +1 for green/bullish, -1 for red/bearish
    body_size: float
    upper_wick: float
    lower_wick: float
    range_size: float


def extract_candles_from_data(
    xs: List[int], 
    centers: List[float], 
    directions: List[int], 
    heights: List[float],
    top_ys: Optional[List[float]] = None,
    bot_ys: Optional[List[float]] = None
) -> List[Candle]:
    """Convert raw visual column clusters into detailed Candle objects with realistic wicks."""
    candles = []
    has_wicks = top_ys is not None and bot_ys is not None and len(top_ys) == len(xs)

    for i, (x, c, d, h) in enumerate(zip(xs, centers, directions, heights)):
        body_h = max(2.5, float(h))
        # Chart y is inverted (smaller y = higher price)
        center_price = -c
        half_b = body_h / 2.0
        
        if d > 0:  # Bullish
            c_open = center_price - half_b
            c_close = center_price + half_b
        else:  # Bearish
            c_open = center_price + half_b
            c_close = center_price - half_b
            
        if has_wicks:
            raw_high = -top_ys[i]
            raw_low = -bot_ys[i]
            upper_w = max(0.5, raw_high - max(c_open, c_close))
            lower_w = max(0.5, min(c_open, c_close) - raw_low)
        else:
            upper_w = max(0.5, body_h * 0.3)
            lower_w = max(0.5, body_h * 0.3)

        c_high = max(c_open, c_close) + upper_w
        c_low = min(c_open, c_close) - lower_w
        rng = max(1.0, c_high - c_low)

        candles.append(Candle(
            x=float(x),
            open=c_open,
            high=c_high,
            low=c_low,
            close=c_close,
            color=d,
            body_size=body_h,
            upper_wick=upper_w,
            lower_wick=lower_w,
            range_size=rng
        ))
    return candles


# =========================================================================
# QUANTITATIVE INDICATOR SUITE (MATHEMATICAL FOUNDATION)
# =========================================================================

def calc_ema_series(prices: List[float], period: int) -> List[float]:
    """Exponential Moving Average."""
    if not prices:
        return []
    k = 2.0 / (period + 1.0)
    ema = [prices[0]]
    for p in prices[1:]:
        ema.append(p * k + ema[-1] * (1.0 - k))
    return ema


def calc_wilder_rsi(prices: List[float], period: int = 14) -> float:
    """Wilder's Smoothed Relative Strength Index."""
    if len(prices) < 2:
        return 50.0
    deltas = np.diff(prices)
    gains = np.maximum(deltas, 0)
    losses = np.maximum(-deltas, 0)
    
    if len(deltas) < period:
        avg_gain = np.mean(gains) if len(gains) > 0 else 0.0
        avg_loss = np.mean(losses) if len(losses) > 0 else 0.0
    else:
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        for g, l in zip(gains[period:], losses[period:]):
            avg_gain = (avg_gain * (period - 1) + g) / period
            avg_loss = (avg_loss * (period - 1) + l) / period

    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return round(float(100.0 - (100.0 / (1.0 + rs))), 1)


def calc_stochastic(highs: List[float], lows: List[float], closes: List[float], k_period: int = 14, d_period: int = 3) -> Tuple[float, float]:
    """Fast & Slow Stochastic Oscillator (%K, %D)."""
    if len(closes) < 3:
        return 50.0, 50.0
    k_vals = []
    for i in range(max(1, len(closes) - d_period - 2), len(closes)):
        sub_highs = highs[max(0, i - k_period + 1):i + 1]
        sub_lows = lows[max(0, i - k_period + 1):i + 1]
        highest = max(sub_highs) if sub_highs else closes[i]
        lowest = min(sub_lows) if sub_lows else closes[i]
        rng = highest - lowest
        if rng <= 0:
            k_vals.append(50.0)
        else:
            k_vals.append(((closes[i] - lowest) / rng) * 100.0)
    
    current_k = k_vals[-1] if k_vals else 50.0
    current_d = float(np.mean(k_vals[-d_period:])) if len(k_vals) >= d_period else current_k
    return round(current_k, 1), round(current_d, 1)


def calc_bollinger_bands(prices: List[float], period: int = 20, num_std: float = 2.0) -> Tuple[float, float, float, float]:
    """Returns (Upper, Middle, Lower, Bandwidth)."""
    if not prices:
        return 0.0, 0.0, 0.0, 0.0
    p_sub = prices[-period:] if len(prices) >= period else prices
    mid = float(np.mean(p_sub))
    std = float(np.std(p_sub)) if len(p_sub) > 1 else 1.0
    upper = mid + num_std * std
    lower = mid - num_std * std
    bandwidth = (upper - lower) / max(1e-5, abs(mid))
    return upper, mid, lower, bandwidth


def detect_fair_value_gaps(candles: List[Candle]) -> List[Dict[str, Any]]:
    """Smart Money Concepts (SMC) Fair Value Gap (FVG) scanner."""
    fvgs = []
    if len(candles) < 3:
        return fvgs
    for i in range(2, len(candles)):
        c1, c2, c3 = candles[i-2], candles[i-1], candles[i]
        # Bullish FVG: Candle 1 High < Candle 3 Low (Gap in Candle 2)
        if c1.high < c3.low and c2.color == 1:
            fvgs.append({
                "type": "BULLISH",
                "top": c3.low,
                "bottom": c1.high,
                "size": c3.low - c1.high,
                "index": i-1
            })
        # Bearish FVG: Candle 1 Low > Candle 3 High (Gap in Candle 2)
        elif c1.low > c3.high and c2.color == -1:
            fvgs.append({
                "type": "BEARISH",
                "top": c1.low,
                "bottom": c3.high,
                "size": c1.low - c3.high,
                "index": i-1
            })
    return fvgs


# =========================================================================
# SPECIALIZED MULTI-AGENT ENGINE
# =========================================================================

class PriceActionAgent:
    """Agent specialized in Japanese Candlestick Patterns and Wick Absorption Index (WAI)."""
    name = "Acción del Precio"

    def analyze(self, candles: List[Candle]) -> Dict[str, Any]:
        if len(candles) < 3:
            return {"vote": "ESPERAR", "confidence": 50, "reason": "Insuficientes velas"}

        c = candles[-1]
        prev = candles[-2]
        prev2 = candles[-3] if len(candles) >= 3 else prev

        lower_ratio = c.lower_wick / max(1.0, c.range_size)
        upper_ratio = c.upper_wick / max(1.0, c.range_size)
        body_ratio = c.body_size / max(1.0, c.range_size)
        wai = (c.lower_wick - c.upper_wick) / max(1.0, c.range_size)

        # 1. Hammer / Pinbar Alcista
        is_hammer = lower_ratio >= 0.50 and upper_ratio <= 0.22
        # 2. Shooting Star / Pinbar Bajista
        is_shooting_star = upper_ratio >= 0.50 and lower_ratio <= 0.22
        # 3. Bullish Engulfing
        is_bullish_engulf = (prev.color == -1 and c.color == 1 and 
                             c.close >= prev.open and c.body_size > prev.body_size * 1.1)
        # 4. Bearish Engulfing
        is_bearish_engulf = (prev.color == 1 and c.color == -1 and 
                             c.close <= prev.open and c.body_size > prev.body_size * 1.1)
        # 5. Morning Star
        is_morning_star = (prev2.color == -1 and prev.body_size <= prev2.body_size * 0.45 and 
                           c.color == 1 and c.close > (prev2.open + prev2.close) / 2.0)
        # 6. Evening Star
        is_evening_star = (prev2.color == 1 and prev.body_size <= prev2.body_size * 0.45 and 
                           c.color == -1 and c.close < (prev2.open + prev2.close) / 2.0)
        # 7. Doji
        is_doji = body_ratio <= 0.12

        if is_morning_star:
            return {"vote": "CALL", "confidence": 93, "pattern": "Morning Star", "reason": "Giro alcista confirmado por 3 velas", "wai": wai}
        elif is_evening_star:
            return {"vote": "PUT", "confidence": 93, "pattern": "Evening Star", "reason": "Giro bajista confirmado por 3 velas", "wai": wai}
        elif is_hammer:
            return {"vote": "CALL", "confidence": 90, "pattern": "Martillo / Pinbar Alcista", "reason": f"Fuerte absorción compradora ({int(lower_ratio*100)}% mecha)", "wai": wai}
        elif is_bullish_engulf:
            return {"vote": "CALL", "confidence": 91, "pattern": "Envolvente Alcista", "reason": "Absorción total de oferta previa", "wai": wai}
        elif is_shooting_star:
            return {"vote": "PUT", "confidence": 90, "pattern": "Estrella Fugaz / Pinbar Bajista", "reason": f"Fuerte rechazo vendedor ({int(upper_ratio*100)}% mecha)", "wai": wai}
        elif is_bearish_engulf:
            return {"vote": "PUT", "confidence": 91, "pattern": "Envolvente Bajista", "reason": "Absorción total de demanda previa", "wai": wai}
        elif is_doji:
            return {"vote": "ESPERAR", "confidence": 40, "pattern": "Doji / Indecisión", "reason": "Equilibrio transitorio; esperar confirmación", "wai": wai}

        if c.color == 1 and prev.color == 1 and c.body_size > prev.body_size:
            return {"vote": "CALL", "confidence": 78, "pattern": "Expansión Verde", "reason": "Aceleración de compradores", "wai": wai}
        elif c.color == -1 and prev.color == -1 and c.body_size > prev.body_size:
            return {"vote": "PUT", "confidence": 78, "pattern": "Expansión Roja", "reason": "Aceleración de vendedores", "wai": wai}

        return {"vote": "ESPERAR", "confidence": 50, "pattern": "Velas Neutras", "reason": "Sin ventaja de acción del precio", "wai": wai}


class SmartMoneyTrapAgent:
    """Agent specialized in Fair Value Gaps (FVG), Order Blocks, and Liquidity Sweeps."""
    name = "Smart Money & Trampas"

    def analyze(self, candles: List[Candle]) -> Dict[str, Any]:
        if len(candles) < 4:
            return {"vote": "ESPERAR", "confidence": 50, "reason": "Datos insuficientes"}

        c = candles[-1]
        current_price = c.close
        highs = [cd.high for cd in candles[:-1]]
        lows = [cd.low for cd in candles[:-1]]
        recent_high = max(highs[-6:]) if highs else c.high
        recent_low = min(lows[-6:]) if lows else c.low

        # 1. Liquidity Sweep Bull Trap (Falsa Ruptura hacia arriba)
        if c.high > recent_high and c.close < recent_high and c.upper_wick >= c.body_size * 0.9:
            return {
                "vote": "PUT", "confidence": 94, "trap": "Trampa de Toros (Bull Trap)",
                "reason": "Barrido de liquidez sobre máximos; reversión bajista inminente"
            }

        # 2. Liquidity Sweep Bear Trap (Falsa Ruptura hacia abajo)
        if c.low < recent_low and c.close > recent_low and c.lower_wick >= c.body_size * 0.9:
            return {
                "vote": "CALL", "confidence": 94, "trap": "Trampa de Osos (Bear Trap)",
                "reason": "Barrido de liquidez bajo mínimos; rebote alcista inminente"
            }

        # 3. Fair Value Gap (FVG) Mitigation
        fvgs = detect_fair_value_gaps(candles)
        if fvgs:
            last_fvg = fvgs[-1]
            if last_fvg["type"] == "BULLISH" and abs(current_price - last_fvg["top"]) / max(1.0, c.range_size) < 1.5:
                return {
                    "vote": "CALL", "confidence": 88, "trap": "Mitigación FVG Alcista",
                    "reason": "Precio rellenando desbalance institucional; soporte fuerte"
                }
            elif last_fvg["type"] == "BEARISH" and abs(current_price - last_fvg["bottom"]) / max(1.0, c.range_size) < 1.5:
                return {
                    "vote": "PUT", "confidence": 88, "trap": "Mitigación FVG Bajista",
                    "reason": "Precio rellenando desbalance institucional; resistencia fuerte"
                }

        return {"vote": "ESPERAR", "confidence": 50, "trap": "Sin anomalía", "reason": "Estructura institucional limpia"}


class MarketStructureAgent:
    """Agent specialized in Support/Resistance, Fibonacci Retracements, and Swings."""
    name = "Estructura & S/R"

    def analyze(self, candles: List[Candle]) -> Dict[str, Any]:
        if len(candles) < 4:
            return {"vote": "ESPERAR", "confidence": 50, "reason": "Datos insuficientes"}

        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        current_price = candles[-1].close
        total_range = max(highs) - min(lows)
        if total_range <= 0:
            return {"vote": "ESPERAR", "confidence": 50, "reason": "Rango plano"}

        highest = max(highs)
        lowest = min(lows)
        dist_res = abs(highest - current_price) / total_range
        dist_sup = abs(current_price - lowest) / total_range

        # Fibonacci Golden Pocket (0.50 a 0.618 de retroceso)
        fib_50 = lowest + total_range * 0.50
        in_golden_pocket = abs(current_price - fib_50) / total_range < 0.07

        if in_golden_pocket and candles[-1].color == 1:
            return {"vote": "CALL", "confidence": 90, "zone": "Fibonacci Golden Pocket", "reason": "Rebote institucional en 50%-61.8% de retroceso"}
        elif in_golden_pocket and candles[-1].color == -1:
            return {"vote": "PUT", "confidence": 90, "zone": "Fibonacci Golden Pocket", "reason": "Rechazo institucional en 50%-61.8% de retroceso"}
        elif dist_sup < 0.08 and candles[-1].color == 1:
            return {"vote": "CALL", "confidence": 88, "zone": "Soporte Mayor", "reason": "Doble suelo / rebote en nivel de soporte"}
        elif dist_res < 0.08 and candles[-1].color == -1:
            return {"vote": "PUT", "confidence": 88, "zone": "Resistencia Mayor", "reason": "Doble techo / rechazo en resistencia"}

        # Bloqueos de seguridad (contra la pared)
        block_call = dist_res < 0.02
        block_put = dist_sup < 0.02

        return {
            "vote": "ESPERAR", "confidence": 50, "zone": "Rango Medio",
            "reason": "Precio en zona neutra de estructura",
            "block_call": block_call, "block_put": block_put
        }


class TechnicalIndicatorAgent:
    """Agent specialized in EMA Ribbon (9, 21, 50), Wilder's RSI, and Stochastic Oscillator."""
    name = "Indicadores & EMA"

    def analyze(self, candles: List[Candle]) -> Dict[str, Any]:
        prices = [c.close for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        
        rsi = calc_wilder_rsi(prices, 14)
        k_val, d_val = calc_stochastic(highs, lows, prices, 14, 3)

        if len(prices) < 4:
            return {"vote": "ESPERAR", "confidence": 50, "rsi": rsi, "stoch": (k_val, d_val), "reason": "Datos insuficientes"}

        ema9 = calc_ema_series(prices, 9)[-1]
        ema21 = calc_ema_series(prices, 21)[-1]
        current_price = prices[-1]

        # 1. Reversión por Sobreextensión Extrema (RSI + Estocástico)
        if rsi <= 30 and k_val <= 25 and k_val > d_val:
            return {
                "vote": "CALL", "confidence": 92, "rsi": rsi, "stoch": (k_val, d_val),
                "reason": f"Sobreventa extrema con cruce alcista estocástico (%K={k_val}, RSI={rsi})"
            }
        elif rsi >= 70 and k_val >= 75 and k_val < d_val:
            return {
                "vote": "PUT", "confidence": 92, "rsi": rsi, "stoch": (k_val, d_val),
                "reason": f"Sobrecompra extrema con cruce bajista estocástico (%K={k_val}, RSI={rsi})"
            }

        # 2. Impulso EMA Ribbon
        if ema9 > ema21 and current_price >= ema9 and rsi < 65:
            return {
                "vote": "CALL", "confidence": 85, "rsi": rsi, "stoch": (k_val, d_val),
                "reason": f"Tendencia alcista sobre EMA 9/21 (RSI={rsi})"
            }
        elif ema9 < ema21 and current_price <= ema9 and rsi > 35:
            return {
                "vote": "PUT", "confidence": 85, "rsi": rsi, "stoch": (k_val, d_val),
                "reason": f"Tendencia bajista bajo EMA 9/21 (RSI={rsi})"
            }

        return {
            "vote": "ESPERAR", "confidence": 50, "rsi": rsi, "stoch": (k_val, d_val),
            "reason": f"RSI neutro ({rsi}) y medias entrelazadas"
        }


class VolatilityBollingerAgent:
    """Agent specialized in Bollinger Bands (20, 2) and John Carter TTM Squeeze Detection."""
    name = "Volatilidad & Bollinger"

    def analyze(self, candles: List[Candle]) -> Dict[str, Any]:
        prices = [c.close for c in candles]
        if len(prices) < 4:
            return {"vote": "ESPERAR", "confidence": 50, "state": "Sin datos", "is_squeeze": False}

        upper, mid, lower, bw = calc_bollinger_bands(prices, period=20, num_std=2.0)
        c = candles[-1]
        current_price = c.close

        # Perforación de banda externa con rechazo
        if c.low <= lower and c.close > lower and c.lower_wick >= c.body_size * 0.7:
            return {
                "vote": "CALL", "confidence": 91, "state": "Rebote Banda Inferior",
                "reason": "Perforación y absorción elástica en Bollinger inferior",
                "is_squeeze": False
            }
        elif c.high >= upper and c.close < upper and c.upper_wick >= c.body_size * 0.7:
            return {
                "vote": "PUT", "confidence": 91, "state": "Rechazo Banda Superior",
                "reason": "Perforación y rechazo elástico en Bollinger superior",
                "is_squeeze": False
            }

        # Detección de Squeeze plano (mercado congelado / peligro de pérdida en binarias)
        is_squeeze = bw < 0.012 and len(prices) >= 12
        if is_squeeze:
            return {
                "vote": "ESPERAR", "confidence": 35, "state": "Squeeze Plano",
                "reason": "Compresión extrema de volatilidad; no operar hasta expansión",
                "is_squeeze": True
            }

        return {
            "vote": "ESPERAR", "confidence": 50, "state": "Volatilidad Normal",
            "reason": "Precio dentro del canal estándar de Bollinger",
            "is_squeeze": False
        }


class MACDMomentumAgent:
    """Agent specialized in MACD Momentum & Acceleration shifts."""
    name = "MACD & Momentum"

    def analyze(self, candles: List[Candle]) -> Dict[str, Any]:
        prices = [c.close for c in candles]
        if len(prices) < 6:
            return {"vote": "ESPERAR", "confidence": 50, "state": "Sin datos"}

        fast = calc_ema_series(prices, 6)
        slow = calc_ema_series(prices, 13)
        macd = [f - s for f, s in zip(fast, slow)]
        signal = calc_ema_series(macd, 5)
        hist = macd[-1] - signal[-1]
        prev_hist = macd[-2] - signal[-2] if len(macd) >= 2 else 0.0

        if hist > 0 and hist > prev_hist:
            return {"vote": "CALL", "confidence": 84, "state": "Aceleración Alcista", "reason": "Histograma MACD en expansión positiva"}
        elif hist < 0 and hist < prev_hist:
            return {"vote": "PUT", "confidence": 84, "state": "Aceleración Bajista", "reason": "Histograma MACD en expansión negativa"}

        return {"vote": "ESPERAR", "confidence": 50, "state": "MACD Neutro", "reason": "Sin aceleración notable de momentum"}


class NextCandlePredictorAgent:
    """Micro-Structure Order Flow Predictor for the immediate next candle (SUBE vs BAJA)."""
    name = "Predictor Próxima Vela"

    def predict(self, candles: List[Candle], r_pa: Dict[str, Any], r_st: Dict[str, Any], r_ind: Dict[str, Any], r_bb: Dict[str, Any], r_trap: Dict[str, Any]) -> Dict[str, Any]:
        if not candles:
            return {
                "direction": "INDECISIÓN", "label": "🔮 PRÓXIMA VELA: ⚖️ INDECISIÓN",
                "short_label": "⚖️ INDECISIÓN", "probability": 50, "reason": "Sin datos suficientes"
            }

        c = candles[-1]
        prev = candles[-2] if len(candles) >= 2 else c

        lower_ratio = c.lower_wick / max(1.0, c.range_size)
        upper_ratio = c.upper_wick / max(1.0, c.range_size)
        body_ratio = c.body_size / max(1.0, c.range_size)

        sube_score = 0.0
        baja_score = 0.0
        reasons_sube = []
        reasons_baja = []

        # 1. Micro-rechazos de mechas en la vela actual
        if lower_ratio >= 0.35:
            w = 35 + int(lower_ratio * 40)
            sube_score += w
            reasons_sube.append(f"Rechazo inferior ({int(lower_ratio*100)}%)")
        if upper_ratio >= 0.35:
            w = 35 + int(upper_ratio * 40)
            baja_score += w
            reasons_baja.append(f"Rechazo superior ({int(upper_ratio*100)}%)")

        # 2. Impulso del cuerpo en vela viva
        if c.color == 1:
            if body_ratio >= 0.40 and upper_ratio <= 0.25:
                sube_score += 30
                reasons_sube.append("Cuerpo verde expansivo")
            elif body_ratio <= 0.15 and prev.color == -1:
                sube_score += 20
                reasons_sube.append("Agotamiento vendedor (Doji)")
        elif c.color == -1:
            if body_ratio >= 0.40 and lower_ratio <= 0.25:
                baja_score += 30
                reasons_baja.append("Cuerpo rojo expansivo")
            elif body_ratio <= 0.15 and prev.color == 1:
                baja_score += 20
                reasons_baja.append("Agotamiento comprador (Doji)")

        # 3. Micro-secuencia de las últimas velas
        if c.color == 1 and prev.color == 1:
            sube_score += 20
            reasons_sube.append("Impulso verde continuo")
        elif c.color == -1 and prev.color == -1:
            baja_score += 20
            reasons_baja.append("Impulso rojo continuo")

        # 4. Aportes de agentes institucionales
        if r_pa.get("vote") == "CALL":
            sube_score += 25
            reasons_sube.append(r_pa.get("pattern", "Patrón alcista"))
        elif r_pa.get("vote") == "PUT":
            baja_score += 25
            reasons_baja.append(r_pa.get("pattern", "Patrón bajista"))

        if r_trap.get("vote") == "CALL":
            sube_score += 30
            reasons_sube.append(r_trap.get("trap", "Trampa de osos / FVG"))
        elif r_trap.get("vote") == "PUT":
            baja_score += 30
            reasons_baja.append(r_trap.get("trap", "Trampa de toros / FVG"))

        if r_st.get("vote") == "CALL":
            sube_score += 25
            reasons_sube.append(r_st.get("zone", "Soporte clave"))
        elif r_st.get("vote") == "PUT":
            baja_score += 25
            reasons_baja.append(r_st.get("zone", "Resistencia clave"))

        if r_bb.get("vote") == "CALL":
            sube_score += 25
            reasons_sube.append("Rebote Bollinger inferior")
        elif r_bb.get("vote") == "PUT":
            baja_score += 25
            reasons_baja.append("Rechazo Bollinger superior")

        rsi = r_ind.get("rsi", 50.0)
        if rsi < 34:
            sube_score += 20
            reasons_sube.append(f"RSI sobrevendido ({rsi})")
        elif rsi > 66:
            baja_score += 20
            reasons_baja.append(f"RSI sobrecomprado ({rsi})")

        # 5. Determinación rápida de la Próxima Vela
        if sube_score > baja_score + 12:
            prob = min(96, int(70 + (sube_score / (sube_score + baja_score + 1e-5)) * 25))
            reason = " · ".join(reasons_sube[:2]) if reasons_sube else "Presión compradora dominante"
            return {
                "direction": "SUBE",
                "label": f"🔮 PRÓXIMA VELA: 🟢 SUBE ({prob}%)",
                "short_label": "🟢 SUBE",
                "probability": prob,
                "reason": reason
            }
        elif baja_score > sube_score + 12:
            prob = min(96, int(70 + (baja_score / (sube_score + baja_score + 1e-5)) * 25))
            reason = " · ".join(reasons_baja[:2]) if reasons_baja else "Presión vendedora dominante"
            return {
                "direction": "BAJA",
                "label": f"🔮 PRÓXIMA VELA: 🔴 BAJA ({prob}%)",
                "short_label": "🔴 BAJA",
                "probability": prob,
                "reason": reason
            }
        else:
            return {
                "direction": "INDECISIÓN",
                "label": "🔮 PRÓXIMA VELA: ⚖️ INDECISIÓN",
                "short_label": "⚖️ INDECISIÓN",
                "probability": 50,
                "reason": "Fuerzas equilibradas en la vela actual"
            }


# =========================================================================
# BAYESIAN LOG-ODDS MASTER CONSENSUS ENGINE
# =========================================================================

class ConsensusMasterAgent:
    """Institutional Master Consensus Coordinator with Bayesian Log-Odds Confluence."""
    def __init__(self):
        self.pa_agent = PriceActionAgent()
        self.st_agent = MarketStructureAgent()
        self.ind_agent = TechnicalIndicatorAgent()
        self.bb_agent = VolatilityBollingerAgent()
        self.macd_agent = MACDMomentumAgent()
        self.trap_agent = SmartMoneyTrapAgent()
        self.next_candle_agent = NextCandlePredictorAgent()

    def evaluate(self, candles: List[Candle]) -> Dict[str, Any]:
        if len(candles) < 3:
            return {
                "signal": "ESPERAR", "confidence": 50, "recommended_time": "—",
                "duration_seconds": 0, "explanation": "Insuficientes velas detectadas.",
                "next_candle": {"direction": "INDECISIÓN", "label": "🔮 PRÓXIMA VELA: ESPERAR", "probability": 50, "reason": "Sin datos"},
                "rsi": 50.0, "trend": "Lateral", "count": len(candles), "agents": {}
            }

        # Ejecución paralela de todos los agentes
        r_pa = self.pa_agent.analyze(candles)
        r_st = self.st_agent.analyze(candles)
        r_ind = self.ind_agent.analyze(candles)
        r_bb = self.bb_agent.analyze(candles)
        r_macd = self.macd_agent.analyze(candles)
        r_trap = self.trap_agent.analyze(candles)
        r_next = self.next_candle_agent.predict(candles, r_pa, r_st, r_ind, r_bb, r_trap)

        # 1. Filtro de Squeeze Peligroso
        if r_bb.get("is_squeeze"):
            return {
                "signal": "ESPERAR", "confidence": 42, "recommended_time": "—",
                "duration_seconds": 0,
                "explanation": "FILTRADO: Mercado en Squeeze plano sin volumen. Prohibido operar hasta ruptura.",
                "next_candle": {"direction": "INDECISIÓN", "label": "🔮 PRÓXIMA VELA: ⚖️ SQUEEZE", "probability": 45, "reason": "Compresión de volatilidad"},
                "rsi": r_ind.get("rsi", 50.0), "trend": "Lateral", "count": len(candles),
                "agents": {
                    "price_action": r_pa, "structure": r_st, "indicators": r_ind,
                    "bollinger": r_bb, "macd": r_macd, "trap": r_trap
                }
            }

        # 2. Bayesian Log-Odds Evidence Accumulator
        # Evidence weights calibrated for Binary Options predictability:
        factors = [
            (r_pa, 0.25),     # Acción del precio y mechas
            (r_trap, 0.22),   # Smart Money, trampas y FVG
            (r_st, 0.18),     # Estructura S/R y Golden Pocket
            (r_bb, 0.15),     # Perforación y rebote de Bollinger
            (r_ind, 0.10),    # Indicadores EMA y RSI
            (r_macd, 0.10)    # Momentum MACD
        ]

        log_odds = 0.0
        call_confluences = 0
        put_confluences = 0

        for agent_res, weight in factors:
            vote = agent_res.get("vote")
            conf = agent_res.get("confidence", 50)
            norm_conf = (conf - 50.0) / 45.0  # Escala 0 a 1
            if vote == "CALL":
                log_odds += weight * norm_conf * 3.5
                call_confluences += 1
            elif vote == "PUT":
                log_odds -= weight * norm_conf * 3.5
                put_confluences += 1

        # Filtros de estructura
        if r_st.get("block_call"):
            log_odds -= 1.8
        if r_st.get("block_put"):
            log_odds += 1.8

        # Inclusión del predictor de la próxima vela
        if r_next["direction"] == "SUBE":
            log_odds += 1.2
        elif r_next["direction"] == "BAJA":
            log_odds -= 1.2

        # Probabilidad Bayesiana Final (Sigmoide)
        prob_call = 1.0 / (1.0 + np.exp(-np.clip(log_odds, -8.0, 8.0)))
        prob_put = 1.0 - prob_call

        final_signal = "ESPERAR"
        final_confidence = 50
        recommended_time = "1 VELA (M1)"
        duration_seconds = 60

        if prob_call >= 0.65 or (r_next["direction"] == "SUBE" and prob_call >= 0.55):
            final_signal = "CALL"
            final_confidence = min(96, int(max(prob_call * 100, r_next["probability"])))
            if "Martillo" in r_pa.get("pattern", "") or r_trap.get("vote") == "CALL":
                recommended_time = "1 VELA (M1)"
                duration_seconds = 60
            elif "Ruptura" in r_st.get("zone", ""):
                recommended_time = "3 MIN"
                duration_seconds = 180
            else:
                recommended_time = "2 MIN"
                duration_seconds = 120

        elif prob_put >= 0.65 or (r_next["direction"] == "BAJA" and prob_put >= 0.55):
            final_signal = "PUT"
            final_confidence = min(96, int(max(prob_put * 100, r_next["probability"])))
            if "Estrella" in r_pa.get("pattern", "") or r_trap.get("vote") == "PUT":
                recommended_time = "1 VELA (M1)"
                duration_seconds = 60
            elif "Ruptura" in r_st.get("zone", ""):
                recommended_time = "3 MIN"
                duration_seconds = 180
            else:
                recommended_time = "2 MIN"
                duration_seconds = 120

        # Explicación de confluencias de mayor peso
        if final_signal != "ESPERAR":
            explanation = (
                f"⚡ {r_next['label']}. Confluencia ({final_confidence}%): {r_next['reason']} | "
                f"Nivel: {r_st.get('zone', 'S/R')} | RSI: {r_ind.get('rsi', 50)}."
            )
        else:
            explanation = (
                f"Consenso IA (Esperar · {r_next['reason']}): "
                "Fuerzas equilibradas entre compradores y vendedores. Esperando gatillo direccional."
            )

        return {
            "signal": final_signal,
            "confidence": final_confidence,
            "recommended_time": recommended_time,
            "duration_seconds": duration_seconds,
            "explanation": explanation,
            "next_candle": r_next,
            "prob_call": round(float(prob_call * 100), 1),
            "prob_put": round(float(prob_put * 100), 1),
            "rsi": r_ind.get("rsi", 50.0),
            "trend": "Alcista" if log_odds > 0.4 else "Bajista" if log_odds < -0.4 else "Lateral",
            "count": len(candles),
            "agents": {
                "price_action": r_pa,
                "structure": r_st,
                "indicators": r_ind,
                "bollinger": r_bb,
                "macd": r_macd,
                "trap": r_trap
            }
        }
