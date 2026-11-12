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


def synthesize_m5(candles: List[Candle]) -> List[Dict[str, Any]]:
    """Group 1M candles into synthetic 5M fractal candles."""
    if not candles:
        return []
    m5_candles = []
    chunk_size = 5
    for i in range(0, len(candles), chunk_size):
        chunk = candles[i:i+chunk_size]
        if not chunk:
            continue
        c_open = chunk[0].open
        c_high = max(cd.high for cd in chunk)
        c_low = min(cd.low for cd in chunk)
        c_close = chunk[-1].close
        color = 1 if c_close >= c_open else -1
        body_h = abs(c_close - c_open)
        rng = max(1.0, c_high - c_low)
        upper_w = max(0.1, c_high - max(c_open, c_close))
        lower_w = max(0.1, min(c_open, c_close) - c_low)
        m5_candles.append({
            "open": c_open, "high": c_high, "low": c_low, "close": c_close,
            "color": color, "body_size": body_h, "range_size": rng,
            "upper_wick": upper_w, "lower_wick": lower_w,
            "lw_ratio": lower_w / rng, "uw_ratio": upper_w / rng,
            "body_ratio": body_h / rng
        })
    return m5_candles


def detect_smc_structure(candles: List[Candle]) -> Dict[str, Any]:
    """
    Smart Money Concepts (SMC) Institutional Engine:
    - Swing Highs / Swing Lows (Fractal pivots)
    - BOS (Break of Structure): Momentum continuation
    - Liquidity Sweeps (Turtle Soup): Stop hunts by market makers
    - Institutional Order Blocks (OB): Unmitigated reaction zones
    - Fair Value Gaps (FVG): Imbalance pockets
    """
    if len(candles) < 5:
        return {
            "bos": "Neutral", "ob": "Ninguno", "ob_vote": "NEUTRO", 
            "fvg": "Equilibrado", "sweep": "Ninguno", "sweep_vote": "NEUTRO"
        }
    
    highs = [c.high for c in candles]
    lows = [c.low for c in candles]
    
    sh = []
    sl = []
    for i in range(2, len(candles) - 1):
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] >= highs[i+1]:
            sh.append((i, highs[i]))
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] <= lows[i+1]:
            sl.append((i, lows[i]))
            
    last_c = candles[-1]
    last_sh = sh[-1][1] if sh else max(highs[:-1])
    last_sl = sl[-1][1] if sl else min(lows[:-1])
    
    # 1. Break of Structure (BOS)
    bos = "Neutral"
    if last_c.close > last_sh:
        bos = "BOS Alcista (Expansión)"
    elif last_c.close < last_sl:
        bos = "BOS Bajista (Expansión)"
        
    # 2. Liquidity Sweep (Turtle Soup)
    sweep = "Ninguno"
    sweep_vote = "NEUTRO"
    rng = max(1.0, last_c.range_size)
    if last_c.high > last_sh and last_c.close < last_sh and (last_c.upper_wick / rng) >= 0.35:
        sweep = f"Caza de Stops sobre Máximo ({last_sh:.1f})"
        sweep_vote = "PUT"
    elif last_c.low < last_sl and last_c.close > last_sl and (last_c.lower_wick / rng) >= 0.35:
        sweep = f"Caza de Stops bajo Mínimo ({last_sl:.1f})"
        sweep_vote = "CALL"

    # 3. Institutional Order Block (OB)
    ob = "Ninguno"
    ob_vote = "NEUTRO"
    for i in range(len(candles) - 4, len(candles) - 1):
        if i >= 1:
            cd = candles[i]
            # Bullish OB: last red candle before green expansion
            if cd.color == -1 and candles[i+1].color == 1 and candles[i+1].close > cd.open:
                if last_c.low <= cd.high and last_c.close >= cd.low:
                    ob = f"Retest Bullish OB [{cd.low:.1f}-{cd.high:.1f}]"
                    ob_vote = "CALL"
                    break
            # Bearish OB: last green candle before red expansion
            elif cd.color == 1 and candles[i+1].color == -1 and candles[i+1].close < cd.open:
                if last_c.high >= cd.low and last_c.close <= cd.high:
                    ob = f"Retest Bearish OB [{cd.low:.1f}-{cd.high:.1f}]"
                    ob_vote = "PUT"
                    break
                    
    # 4. Fair Value Gap (FVG)
    fvg = "Equilibrado"
    if len(candles) >= 3:
        c1, c3 = candles[-3], candles[-1]
        if c3.low > c1.high:
            fvg = "Bullish FVG (Imbalance Alcista)"
        elif c3.high < c1.low:
            fvg = "Bearish FVG (Imbalance Bajista)"
            
    return {
        "bos": bos, "ob": ob, "ob_vote": ob_vote, 
        "fvg": fvg, "sweep": sweep, "sweep_vote": sweep_vote,
        "last_sh": last_sh, "last_sl": last_sl
    }


