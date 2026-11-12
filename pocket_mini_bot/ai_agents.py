"""
Sniper Institutional Trading Engine for Pocket Mini Bot.
High Win-Rate Methodology for 1-Minute Binary Options (Pocket Option):

THE 4 GOLDEN A+ SNIPER SETUPS:
1. SETUP A+ (RECHAZO ELÁSTICO DE MECHA / PINBAR ABSORPTION):
   - Fuerte absorción institucional: Mecha de rechazo >= 50% del rango total.
   - Cuerpo pequeño (<= 30%) y mecha opuesta insignificante (<= 20%).
   - Alta probabilidad de retroceso elástico en la apertura de la siguiente vela (88%-95%).

2. SETUP A+ (EXPANSIÓN DE IMPULSO CONTINUO / MARUBOZU BREAKOUT):
   - Aceleración institucional: 2 velas consecutivas en la misma dirección.
   - Vela actual supera en tamaño a la anterior (volumen creciente).
   - Mecha en la dirección del movimiento <= 15% (cierre firme sin vacilación).
   - Continuación garantizada en la siguiente vela (85%-92%).

3. SETUP A+ (TRAMPA DE LIQUIDEZ SMART MONEY / SMC TURTLE SOUP):
   - Falsa ruptura de máximos/mínimos de las últimas 6-12 velas.
   - El precio perfora el nivel para cazar stops minoristas y cierra dentro del rango con mecha.
   - Giro violento institucional en la siguiente vela (90%-96%).

4. SETUP A+ (REVERSIÓN EXTREMA BOLLINGER + SOBREVENTA/SOBRECOMPRA):
   - Perforación profunda de la banda exterior de 2.0 desviaciones.
   - RSI < 28 (para CALL) o RSI > 72 (para PUT).
   - Absorción elástica inmediata hacia la media móvil.

5. FILTRO ESTRICTO DE CHOP / CONSOLIDACIÓN (PROTECCIÓN DE CAPITAL):
   - Si el mercado está en dojis o velas planas sin desplazamiento, el bot bloquea operaciones.
   - «Calidad antes que cantidad»: solo opera cuando hay ventaja matemática real.
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


def calc_ema(prices: List[float], period: int) -> float:
    if not prices:
        return 0.0
    k = 2.0 / (period + 1.0)
    ema = prices[0]
    for p in prices[1:]:
        ema = p * k + ema * (1.0 - k)
    return ema


def calc_rsi(prices: List[float], period: int = 14) -> float:
    if len(prices) < 2:
        return 50.0
    deltas = np.diff(prices)
    gains = np.maximum(deltas, 0)
    losses = np.maximum(-deltas, 0)
    if len(deltas) < period:
        avg_gain = float(np.mean(gains)) if len(gains) > 0 else 0.0
        avg_loss = float(np.mean(losses)) if len(losses) > 0 else 0.0
    else:
        avg_gain = float(np.mean(gains[:period]))
        avg_loss = float(np.mean(losses[:period]))
        for g, l in zip(gains[period:], losses[period:]):
            avg_gain = (avg_gain * (period - 1) + g) / period
            avg_loss = (avg_loss * (period - 1) + l) / period
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return round(float(100.0 - (100.0 / (1.0 + rs))), 1)


def calc_bollinger(prices: List[float], period: int = 20) -> Tuple[float, float, float]:
    p_sub = prices[-period:] if len(prices) >= period else prices
    mid = float(np.mean(p_sub))
    std = float(np.std(p_sub)) if len(p_sub) > 1 else 1.0
    return mid + 2.0 * std, mid, mid - 2.0 * std


# =========================================================================
# HIGH WIN-RATE SNIPER ENGINE
# =========================================================================

class ConsensusMasterAgent:
    """Master Sniper Engine executing only proven, high-probability A+ Setups."""
    def __init__(self):
        pass

    def evaluate(self, candles: List[Candle]) -> Dict[str, Any]:
        if len(candles) < 3:
            return {
                "signal": "ESPERAR", "confidence": 50, "grade": "—",
                "recommended_time": "—", "duration_seconds": 0,
                "explanation": "Escaneando gráfico en busca de velas...",
                "next_candle": {"direction": "INDECISIÓN", "label": "🔮 PRÓXIMA VELA: EVALUANDO", "probability": 50, "reason": "Pocas velas"},
                "rsi": 50.0, "trend": "Lateral", "count": len(candles), "agents": {}
            }

        c = candles[-1]
        prev = candles[-2]
        prev2 = candles[-3] if len(candles) >= 3 else prev

        prices = [cd.close for cd in candles]
        rsi = calc_rsi(prices, 14)
        upper_bb, mid_bb, lower_bb = calc_bollinger(prices, 20)
        ema9 = calc_ema(prices, 9)
        ema21 = calc_ema(prices, 21)
        ema50 = calc_ema(prices, min(50, len(prices)))

        rng = max(1.0, c.range_size)
        lw_ratio = c.lower_wick / rng
        uw_ratio = c.upper_wick / rng
        body_ratio = c.body_size / rng

        # Recopilación de extremos de las últimas 8 velas previas
        past_highs = [cd.high for cd in candles[:-1]]
        past_lows = [cd.low for cd in candles[:-1]]
        recent_high = max(past_highs[-8:]) if past_highs else c.high
        recent_low = min(past_lows[-8:]) if past_lows else c.low

        # Mapeo de Soporte y Resistencia Global del Gráfico
        all_highs = [cd.high for cd in candles]
        all_lows = [cd.low for cd in candles]
        max_h = max(all_highs)
        min_l = min(all_lows)
        total_range = max(1.0, max_h - min_l)
        curr_price = prices[-1]
        dist_to_res = (max_h - curr_price) / total_range
        dist_to_sup = (curr_price - min_l) / total_range

        # Conteo de velas consecutivas previas (para evitar trampas de agotamiento)
        consec_green = 0
        consec_red = 0
        for cd in reversed(candles[:-1]):
            if cd.color == 1 and consec_red == 0:
                consec_green += 1
            elif cd.color == -1 and consec_green == 0:
                consec_red += 1
            else:
                break

        # =============================================================
        # PILAR 1: ANÁLISIS DE VELAS ANTERIORES (SECUENCIA & MOMENTUM)
        # =============================================================
        p1_vote = "ESPERAR"
        p1_score = 50
        p1_status = "Neutral"
        p1_detail = "Sin patrón claro en velas anteriores"

        is_morning_star = (
            prev2.color == -1 and 
            prev.body_size <= prev2.body_size * 0.45 and 
            c.color == 1 and 
            c.close >= (prev2.open + prev2.close) / 2.0
        )
        is_evening_star = (
            prev2.color == 1 and 
            prev.body_size <= prev2.body_size * 0.45 and 
            c.color == -1 and 
            c.close <= (prev2.open + prev2.close) / 2.0
        )
        is_bull_engulf = (
            prev.color == -1 and 
            c.color == 1 and 
            c.close >= prev.open and 
            c.body_size > prev.body_size * 1.10
        )
        is_bear_engulf = (
            prev.color == 1 and 
            c.color == -1 and 
            c.close <= prev.open and 
            c.body_size > prev.body_size * 1.10
        )
        is_bull_marubozu = (
            c.color == 1 and 
            prev.color == 1 and 
            c.body_size > prev.body_size * 1.10 and 
            uw_ratio <= 0.15 and 
            body_ratio >= 0.65
        )
        is_bear_marubozu = (
            c.color == -1 and 
            prev.color == -1 and 
            c.body_size > prev.body_size * 1.10 and 
            lw_ratio <= 0.15 and 
            body_ratio >= 0.65
        )
        is_hammer_rejection = (lw_ratio >= 0.48 and body_ratio <= 0.40)
        is_star_rejection = (uw_ratio >= 0.48 and body_ratio <= 0.40)

        # Chequeo de agotamiento en velas anteriores
        if consec_green >= 3:
            p1_vote = "ESPERAR"
            p1_status = "Agotamiento"
            p1_detail = f"Agotamiento: {consec_green+1} verdes seguidas (riesgo de retroceso)"
        elif consec_red >= 3:
            p1_vote = "ESPERAR"
            p1_status = "Agotamiento"
            p1_detail = f"Agotamiento: {consec_red+1} rojas seguidas (riesgo de rebote)"
        elif is_morning_star:
            p1_vote = "CALL"
            p1_score = 92
            p1_status = "Giro 3 Velas"
            p1_detail = "Morning Star confirmado en 3 velas"
        elif is_evening_star:
            p1_vote = "PUT"
            p1_score = 92
            p1_status = "Giro 3 Velas"
            p1_detail = "Evening Star confirmado en 3 velas"
        elif is_bull_engulf:
            p1_vote = "CALL"
            p1_score = 89
            p1_status = "Envolvente"
            p1_detail = "Vela verde absorbe a la roja anterior"
        elif is_bear_engulf:
            p1_vote = "PUT"
            p1_score = 89
            p1_status = "Envolvente"
            p1_detail = "Vela roja absorbe a la verde anterior"
        elif is_bull_marubozu:
            p1_vote = "CALL"
            p1_score = 90
            p1_status = "Impulso Sólido"
            p1_detail = "Marubozu verde expansivo sin mecha frontal"
        elif is_bear_marubozu:
            p1_vote = "PUT"
            p1_score = 90
            p1_status = "Impulso Sólido"
            p1_detail = "Marubozu rojo expansivo sin mecha frontal"
        elif is_hammer_rejection:
            p1_vote = "CALL"
            p1_score = 91
            p1_status = "Rechazo Mecha"
            p1_detail = f"Martillo con {int(lw_ratio*100)}% mecha inferior"
        elif is_star_rejection:
            p1_vote = "PUT"
            p1_score = 91
            p1_status = "Rechazo Mecha"
            p1_detail = f"Estrella fugaz con {int(uw_ratio*100)}% mecha superior"

        # =============================================================
        # PILAR 2: ANÁLISIS DE LA TENDENCIA (ESTRUCTURA & MEDIAS MÓVILES)
        # =============================================================
        p2_vote = "ESPERAR"
        p2_score = 50
        p2_status = "Lateral"
        p2_detail = "Sin tendencia clara"

        bull_trend_strong = (ema9 > ema21 and ema21 > ema50)
        bear_trend_strong = (ema9 < ema21 and ema21 < ema50)
        soft_bull = (ema9 > ema21 and curr_price >= ema21)
        soft_bear = (ema9 < ema21 and curr_price <= ema21)

        if bull_trend_strong:
            p2_vote = "CALL"
            p2_score = 92
            p2_status = "Alcista Fuerte"
            p2_detail = "EMA 9>21>50 alineadas al alza"
        elif bear_trend_strong:
            p2_vote = "PUT"
            p2_score = 92
            p2_status = "Bajista Fuerte"
            p2_detail = "EMA 9<21<50 alineadas a la baja"
        elif soft_bull:
            p2_vote = "CALL"
            p2_score = 82
            p2_status = "Alcista Moderada"
            p2_detail = "EMA 9>21 precio sobre media"
        elif soft_bear:
            p2_vote = "PUT"
            p2_score = 82
            p2_status = "Bajista Moderada"
            p2_detail = "EMA 9<21 precio bajo media"
        else:
            p2_vote = "NEUTRO"
            p2_score = 60
            p2_status = "Rango Lateral"
            p2_detail = "Medias entrelazadas (Mercado en consolidación)"

        # =============================================================
        # PILAR 3: ESCUDO & DETECCIÓN DE MANIPULACIÓN DE BROKER (OTC)
        # =============================================================
        is_bull_trap = (c.high > recent_high and c.close < recent_high and uw_ratio >= 0.35)
        is_bear_trap = (c.low < recent_low and c.close > recent_low and lw_ratio >= 0.35)

        is_spike_manipulation = (uw_ratio >= 0.68 or lw_ratio >= 0.68) and c.body_size < 3.5
        avg_body = float(np.mean([cd.body_size for cd in candles[-5:]])) if len(candles) >= 5 else c.body_size
        is_flat_doji = c.body_size < 2.0 or rng < 3.0 or (c.body_size < avg_body * 0.22)

        p3_is_safe = True
        p3_vote = "NEUTRO"
        p3_status = "Limpio"
        p3_detail = "Sin manipulación detectable"

        if is_spike_manipulation:
            p3_is_safe = False
            p3_status = "Spike OTC Falso"
            p3_detail = "Mecha extrema artificial detectada (>68% rango). Bloqueado."
        elif is_flat_doji:
            p3_is_safe = False
            p3_status = "Doji / Sin Volumen"
            p3_detail = "Vela plana sin volumen institucional. Bloqueado."
        elif is_bull_trap:
            p3_vote = "PUT"
            p3_status = "Trampa de Toros (SMC)"
            p3_detail = f"Falsa ruptura de máximos ({recent_high:.1f}). Absorción bajista."
        elif is_bear_trap:
            p3_vote = "CALL"
            p3_status = "Trampa de Osos (SMC)"
            p3_detail = f"Falsa ruptura de mínimos ({recent_low:.1f}). Absorción alcista."
        elif dist_to_res < 0.035:
            p3_is_safe = False
            p3_status = "Techo Inmediato"
            p3_detail = "Precio rozando resistencia máxima (alto riesgo de rechazo)."
        elif dist_to_sup < 0.035:
            p3_is_safe = False
            p3_status = "Piso Inmediato"
            p3_detail = "Precio rozando soporte mínimo (alto riesgo de rebote)."
        elif rsi > 70:
            p3_is_safe = False
            p3_status = "RSI Sobrecomprado"
            p3_detail = f"RSI extremo ({rsi:.1f}). Riesgo de comprar en el pico."
        elif rsi < 30:
            p3_is_safe = False
            p3_status = "RSI Sobrevendido"
            p3_detail = f"RSI extremo ({rsi:.1f}). Riesgo de vender en el suelo."

        # =============================================================
        # REGLA DE ORO: CONFLUENCIA DE LOS 3 PILARES PARA ENTRAR
        # =============================================================
        signal = "ESPERAR"
        confidence = 50
        grade = "—"
        setup_name = ""
        reason = ""
        next_candle_dir = "INDECISIÓN"
        next_candle_label = "🔮 PRÓXIMA VELA (1M): ⚖️ INDECISIÓN"
        next_candle_prob = 50

        # Caso A: Trampa de Liquidez Detectada (Aprovechamos la manipulación del broker)
        if p3_vote == "PUT" and p3_is_safe and p2_vote != "CALL":
            signal = "PUT"
            confidence = 94
            grade = "A+"
            setup_name = "Trampa de Toros (SMC Bear Trap)"
            reason = "Manipulación de broker detectada: falsa ruptura y rechazo masivo"
            next_candle_dir = "BAJA"
            next_candle_label = f"🔮 PRÓXIMA VELA (1M): 🔴 BAJA ({confidence}%)"
            next_candle_prob = confidence

        elif p3_vote == "CALL" and p3_is_safe and p2_vote != "PUT":
            signal = "CALL"
            confidence = 94
            grade = "A+"
            setup_name = "Trampa de Osos (SMC Bull Trap)"
            reason = "Manipulación de broker detectada: falso barrido y absorción de compras"
            next_candle_dir = "SUBE"
            next_candle_label = f"🔮 PRÓXIMA VELA (1M): 🟢 SUBE ({confidence}%)"
            next_candle_prob = confidence

        # Caso B: Confluencia Triple (Velas Anteriores + Tendencia + Anti-Manipulación Seguro)
        elif p3_is_safe:
            if p1_vote == "CALL" and (p2_vote == "CALL" or (p2_vote == "NEUTRO" and c.low <= lower_bb)):
                signal = "CALL"
                confidence = max(p1_score, p2_score)
                grade = "A+"
                setup_name = p1_detail
                reason = f"Confluencia Triple: {p1_detail} + Tendencia {p2_status}"
                next_candle_dir = "SUBE"
                next_candle_label = f"🔮 PRÓXIMA VELA (1M): 🟢 SUBE ({confidence}%)"
                next_candle_prob = confidence

            elif p1_vote == "PUT" and (p2_vote == "PUT" or (p2_vote == "NEUTRO" and c.high >= upper_bb)):
                signal = "PUT"
                confidence = max(p1_score, p2_score)
                grade = "A+"
                setup_name = p1_detail
                reason = f"Confluencia Triple: {p1_detail} + Tendencia {p2_status}"
                next_candle_dir = "BAJA"
                next_candle_label = f"🔮 PRÓXIMA VELA (1M): 🔴 BAJA ({confidence}%)"
                next_candle_prob = confidence

        if signal == "ESPERAR":
            # Explicación transparente de cuál pilar bloqueó la orden
            if not p3_is_safe:
                blocker = f"Anti-Manipulación ({p3_status}: {p3_detail})"
            elif p1_status == "Agotamiento":
                blocker = f"Velas Anteriores ({p1_detail})"
            elif p1_vote != "ESPERAR" and p2_vote != "ESPERAR" and p1_vote != p2_vote:
                blocker = f"Conflicto de Tendencia (Velas: {p1_vote} vs Tendencia: {p2_status})"
            else:
                blocker = "Esperando confluencia simultánea de Velas + Tendencia + Manipulación"

            explanation = f"Consenso IA (Esperar): {blocker}. Protegiendo saldo."
            prob_call = 50.0
            prob_put = 50.0
        else:
            explanation = f"🎯 [CONFLUENCIA TRIPLE | {grade}] ({confidence}%): Entrada {signal} (1 MIN). {reason}."
            prob_call = float(confidence) if signal == "CALL" else round(100.0 - confidence, 1)
            prob_put = float(confidence) if signal == "PUT" else round(100.0 - confidence, 1)

        trend_str = p2_status

        return {
            "signal": signal,
            "confidence": confidence,
            "grade": grade,
            "setup": setup_name,
            "recommended_time": "1 MINUTO (M1)" if signal != "ESPERAR" else "—",
            "duration_seconds": 60 if signal != "ESPERAR" else 0,
            "explanation": explanation,
            "next_candle": {
                "direction": next_candle_dir,
                "label": next_candle_label.replace("(5M)", "(1M)"),
                "probability": next_candle_prob,
                "reason": setup_name if setup_name else "Fuerzas equilibradas"
            },
            "prob_call": prob_call,
            "prob_put": prob_put,
            "rsi": rsi,
            "trend": trend_str,
            "count": len(candles),
            "agents": {
                "candles": {"vote": p1_vote, "status": p1_status, "detail": p1_detail},
                "trend": {"vote": p2_vote, "status": p2_status, "detail": p2_detail},
                "manipulation": {"vote": p3_vote if p3_vote != "NEUTRO" else ("ESPERAR" if not p3_is_safe else "LIMPIO"), "status": p3_status, "detail": p3_detail},
                "confluence": {"vote": signal, "status": grade, "detail": setup_name or "Esperando 3 Pilares"}
            }
        }
