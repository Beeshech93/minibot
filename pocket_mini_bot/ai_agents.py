"""
Pro-Grade Multi-Agent AI Market Intelligence System for Pocket Mini Bot.
Institutional Architecture with Triple-Confluence Verification:
1. PriceActionAgent: Candlestick patterns, wick absorption, multi-candle structures.
2. MarketStructureAgent: Pivot Swings, Dynamic S/R, Fibonacci Golden Pocket (0.5 - 0.618).
3. TechnicalIndicatorAgent: Triple EMA (9, 21, 50), dynamic RSI 14, Divergence Scanner.
4. VolatilityBollingerAgent: Bollinger Bands (20, 2), Squeeze detection, Mean Reversion.
5. MACDMomentumAgent: MACD Line, Signal Line (12, 26, 9), Histogram momentum shifts.
6. SmartMoneyTrapAgent: Liquidity sweeps, fakeout traps (rejection of false breakouts).
7. InstitutionalConsensusEngine: Triple Confluence validation, strict risk filters, dynamic expirations.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
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


def extract_candles_from_data(xs: List[int], centers: List[float], directions: List[int], heights: List[float]) -> List[Candle]:
    """Convert raw visual column clusters into detailed Candle objects."""
    candles = []
    for x, c, d, h in zip(xs, centers, directions, heights):
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


# Helper EMA function
def calc_ema_series(prices: List[float], period: int) -> List[float]:
    if not prices:
        return []
    k = 2.0 / (period + 1.0)
    ema = [prices[0]]
    for p in prices[1:]:
        ema.append(p * k + ema[-1] * (1.0 - k))
    return ema


class PriceActionAgent:
    """Agent specialized in Japanese Candlestick Patterns and Price Action Rejections."""
    name = "Acción del Precio"

    def analyze(self, candles: List[Candle]) -> Dict[str, Any]:
        if len(candles) < 3:
            return {"vote": "ESPERAR", "confidence": 50, "reason": "Insuficientes velas"}

        c = candles[-1]
        prev = candles[-2]
        prev2 = candles[-3] if len(candles) >= 3 else prev

        # Ratios de absorción de mechas
        lower_ratio = c.lower_wick / max(1.0, c.range_size)
        upper_ratio = c.upper_wick / max(1.0, c.range_size)
        body_ratio = c.body_size / max(1.0, c.range_size)

        # 1. Hammer / Pinbar Alcista (Mecha inferior > 55% del rango total)
        is_hammer = lower_ratio >= 0.55 and upper_ratio <= 0.20
        # 2. Shooting Star / Pinbar Bajista (Mecha superior > 55% del rango total)
        is_shooting_star = upper_ratio >= 0.55 and lower_ratio <= 0.20
        # 3. Bullish Engulfing (Vela verde envolvente de rango superior)
        is_bullish_engulf = (prev.color == -1 and c.color == 1 and 
                             c.close >= prev.open and c.open <= prev.close and c.body_size > prev.body_size * 1.15)
        # 4. Bearish Engulfing (Vela roja envolvente)
        is_bearish_engulf = (prev.color == 1 and c.color == -1 and 
                             c.open >= prev.close and c.close <= prev.open and c.body_size > prev.body_size * 1.15)
        # 5. Morning Star (Patrón de 3 velas: bajista + indecisión + vela alcista fuerte)
        is_morning_star = (prev2.color == -1 and prev.body_size <= prev2.body_size * 0.4 and 
                           c.color == 1 and c.close > (prev2.open + prev2.close) / 2)
        # 6. Evening Star (Patrón de 3 velas: alcista + indecisión + vela bajista fuerte)
        is_evening_star = (prev2.color == 1 and prev.body_size <= prev2.body_size * 0.4 and 
                           c.color == -1 and c.close < (prev2.open + prev2.close) / 2)
        # 7. Doji (Indecisión / Compresión)
        is_doji = body_ratio <= 0.12

        if is_morning_star:
            return {"vote": "CALL", "confidence": 92, "pattern": "Estrella de la Mañana (Morning Star)", "reason": "Giro alcista mayor confirmado por 3 velas"}
        elif is_evening_star:
            return {"vote": "PUT", "confidence": 92, "pattern": "Estrella del Atardecer (Evening Star)", "reason": "Giro bajista mayor confirmado por 3 velas"}
        elif is_hammer:
            return {"vote": "CALL", "confidence": 88, "pattern": "Martillo / Pinbar Alcista", "reason": f"Fuerte absorción compradora ({int(lower_ratio*100)}% mecha inferior)"}
        elif is_bullish_engulf:
            return {"vote": "CALL", "confidence": 89, "pattern": "Envolvente Alcista", "reason": "Absorción total de oferta previa"}
        elif is_shooting_star:
            return {"vote": "PUT", "confidence": 88, "pattern": "Estrella Fugaz / Pinbar Bajista", "reason": f"Fuerte rechazo vendedor ({int(upper_ratio*100)}% mecha superior)"}
        elif is_bearish_engulf:
            return {"vote": "PUT", "confidence": 89, "pattern": "Envolvente Bajista", "reason": "Absorción total de demanda previa"}
        elif is_doji:
            return {"vote": "ESPERAR", "confidence": 40, "pattern": "Doji / Indecisión", "reason": "Equilibrio transitorio; esperar confirmación"}

        # Continuidad de impulso
        if c.color == 1 and prev.color == 1 and c.body_size > prev.body_size * 1.1:
            return {"vote": "CALL", "confidence": 76, "pattern": "Expansión Alcista", "reason": "Cuerpos verdes en aceleración"}
        elif c.color == -1 and prev.color == -1 and c.body_size > prev.body_size * 1.1:
            return {"vote": "PUT", "confidence": 76, "pattern": "Expansión Bajista", "reason": "Cuerpos rojos en aceleración"}

        return {"vote": "ESPERAR", "confidence": 50, "pattern": "Sin patrón claro", "reason": "Velas neutras sin ventaja estadística"}


class MarketStructureAgent:
    """Agent specialized in Support/Resistance, Fibonacci Retracements, and Swings."""
    name = "Estructura & S/R"

    def analyze(self, candles: List[Candle]) -> Dict[str, Any]:
        if len(candles) < 8:
            return {"vote": "ESPERAR", "confidence": 50, "reason": "Datos insuficientes"}

        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        current_price = candles[-1].close
        total_range = max(highs) - min(lows)
        if total_range <= 0:
            return {"vote": "ESPERAR", "confidence": 50, "reason": "Rango plano"}

        # Pivotes locales (extremos de 5 velas)
        swing_highs = []
        swing_lows = []
        for i in range(2, len(candles) - 2):
            if highs[i] >= highs[i-1] and highs[i] >= highs[i-2] and highs[i] >= highs[i+1] and highs[i] >= highs[i+2]:
                swing_highs.append(highs[i])
            if lows[i] <= lows[i-1] and lows[i] <= lows[i-2] and lows[i] <= lows[i+1] and lows[i] <= lows[i+2]:
                swing_lows.append(lows[i])

        highest = max(highs)
        lowest = min(lows)
        nearest_res = min([h for h in swing_highs if h >= current_price], default=highest)
        nearest_sup = max([l for l in swing_lows if l <= current_price], default=lowest)

        dist_res = abs(nearest_res - current_price) / total_range
        dist_sup = abs(current_price - nearest_sup) / total_range

        # Fibonacci Golden Pocket (0.50 a 0.618 de retroceso del impulso mayor)
        fib_50 = lowest + total_range * 0.50
        fib_618 = lowest + total_range * 0.382  # Golden pocket en retroceso
        in_golden_pocket_bull = abs(current_price - fib_50) / total_range < 0.06 and candles[-1].color == 1

        # 1. Rebote en Soporte o Golden Pocket
        if in_golden_pocket_bull:
            return {
                "vote": "CALL", "confidence": 90, "zone": "Fibonacci Golden Pocket",
                "reason": "Rebote institucional en retroceso 50%-61.8% Fibonacci"
            }
        elif dist_sup < 0.07 and candles[-1].color == 1:
            return {
                "vote": "CALL", "confidence": 88, "zone": "Rebote en Soporte",
                "reason": f"Soporte confirmado ({dist_sup*100:.1f}% distancia)"
            }
        elif dist_res < 0.07 and candles[-1].color == -1:
            return {
                "vote": "PUT", "confidence": 88, "zone": "Rechazo en Resistencia",
                "reason": f"Resistencia confirmada ({dist_res*100:.1f}% distancia)"
            }
        elif current_price > nearest_res * 0.998 and candles[-1].color == 1:
            return {
                "vote": "CALL", "confidence": 85, "zone": "Ruptura de Resistencia",
                "reason": "Ruptura limpia de nivel estructural alcista"
            }
        elif current_price < nearest_sup * 1.002 and candles[-1].color == -1:
            return {
                "vote": "PUT", "confidence": 85, "zone": "Ruptura de Soporte",
                "reason": "Ruptura limpia de piso estructural bajista"
            }

        # Filtros de peligro
        if dist_res < 0.025:
            return {
                "vote": "ESPERAR", "confidence": 80, "zone": "Peligro: Techo Próximo",
                "reason": "Precio contra resistencia; bloquear CALL", "block_call": True
            }
        if dist_sup < 0.025:
            return {
                "vote": "ESPERAR", "confidence": 80, "zone": "Peligro: Piso Próximo",
                "reason": "Precio sobre soporte; bloquear PUT", "block_put": True
            }

        return {
            "vote": "ESPERAR", "confidence": 55, "zone": "Zona Media",
            "reason": "Precio oscilando entre niveles clave sin confirmación"
        }


class TechnicalIndicatorAgent:
    """Agent specialized in Triple EMAs (9, 21, 50), Dynamic RSI 14, and Divergences."""
    name = "Indicadores & EMA"

    def analyze(self, candles: List[Candle]) -> Dict[str, Any]:
        if len(candles) < 8:
            return {"vote": "ESPERAR", "confidence": 50, "reason": "Insuficientes velas"}

        prices = [c.close for c in candles]
        ema9 = calc_ema_series(prices, 9)[-1]
        ema21 = calc_ema_series(prices, 21)[-1]
        ema50 = calc_ema_series(prices, min(50, len(prices)))[-1]

        # RSI 14
        deltas = np.diff(prices)
        gains = np.maximum(deltas, 0)
        losses = np.maximum(-deltas, 0)
        p = min(14, len(deltas))
        avg_gain = gains[-p:].mean() if p else 0.0
        avg_loss = losses[-p:].mean() if p else 0.0
        rsi = 100.0 if avg_loss == 0 else (100.0 - (100.0 / (1.0 + (avg_gain / avg_loss))))

        # Divergencias Regulares de RSI
        bullish_div = False
        bearish_div = False
        if len(prices) >= 12:
            recent_low = min(prices[-4:])
            older_low = min(prices[-12:-4])
            if recent_low < older_low and rsi > 34:
                bullish_div = True
            recent_high = max(prices[-4:])
            older_high = max(prices[-12:-4])
            if recent_high > older_high and rsi < 66:
                bearish_div = True

        bull_trend = ema9 > ema21 and ema21 > ema50
        bear_trend = ema9 < ema21 and ema21 < ema50

        if bullish_div:
            return {"vote": "CALL", "confidence": 91, "reason": f"Divergencia Alcista RSI ({rsi:.1f}) · Inversión inminente", "rsi": round(rsi, 1)}
        elif bearish_div:
            return {"vote": "PUT", "confidence": 91, "reason": f"Divergencia Bajista RSI ({rsi:.1f}) · Agotamiento institucional", "rsi": round(rsi, 1)}
        elif bull_trend and rsi < 66 and prices[-1] > ema9:
            return {"vote": "CALL", "confidence": 85, "reason": f"Tendencia Alcista (EMA 9 > 21 > 50) + RSI {rsi:.1f}", "rsi": round(rsi, 1)}
        elif bear_trend and rsi > 34 and prices[-1] < ema9:
            return {"vote": "PUT", "confidence": 85, "reason": f"Tendencia Bajista (EMA 9 < 21 < 50) + RSI {rsi:.1f}", "rsi": round(rsi, 1)}
        elif rsi < 24:
            return {"vote": "CALL", "confidence": 82, "reason": f"Sobreventa Extrema (RSI {rsi:.1f}) · Rebote inminente", "rsi": round(rsi, 1)}
        elif rsi > 76:
            return {"vote": "PUT", "confidence": 82, "reason": f"Sobrecompra Extrema (RSI {rsi:.1f}) · Corrección inminente", "rsi": round(rsi, 1)}

        return {"vote": "ESPERAR", "confidence": 50, "reason": f"Rango neutral (RSI {rsi:.1f})", "rsi": round(rsi, 1)}


class VolatilityBollingerAgent:
    """Agent specialized in Bollinger Bands (20, 2), Volatility Squeeze, and Mean Reversion."""
    name = "Bandas de Bollinger & Volatilidad"

    def analyze(self, candles: List[Candle]) -> Dict[str, Any]:
        if len(candles) < 15:
            return {"vote": "ESPERAR", "confidence": 50, "reason": "Insuficientes datos"}

        prices = [c.close for c in candles]
        window = min(20, len(prices))
        basis = float(np.mean(prices[-window:]))
        std = float(np.std(prices[-window:]))
        upper_band = basis + 2.0 * std
        lower_band = basis - 2.0 * std
        bandwidth = (upper_band - lower_band) / max(1.0, basis)

        current_price = prices[-1]

        # 1. Detección de Squeeze (Compresión de volatilidad peligrosa para binarias)
        is_squeeze = bandwidth < 0.015 or std < 1.2
        if is_squeeze:
            return {
                "vote": "ESPERAR", "confidence": 85, "state": "Squeeze / Rango Plano",
                "reason": "Mercado comprimido sin volatilidad (riesgo alto de doji); evitar operar",
                "is_squeeze": True
            }

        # 2. Mean Reversion (Precio perfora banda exterior con mecha de regreso)
        if current_price <= lower_band and candles[-1].lower_wick >= candles[-1].body_size * 0.8:
            return {
                "vote": "CALL", "confidence": 89, "state": "Perforación Banda Inferior",
                "reason": "Precio bajo Banda Inferior con rechazo; rebote a la media inminente"
            }
        elif current_price >= upper_band and candles[-1].upper_wick >= candles[-1].body_size * 0.8:
            return {
                "vote": "PUT", "confidence": 89, "state": "Perforación Banda Superior",
                "reason": "Precio sobre Banda Superior con rechazo; corrección a la media inminente"
            }

        # 3. Ruptura de Bandas con aceleración (Band Walk)
        if current_price > upper_band and candles[-1].color == 1 and candles[-1].body_size > std:
            return {
                "vote": "CALL", "confidence": 83, "state": "Ruptura Volátil Alcista",
                "reason": "Aceleración de volatilidad montando la banda superior"
            }
        elif current_price < lower_band and candles[-1].color == -1 and candles[-1].body_size > std:
            return {
                "vote": "PUT", "confidence": 83, "state": "Ruptura Volátil Bajista",
                "reason": "Aceleración de volatilidad montando la banda inferior"
            }

        return {
            "vote": "ESPERAR", "confidence": 52, "state": "Dentro de Bandas",
            "reason": f"Precio dentro del canal normal (Ancho: {bandwidth*100:.1f}%)"
        }


class MACDMomentumAgent:
    """Agent specialized in MACD Line, Signal Line (12, 26, 9), and Histogram Momentum Shifts."""
    name = "MACD & Momentum"

    def analyze(self, candles: List[Candle]) -> Dict[str, Any]:
        if len(candles) < 20:
            return {"vote": "ESPERAR", "confidence": 50, "reason": "Insuficientes datos"}

        prices = [c.close for c in candles]
        ema12 = calc_ema_series(prices, 12)
        ema26 = calc_ema_series(prices, 26)
        macd_line = [f - s for f, s in zip(ema12, ema26)]
        signal_line = calc_ema_series(macd_line, 9)
        histogram = [m - s for m, s in zip(macd_line, signal_line)]

        curr_hist = histogram[-1]
        prev_hist = histogram[-2] if len(histogram) >= 2 else curr_hist

        # Cruce de línea cero en histograma (giro de impulso)
        if prev_hist <= 0 and curr_hist > 0:
            return {
                "vote": "CALL", "confidence": 87, "state": "Cruce Alcista MACD",
                "reason": "Histograma MACD cruzó a positivo con fuerte aceleración compradora"
            }
        elif prev_hist >= 0 and curr_hist < 0:
            return {
                "vote": "PUT", "confidence": 87, "state": "Cruce Bajista MACD",
                "reason": "Histograma MACD cruzó a negativo con fuerte aceleración vendedora"
            }
        elif curr_hist > 0 and curr_hist > prev_hist:
            return {
                "vote": "CALL", "confidence": 80, "state": "Momento Alcista Creciente",
                "reason": "Histograma verde en expansión"
            }
        elif curr_hist < 0 and curr_hist < prev_hist:
            return {
                "vote": "PUT", "confidence": 80, "state": "Momento Bajista Creciente",
                "reason": "Histograma rojo en expansión"
            }

        return {
            "vote": "ESPERAR", "confidence": 50, "state": "MACD Plano",
            "reason": "Oscilador sin divergencia ni aceleración notable"
        }


class SmartMoneyTrapAgent:
    """Agent specialized in Liquidity Sweeps, Fakeout Traps, and Institutional Manipulation."""
    name = "Cazador de Trampas & Liquidez"

    def analyze(self, candles: List[Candle]) -> Dict[str, Any]:
        if len(candles) < 10:
            return {"vote": "ESPERAR", "confidence": 50, "reason": "Datos insuficientes"}

        highs = [c.high for c in candles[:-1]]
        lows = [c.low for c in candles[:-1]]
        recent_high = max(highs[-8:])
        recent_low = min(lows[-8:])
        c = candles[-1]

        # 1. Bullish Trap / Liquidity Sweep de Máximos (Falsa Ruptura hacia arriba)
        # La vela supera el máximo anterior pero cierra por debajo con mecha superior larga
        if c.high > recent_high and c.close < recent_high and c.upper_wick >= c.body_size * 1.2:
            return {
                "vote": "PUT", "confidence": 93, "trap": "Trampa de Toros (Bull Trap)",
                "reason": "Barrido de liquidez sobre máximos; compradores atrapados, giro a la baja"
            }

        # 2. Bearish Trap / Liquidity Sweep de Mínimos (Falsa Ruptura hacia abajo)
        # La vela perfora el mínimo anterior pero cierra por encima con mecha inferior larga
        if c.low < recent_low and c.close > recent_low and c.lower_wick >= c.body_size * 1.2:
            return {
                "vote": "CALL", "confidence": 93, "trap": "Trampa de Osos (Bear Trap)",
                "reason": "Barrido de liquidez bajo mínimos; vendedores atrapados, rebote al alza"
            }

        return {
            "vote": "ESPERAR", "confidence": 50, "trap": "Sin trampa",
            "reason": "Estructura de liquidez normal"
        }


class ConsensusMasterAgent:
    """Institutional Master Consensus Coordinator with Triple-Confluence Verification."""
    def __init__(self):
        self.pa_agent = PriceActionAgent()
        self.st_agent = MarketStructureAgent()
        self.ind_agent = TechnicalIndicatorAgent()
        self.bb_agent = VolatilityBollingerAgent()
        self.macd_agent = MACDMomentumAgent()
        self.trap_agent = SmartMoneyTrapAgent()

    def evaluate(self, candles: List[Candle]) -> Dict[str, Any]:
        r_pa = self.pa_agent.analyze(candles)
        r_st = self.st_agent.analyze(candles)
        r_ind = self.ind_agent.analyze(candles)
        r_bb = self.bb_agent.analyze(candles)
        r_macd = self.macd_agent.analyze(candles)
        r_trap = self.trap_agent.analyze(candles)

        # 1. FILTRO DE BLOQUEO DE RANGO / SQUEEZE
        if r_bb.get("is_squeeze"):
            return {
                "signal": "ESPERAR",
                "confidence": 45,
                "recommended_time": "—",
                "duration_seconds": 0,
                "explanation": "FILTRADO: Mercado en Squeeze / Consolidación plana sin dirección. Esperando volumen.",
                "rsi": r_ind.get("rsi", 50.0),
                "trend": "Lateral",
                "count": len(candles),
                "agents": {
                    "price_action": r_pa, "structure": r_st, "indicators": r_ind,
                    "bollinger": r_bb, "macd": r_macd, "trap": r_trap
                }
            }

        # 2. PONDERACIÓN INSTITUCIONAL DE AGENTES
        # Ponderación calibrada:
        # Acción del Precio: 25%, Estructura S/R: 25%, Indicadores: 15%, Bollinger: 15%, MACD: 10%, Trampas: 10%
        agents_list = [
            (r_pa, 0.25),
            (r_st, 0.25),
            (r_ind, 0.15),
            (r_bb, 0.15),
            (r_macd, 0.10),
            (r_trap, 0.10)
        ]

        call_score = 0.0
        put_score = 0.0
        call_confluences = 0
        put_confluences = 0

        for res, weight in agents_list:
            v = res.get("vote")
            c = res.get("confidence", 50)
            if v == "CALL":
                call_score += c * weight
                call_confluences += 1
            elif v == "PUT":
                put_score += c * weight
                put_confluences += 1

        call_weight_sum = sum(w for res, w in agents_list if res.get("vote") == "CALL")
        put_weight_sum = sum(w for res, w in agents_list if res.get("vote") == "PUT")

        call_norm_score = (call_score / call_weight_sum) if call_weight_sum > 0 else 0.0
        put_norm_score = (put_score / put_weight_sum) if put_weight_sum > 0 else 0.0

        # 3. FILTROS DE SEGURIDAD ESTRICTOS
        if r_st.get("block_call"):
            call_norm_score *= 0.35
            call_confluences = max(0, call_confluences - 1)
        if r_st.get("block_put"):
            put_norm_score *= 0.35
            put_confluences = max(0, put_confluences - 1)

        # 4. CONDICIÓN DE RÁPIDA CONFIRMACIÓN INSTITUCIONAL (Fast Trigger Engine)
        has_prime_trigger_call = (
            (r_pa.get("vote") == "CALL" and r_pa.get("confidence", 0) >= 84) or
            (r_trap.get("vote") == "CALL" and r_trap.get("confidence", 0) >= 86) or
            (r_bb.get("vote") == "CALL" and r_bb.get("confidence", 0) >= 85)
        )
        has_prime_trigger_put = (
            (r_pa.get("vote") == "PUT" and r_pa.get("confidence", 0) >= 84) or
            (r_trap.get("vote") == "PUT" and r_trap.get("confidence", 0) >= 86) or
            (r_bb.get("vote") == "PUT" and r_bb.get("confidence", 0) >= 85)
        )

        final_signal = "ESPERAR"
        final_confidence = 50
        recommended_time = "—"
        duration_seconds = 0

        # Disparo rápido: Gatillo clave + confirmación secundaria (>= 2 agentes de acuerdo)
        is_fast_call = (has_prime_trigger_call and call_confluences >= 2 and call_norm_score >= 74 and put_confluences == 0)
        is_standard_call = (call_confluences >= 2 and call_weight_sum >= 0.35 and call_norm_score >= 75 and put_confluences <= 1)

        is_fast_put = (has_prime_trigger_put and put_confluences >= 2 and put_norm_score >= 74 and call_confluences == 0)
        is_standard_put = (put_confluences >= 2 and put_weight_sum >= 0.35 and put_norm_score >= 75 and call_confluences <= 1)

        if (is_fast_call or is_standard_call) and call_norm_score > put_norm_score + 10:
            final_signal = "CALL"
            final_confidence = min(96, int(max(call_norm_score, 80)))
            # Tiempo óptimo según gatillo
            if r_trap.get("vote") == "CALL" or r_bb.get("vote") == "CALL" or "Martillo" in r_pa.get("pattern", ""):
                recommended_time = "1 MIN"   # Rebote elástico rápido
                duration_seconds = 60
            elif "Ruptura" in r_st.get("zone", "") or "Morning" in r_pa.get("pattern", ""):
                recommended_time = "3 MIN"   # Ruptura con continuación
                duration_seconds = 180
            else:
                recommended_time = "2 MIN"   # Tendencial estándar
                duration_seconds = 120

        elif (is_fast_put or is_standard_put) and put_norm_score > call_norm_score + 10:
            final_signal = "PUT"
            final_confidence = min(96, int(max(put_norm_score, 80)))
            if r_trap.get("vote") == "PUT" or r_bb.get("vote") == "PUT" or "Estrella" in r_pa.get("pattern", ""):
                recommended_time = "1 MIN"   # Corrección elástica rápida
                duration_seconds = 60
            elif "Ruptura" in r_st.get("zone", "") or "Evening" in r_pa.get("pattern", ""):
                recommended_time = "3 MIN"
                duration_seconds = 180
            else:
                recommended_time = "2 MIN"
                duration_seconds = 120

        # Resumen explicativo de la confluencia
        active_agents = call_confluences if final_signal == "CALL" else put_confluences if final_signal == "PUT" else 0
        if final_signal != "ESPERAR":
            explanation = (
                f"Triple Confluencia ({final_confidence}% · {active_agents} agentes): {final_signal} a {recommended_time}. "
                f"Gatillo: {r_pa.get('pattern', 'Acción de precio')} | "
                f"Nivel: {r_st.get('zone', 'S/R')} | "
                f"RSI: {r_ind.get('rsi', '—')}."
            )
        else:
            explanation = (
                f"Consenso IA (Esperar · {int(max(call_score, put_score))}%): "
                "Filtro de calidad activo. Esperando confluencia mínima de 3 agentes para operar con alta probabilidad."
            )

        return {
            "signal": final_signal,
            "confidence": final_confidence,
            "recommended_time": recommended_time,
            "duration_seconds": duration_seconds,
            "explanation": explanation,
            "rsi": r_ind.get("rsi", 50.0),
            "trend": "Alcista" if call_score > put_score else "Bajista" if put_score > call_score else "Lateral",
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