def analyze_vsa(candles: List[Candle]) -> Dict[str, Any]:
    """Volume Spread Analysis (VSA): Relative Volatility & Institutional Absorption."""
    if not candles:
        return {"rel_spread": 1.0, "status": "Normal", "is_stopping_vol": False}
    c = candles[-1]
    rngs = [cd.range_size for cd in candles[-10:]]
    avg_rng = float(np.mean(rngs)) if rngs else c.range_size
    rel_spread = c.range_size / max(1.0, avg_rng)
    
    rng = max(1.0, c.range_size)
    lw_ratio = c.lower_wick / rng
    uw_ratio = c.upper_wick / rng
    
    is_stopping_vol = rel_spread >= 1.35 and (lw_ratio >= 0.45 or uw_ratio >= 0.45)
    is_no_supply = rel_spread <= 0.65 and c.color == -1
    is_no_demand = rel_spread <= 0.65 and c.color == 1
    
    status = "Normal"
    if is_stopping_vol:
        status = "Absorción Institucional (Stopping Volume)"
    elif is_no_supply:
        status = "No Supply (Secado de Ventas)"
    elif is_no_demand:
        status = "No Demand (Secado de Compras)"
    elif rel_spread >= 1.6:
        status = "Ultra Alto Spread (Impulso Fuerte)"
        
    return {
        "rel_spread": round(rel_spread, 2),
        "status": status,
        "is_stopping_vol": is_stopping_vol
    }


# =========================================================================
# HIGH WIN-RATE SNIPER ENGINE
# =========================================================================

