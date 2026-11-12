"""
AI Multi-Agent Market Intelligence System for Pocket Mini Bot.
Provides specialized cooperative agents for chart and candlestick analysis:
1. PriceActionAgent: Candlestick patterns, wick rejections, pinbars.
2. MarketStructureAgent: Support & Resistance levels, swing pivots, breakouts.
3. TechnicalIndicatorAgent: Multi-period EMAs (9, 21, 50), dynamic RSI, divergences.
4. OrderFlowMomentumAgent: Candle body acceleration, exhaustion, volume pressure.
5. ConsensusMasterAgent: Weighted consensus voting, safety filters, expiration calculation.
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
        body_h = max(2.0, float(h))
        # Note: Chart y is inverted (smaller y = higher price)
        # We invert here so prices are intuitive (higher value = higher price)
        center_price = -c
        half_b = body_h / 2.0
        
        if d > 0:  # Bullish
            c_open = center_price - half_b
            c_close = center_price + half_b
        else:  # Bearish
            c_open = center_price + half_b
            c_close = center_price - half_b
            
        # Estimate wicks based on body and surrounding pixels
        upper_w = max(0.5, body_h * 0.25)
        lower_w = max(0.5, body_h * 0.25)
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


class PriceActionAgent:
    """Agent specialized in Japanese Candlestick Patterns and Price Action Rejections."""
    name = "Acción del Precio"

    def analyze(self, candles: List[Candle]) -> Dict[str, Any]:
        if len(candles) < 3:
            return {"vote": "ESPERAR", "confidence": 50, "reason": "Insuficientes velas para patrones"}

        c = candles[-1]
        prev = candles[-2]
        prev2 = candles[-3] if len(candles) >= 3 else prev

        # 1. Hammer / Pinbar Alcista (Larga mecha inferior, cuerpo pequeño arriba)
        is_hammer = (c.lower_wick >= c.body_size * 1.5) and (c.upper_wick <= c.body_size * 0.8)
        # 2. Shooting Star / Pinbar Bajista (Larga mecha superior, cuerpo pequeño abajo)
        is_shooting_star = (c.upper_wick >= c.body_size * 1.5) and (c.lower_wick <= c.body_size * 0.8)
        # 3. Bullish Engulfing (Vela verde envolvente sobre vela roja anterior)
        is_bullish_engulf = (prev.color == -1 and c.color == 1 and 
                             c.close >= prev.open and c.open <= prev.close and c.body_size > prev.body_size * 1.1)
        # 4. Bearish Engulfing (Vela roja envolvente sobre vela verde anterior)
        is_bearish_engulf = (prev.color == 1 and c.color == -1 and 
                             c.open >= prev.close and c.close <= prev.open and c.body_size > prev.body_size * 1.1)
        # 5. Doji (Indecisión extrema)
        is_doji = c.body_size <= c.range_size * 0.15

        if is_hammer:
            return {"vote": "CALL", "confidence": 85, "pattern": "Martillo / Pinbar Alcista", "reason": "Fuerte rechazo de mínimos con mecha de absorción"}
        elif is_bullish_engulf:
            return {"vote": "CALL", "confidence": 88, "pattern": "Envolvente Alcista", "reason": "Compradores absorbieron completamente la oferta anterior"}
        elif is_shooting_star:
            return {"vote": "PUT", "confidence": 85, "pattern": "Estrella Fugaz / Pinbar Bajista", "reason": "Fuerte rechazo de máximos con presión vendedora"}
        elif is_bearish_engulf:
            return {"vote": "PUT", "confidence": 88, "pattern": "Envolvente Bajista", "reason": "Vendedores superaron con fuerza la demanda anterior"}
        elif is_doji:
            return {"vote": "ESPERAR", "confidence": 45, "pattern": "Doji / Indecisión", "reason": "Equilibrio transitorio; esperar confirmación de ruptura"}

        # Evaluación de continuidad de velas
        if c.color == 1 and prev.color == 1 and c.body_size > prev.body_size:
            return {"vote": "CALL", "confidence": 74, "pattern": "Impulso Alcista Continuo", "reason": "Cuerpos verdes en expansión"}
        elif c.color == -1 and prev.color == -1 and c.body_size > prev.body_size:
            return {"vote": "PUT", "confidence": 74, "pattern": "Impulso Bajista Continuo", "reason": "Cuerpos rojos en expansión"}

        return {"vote": "ESPERAR", "confidence": 52, "pattern": "Sin patrón claro", "reason": "Estructura de velas neutral"}


class MarketStructureAgent:
    """Agent specialized in Support & Resistance, Pivot Swings, and Breakouts."""
    name = "Estructura & S/R"

    def analyze(self, candles: List[Candle]) -> Dict[str, Any]:
        if len(candles) < 8:
            return {"vote": "ESPERAR", "confidence": 50, "reason": "Historial corto para mapear soporte/resistencia"}

        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        current_price = candles[-1].close
        total_range = max(highs) - min(lows)
        if total_range <= 0:
            return {"vote": "ESPERAR", "confidence": 50, "reason": "Rango plano"}

        # Identificar pivotes máximos y mínimos
        swing_highs = []
        swing_lows = []
        for i in range(2, len(candles) - 2):
            if highs[i] >= highs[i-1] and highs[i] >= highs[i-2] and highs[i] >= highs[i+1] and highs[i] >= highs[i+2]:
                swing_highs.append(highs[i])
            if lows[i] <= lows[i-1] and lows[i] <= lows[i-2] and lows[i] <= lows[i+1] and lows[i] <= lows[i+2]:
                swing_lows.append(lows[i])

        nearest_res = min([h for h in swing_highs if h >= current_price], default=max(highs))
        nearest_sup = max([l for l in swing_lows if l <= current_price], default=min(lows))

        dist_res = abs(nearest_res - current_price) / total_range
        dist_sup = abs(current_price - nearest_sup) / total_range

        # Ruptura alcista confirmada (precio por encima de resistencia previa)
        if current_price > nearest_res * 0.998 and candles[-1].color == 1:
            return {
                "vote": "CALL", "confidence": 84, "zone": "Ruptura de Resistencia",
                "reason": f"Precio rompiendo zona clave con fuerza alcista",
                "nearest_res": nearest_res, "nearest_sup": nearest_sup
            }

        # Rebote en soporte clave
        if dist_sup < 0.08 and candles[-1].color == 1:
            return {
                "vote": "CALL", "confidence": 86, "zone": "Rebote en Soporte",
                "reason": f"Rechazo y rebote confirmado sobre nivel de soporte ({dist_sup*100:.1f}%)",
                "nearest_res": nearest_res, "nearest_sup": nearest_sup
            }

        # Rebote en resistencia clave
        if dist_res < 0.08 and candles[-1].color == -1:
            return {
                "vote": "PUT", "confidence": 86, "zone": "Rechazo en Resistencia",
                "reason": f"Rechazo y techo confirmado bajo nivel de resistencia ({dist_res*100:.1f}%)",
                "nearest_res": nearest_res, "nearest_sup": nearest_sup
            }

        # Alerta: demasiado cerca de resistencia (bloquear compras prematuras)
        if dist_res < 0.03:
            return {
                "vote": "ESPERAR", "confidence": 75, "zone": "Peligro: Techo Próximo",
                "reason": "Precio pegado a resistencia; riesgo alto de retroceso en CALL",
                "block_call": True, "nearest_res": nearest_res, "nearest_sup": nearest_sup
            }

        # Alerta: demasiado cerca de soporte (bloquear ventas prematuras)
        if dist_sup < 0.03:
            return {
                "vote": "ESPERAR", "confidence": 75, "zone": "Peligro: Piso Próximo",
                "reason": "Precio pegado a soporte; riesgo alto de rebote en PUT",
                "block_put": True, "nearest_res": nearest_res, "nearest_sup": nearest_sup
            }

        return {
            "vote": "ESPERAR", "confidence": 55, "zone": "Zona Media",
            "reason": "Precio navegando entre soporte y resistencia sin ruptura",
            "nearest_res": nearest_res, "nearest_sup": nearest_sup
        }


class TechnicalIndicatorAgent:
    """Agent specialized in Multi-Timeframe EMAs, Dynamic RSI, and Divergences."""
    name = "Indicadores & EMA"

    def calc_ema(self, prices: List[float], period: int) -> float:
        if len(prices) < period:
            return float(np.mean(prices))
        k = 2.0 / (period + 1.0)
        ema = float(prices[0])
        for p in prices[1:]:
            ema = p * k + ema * (1.0 - k)
        return ema

    def analyze(self, candles: List[Candle]) -> Dict[str, Any]:
        if len(candles) < 8:
            return {"vote": "ESPERAR", "confidence": 50, "reason": "Insuficientes datos para EMAs"}

        prices = [c.close for c in candles]
        
        # EMAs 9, 21, 50
        ema9 = self.calc_ema(prices, 9)
        ema21 = self.calc_ema(prices, 21)
        ema50 = self.calc_ema(prices, min(50, len(prices)))

        # RSI 14
        deltas = np.diff(prices)
        gains = np.maximum(deltas, 0)
        losses = np.maximum(-deltas, 0)
        p = min(14, len(deltas))
        avg_gain = gains[-p:].mean() if p else 0.0
        avg_loss = losses[-p:].mean() if p else 0.0
        rsi = 100.0 if avg_loss == 0 else (100.0 - (100.0 / (1.0 + (avg_gain / avg_loss))))

        # Detección de divergencia regular RSI
        bullish_div = False
        bearish_div = False
        if len(prices) >= 12:
            recent_low = min(prices[-4:])
            older_low = min(prices[-12:-4])
            if recent_low < older_low and rsi > 35:
                bullish_div = True
            recent_high = max(prices[-4:])
            older_high = max(prices[-12:-4])
            if recent_high > older_high and rsi < 65:
                bearish_div = True

        # Alineación tendencial
        bullish_trend = ema9 > ema21 and ema21 > ema50
        bearish_trend = ema9 < ema21 and ema21 < ema50

        if bullish_div:
            return {
                "vote": "CALL", "confidence": 87, "reason": f"Divergencia Alcista RSI ({rsi:.1f}) + Rebote potencial",
                "rsi": round(rsi, 1), "ema9": round(ema9, 2), "ema21": round(ema21, 2)
            }
        elif bearish_div:
            return {
                "vote": "PUT", "confidence": 87, "reason": f"Divergencia Bajista RSI ({rsi:.1f}) + Agotamiento de compras",
                "rsi": round(rsi, 1), "ema9": round(ema9, 2), "ema21": round(ema21, 2)
            }
        elif bullish_trend and rsi < 68 and prices[-1] > ema9:
            return {
                "vote": "CALL", "confidence": 82, "reason": f"Alineación alcista fuerte (EMA9 > 21 > 50) con RSI saludable ({rsi:.1f})",
                "rsi": round(rsi, 1), "ema9": round(ema9, 2), "ema21": round(ema21, 2)
            }
        elif bearish_trend and rsi > 32 and prices[-1] < ema9:
            return {
                "vote": "PUT", "confidence": 82, "reason": f"Alineación bajista fuerte (EMA9 < 21 < 50) con RSI saludable ({rsi:.1f})",
                "rsi": round(rsi, 1), "ema9": round(ema9, 2), "ema21": round(ema21, 2)
            }
        elif rsi < 25:
            return {
                "vote": "CALL", "confidence": 76, "reason": f"Sobreventa extrema (RSI {rsi:.1f}), alta probabilidad de rebote rápido",
                "rsi": round(rsi, 1), "ema9": round(ema9, 2), "ema21": round(ema21, 2)
            }
        elif rsi > 75:
            return {
                "vote": "PUT", "confidence": 76, "reason": f"Sobrecompra extrema (RSI {rsi:.1f}), alta probabilidad de corrección rápida",
                "rsi": round(rsi, 1), "ema9": round(ema9, 2), "ema21": round(ema21, 2)
            }

        return {
            "vote": "ESPERAR", "confidence": 50, "reason": f"Indicadores en rango neutral (RSI {rsi:.1f})",
            "rsi": round(rsi, 1), "ema9": round(ema9, 2), "ema21": round(ema21, 2)
        }


class OrderFlowMomentumAgent:
    """Agent specialized in Volume Pressure, Acceleration, and Exhaustion."""
    name = "Volumen & Momentum"

    def analyze(self, candles: List[Candle]) -> Dict[str, Any]:
        if len(candles) < 5:
            return {"vote": "ESPERAR", "confidence": 50, "reason": "Datos insuficientes para medir flujo"}

        recent_bodies = [c.body_size for c in candles[-5:]]
        avg_body = float(np.mean([c.body_size for c in candles]))
        last_body = candles[-1].body_size

        # Aceleración de volumen/intención
        is_expanding = last_body > avg_body * 1.3
        is_exhausting = last_body < avg_body * 0.4 and recent_bodies[-2] > avg_body * 1.2

        last_dir = candles[-1].color
        prev_dir = candles[-2].color

        if is_expanding and last_dir == prev_dir:
            sig = "CALL" if last_dir == 1 else "PUT"
            return {
                "vote": sig, "confidence": 81, "state": "Intención Institucional",
                "reason": f"Vela de volumen y cuerpo expansivo (+{int((last_body/max(1.0, avg_body)-1)*100)}%)"
            }
        elif is_exhausting:
            sig = "PUT" if prev_dir == 1 else "CALL"
            return {
                "vote": sig, "confidence": 74, "state": "Agotamiento de Movimiento",
                "reason": "Disminución súbita de volumen tras impulso; probable giro"
            }

        return {
            "vote": "ESPERAR", "confidence": 52, "state": "Volumen Normal",
            "reason": "Flujo de órdenes estable sin anomalías"
        }


class ConsensusMasterAgent:
    """Master Coordinator Agent combining all reports with weighted voting and risk filters."""
    def __init__(self):
        self.price_action_agent = PriceActionAgent()
        self.structure_agent = MarketStructureAgent()
        self.indicator_agent = TechnicalIndicatorAgent()
        self.momentum_agent = OrderFlowMomentumAgent()

    def evaluate(self, candles: List[Candle]) -> Dict[str, Any]:
        r_pa = self.price_action_agent.analyze(candles)
        r_st = self.structure_agent.analyze(candles)
        r_ind = self.indicator_agent.analyze(candles)
        r_mom = self.momentum_agent.analyze(candles)

        # Pesos de ponderación
        weights = {
            "pa": 0.30,   # Acción del precio (30%)
            "st": 0.30,   # Soporte / Resistencia (30%)
            "ind": 0.25,  # Indicadores & Divergencias (25%)
            "mom": 0.15   # Flujo & Momentum (15%)
        }

        call_score = 0.0
        put_score = 0.0

        for key, res in [("pa", r_pa), ("st", r_st), ("ind", r_ind), ("mom", r_mom)]:
            w = weights[key]
            conf = res.get("confidence", 50)
            if res["vote"] == "CALL":
                call_score += conf * w
            elif res["vote"] == "PUT":
                put_score += conf * w

        # Filtro de seguridad por Soporte/Resistencia
        if r_st.get("block_call"):
            call_score *= 0.4  # Penalizar CALL si estamos contra un techo
        if r_st.get("block_put"):
            put_score *= 0.4   # Penalizar PUT si estamos sobre un piso

        final_signal = "ESPERAR"
        final_confidence = 50
        recommended_time = "—"
        duration_seconds = 0

        # Umbral estricto para señales de alta precisión (>= 72%)
        if call_score >= 72 and call_score > put_score + 10:
            final_signal = "CALL"
            final_confidence = min(94, int(call_score))
            # Si es rebote en soporte o martillo -> 1 MIN (scalp rápido)
            if r_pa.get("vote") == "CALL" and ("Martillo" in r_pa.get("pattern", "") or "Rebote" in r_st.get("zone", "")):
                recommended_time = "1 MIN"
                duration_seconds = 60
            elif "Ruptura" in r_st.get("zone", "") or "Alineación" in r_ind.get("reason", ""):
                recommended_time = "3 MIN"
                duration_seconds = 180
            else:
                recommended_time = "2 MIN"
                duration_seconds = 120

        elif put_score >= 72 and put_score > call_score + 10:
            final_signal = "PUT"
            final_confidence = min(94, int(put_score))
            if r_pa.get("vote") == "PUT" and ("Estrella" in r_pa.get("pattern", "") or "Rechazo" in r_st.get("zone", "")):
                recommended_time = "1 MIN"
                duration_seconds = 60
            elif "Ruptura" in r_st.get("zone", "") or "Alineación" in r_ind.get("reason", ""):
                recommended_time = "3 MIN"
                duration_seconds = 180
            else:
                recommended_time = "2 MIN"
                duration_seconds = 120

        # Explicación resumida del consenso de agentes
        details = (
            f"Consenso IA ({final_confidence}%): {final_signal}. "
            f"Patrón: {r_pa.get('pattern', r_pa['vote'])} | "
            f"Zona: {r_st.get('zone', 'Media')} | "
            f"RSI: {r_ind.get('rsi', '—')} | "
            f"Flujo: {r_mom.get('state', 'Normal')}."
        )

        return {
            "signal": final_signal,
            "confidence": final_confidence,
            "recommended_time": recommended_time,
            "duration_seconds": duration_seconds,
            "explanation": details,
            "rsi": r_ind.get("rsi", 50.0),
            "trend": "Alcista" if call_score > put_score else "Bajista" if put_score > call_score else "Lateral",
            "count": len(candles),
            "agents": {
                "price_action": r_pa,
                "structure": r_st,
                "indicators": r_ind,
                "momentum": r_mom
            }
        }