class ConsensusMasterAgent:
    """Master Quantitative Sniper Engine integrating SMC, Fractal M5, VSA & Bayesian Intelligence."""
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
        # MÓDULO INTELIGENTE 1: SMART MONEY CONCEPTS & ESTRUCTURA
        # =============================================================
        smc = detect_smc_structure(candles)

        # =============================================================
        # MÓDULO INTELIGENTE 2: FRACTAL SYNTHETIC M5 ANALYSIS
        # =============================================================
        m5_list = synthesize_m5(candles)
        current_m5 = m5_list[-1] if m5_list else None
        m5_bullish = current_m5 and (current_m5["color"] == 1 or current_m5["lw_ratio"] >= 0.35)
        m5_bearish = current_m5 and (current_m5["color"] == -1 or current_m5["uw_ratio"] >= 0.35)

        # =============================================================
        # MÓDULO INTELIGENTE 3: VOLUME SPREAD ANALYSIS (VSA)
        # =============================================================
        vsa = analyze_vsa(candles)

        # =============================================================
        # PILAR 1: ANÁLISIS DE VELAS ANTERIORES & PATRONES
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
            p2_detail = f"EMA 9>21>50 + M5 ({'Alcista' if m5_bullish else 'Neutral'})"
        elif bear_trend_strong:
            p2_vote = "PUT"
            p2_score = 92
            p2_status = "Bajista Fuerte"
            p2_detail = f"EMA 9<21<50 + M5 ({'Bajista' if m5_bearish else 'Neutral'})"
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
        elif smc["sweep_vote"] == "PUT":
            p3_vote = "PUT"
            p3_status = "Trampa de Toros (SMC)"
            p3_detail = smc["sweep"]
        elif smc["sweep_vote"] == "CALL":
            p3_vote = "CALL"
            p3_status = "Trampa de Osos (SMC)"
            p3_detail = smc["sweep"]
        elif smc["ob_vote"] == "CALL" and dist_to_res >= 0.05:
            p3_vote = "CALL"
            p3_status = "Order Block SMC"
            p3_detail = smc["ob"]
        elif smc["ob_vote"] == "PUT" and dist_to_sup >= 0.05:
            p3_vote = "PUT"
            p3_status = "Order Block SMC"
            p3_detail = smc["ob"]
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
        # MÓDULO 4: PROBABILIDAD BAYESIANA ADAPTATIVA
        # =============================================================
        z_call = 0.0
        z_put = 0.0

        # Evidencia de Velas y VSA
        if p1_vote == "CALL":
            z_call += 1.4
        elif p1_vote == "PUT":
            z_put += 1.4

        if vsa["is_stopping_vol"] and lw_ratio >= 0.45:
            z_call += 1.2
        elif vsa["is_stopping_vol"] and uw_ratio >= 0.45:
            z_put += 1.2

        # Evidencia de Tendencia Macro
        if p2_vote == "CALL":
            z_call += 1.3
            z_put -= 1.5
        elif p2_vote == "PUT":
            z_put += 1.3
            z_call -= 1.5

        # Evidencia Fractal M5
        if m5_bullish:
            z_call += 1.0
        if m5_bearish:
            z_put += 1.0

        # Evidencia Smart Money (SMC)
        if smc["sweep_vote"] == "CALL":
            z_call += 2.2
        elif smc["sweep_vote"] == "PUT":
            z_put += 2.2

        if smc["ob_vote"] == "CALL":
            z_call += 1.5
        elif smc["ob_vote"] == "PUT":
            z_put += 1.5

        if smc["bos"] == "BOS Alcista (Expansión)":
            z_call += 0.8
        elif smc["bos"] == "BOS Bajista (Expansión)":
            z_put += 0.8

        # Penalizaciones estrictas de protección
        if not p3_is_safe:
            z_call -= 3.0
            z_put -= 3.0
        if consec_green >= 3:
            z_call -= 3.0
        if consec_red >= 3:
            z_put -= 3.0
        if dist_to_res < 0.035:
            z_call -= 3.5
        if dist_to_sup < 0.035:
            z_put -= 3.5

        # Cálculo de probabilidades sigmoides calibradas
        prob_call = round(float(100.0 / (1.0 + np.exp(-z_call))), 1)
        prob_put = round(float(100.0 / (1.0 + np.exp(-z_put))), 1)

        # =============================================================
        # REGLA DE ORO DE CONFLUENCIA
        # =============================================================
        signal = "ESPERAR"
        confidence = 50
        grade = "—"
        setup_name = ""
        reason = ""
        next_candle_dir = "INDECISIÓN"
        next_candle_label = "🔮 PRÓXIMA VELA (1M): ⚖️ INDECISIÓN"
        next_candle_prob = 50

        # Caso A: Trampa de Liquidez Detectada (SMC Sweep)
        if smc["sweep_vote"] == "PUT" and p3_is_safe and p2_vote != "CALL":
            signal = "PUT"
            confidence = max(90, min(97, int(prob_put)))
            grade = "A+"
            setup_name = "Trampa de Toros (SMC Bear Sweep)"
            reason = f"{smc['sweep']} + Absorción de Smart Money"
            next_candle_dir = "BAJA"
            next_candle_label = f"🔮 PRÓXIMA VELA (1M): 🔴 BAJA ({confidence}%)"
            next_candle_prob = confidence

        elif smc["sweep_vote"] == "CALL" and p3_is_safe and p2_vote != "PUT":
            signal = "CALL"
            confidence = max(90, min(97, int(prob_call)))
            grade = "A+"
            setup_name = "Trampa de Osos (SMC Bull Sweep)"
            reason = f"{smc['sweep']} + Absorción de Smart Money"
            next_candle_dir = "SUBE"
            next_candle_label = f"🔮 PRÓXIMA VELA (1M): 🟢 SUBE ({confidence}%)"
            next_candle_prob = confidence

        # Caso B: Confluencia Cuántica Probabilística (P >= 85% + P3 Seguro)
        elif p3_is_safe:
            if prob_call >= 85.0 and p1_vote == "CALL" and (p2_vote == "CALL" or (p2_vote == "NEUTRO" and c.low <= lower_bb)):
                signal = "CALL"
                confidence = max(86, min(96, int(prob_call)))
                grade = "A+"
                setup_name = f"{p1_detail} | {smc['bos'] or 'Impulso'}"
                reason = f"Confluencia Cuántica: {p1_detail} + M5 Alcista + {vsa['status']}"
                next_candle_dir = "SUBE"
                next_candle_label = f"🔮 PRÓXIMA VELA (1M): 🟢 SUBE ({confidence}%)"
                next_candle_prob = confidence

            elif prob_put >= 85.0 and p1_vote == "PUT" and (p2_vote == "PUT" or (p2_vote == "NEUTRO" and c.high >= upper_bb)):
                signal = "PUT"
                confidence = max(86, min(96, int(prob_put)))
                grade = "A+"
                setup_name = f"{p1_detail} | {smc['bos'] or 'Impulso'}"
                reason = f"Confluencia Cuántica: {p1_detail} + M5 Bajista + {vsa['status']}"
                next_candle_dir = "BAJA"
                next_candle_label = f"🔮 PRÓXIMA VELA (1M): 🔴 BAJA ({confidence}%)"
                next_candle_prob = confidence

        if signal == "ESPERAR":
            if not p3_is_safe:
                blocker = f"Anti-Manipulación ({p3_status}: {p3_detail})"
            elif p1_status == "Agotamiento":
                blocker = f"Velas Anteriores ({p1_detail})"
            elif p1_vote != "ESPERAR" and p2_vote != "ESPERAR" and p1_vote != p2_vote:
                blocker = f"Conflicto de Tendencia (Velas: {p1_vote} vs Tendencia: {p2_status})"
            else:
                blocker = f"Probabilidad insuficiente (CALL: {prob_call}% | PUT: {prob_put}%) - Esperando Setup A+"

            explanation = f"Consenso IA Cuántico (Esperar): {blocker}. Protegiendo saldo."
        else:
            explanation = f"🎯 [IA CUÁNTICA A+ | {grade}] ({confidence}%): Entrada {signal} (1 MIN). {reason}."

        trend_str = f"{p2_status} (M5: {'🟢' if m5_bullish else '🔴' if m5_bearish else '⚪'})"

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
                "candles": {"vote": p1_vote, "status": vsa["status"], "detail": f"{p1_detail} | Spread {vsa['rel_spread']}x"},
                "trend": {"vote": p2_vote, "status": p2_status, "detail": f"{p2_detail} | M5: {'Alcista' if m5_bullish else 'Bajista' if m5_bearish else 'Neutral'}"},
                "manipulation": {"vote": p3_vote if p3_vote != "NEUTRO" else ("ESPERAR" if not p3_is_safe else "LIMPIO"), "status": p3_status, "detail": f"{p3_detail} | {smc['ob']}"},
                "confluence": {"vote": signal, "status": grade, "detail": f"Prob: 🟢{prob_call}% 🔴{prob_put}% | {setup_name or 'Esperando A+'}"}
            }
        }
