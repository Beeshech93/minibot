from datetime import datetime
import numpy as np
import cv2
import mss
from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import QWidget, QApplication

def capture_region(rect):
    # Qt screen coordinates may differ on Retina; MSS uses physical pixels.
    mss_factory = getattr(mss, "MSS", None) or mss.mss
    with mss_factory() as sct:
        monitor = {
            "left": int(rect.x()), "top": int(rect.y()),
            "width": int(rect.width()), "height": int(rect.height())
        }
        shot = np.array(sct.grab(monitor))
    return cv2.cvtColor(shot, cv2.COLOR_BGRA2BGR)

def analyze_chart(image):
    """Heuristic visual candle-body detector; not an exchange price feed."""
    h, w = image.shape[:2]
    if h < 80 or w < 120:
        raise ValueError("La región seleccionada es demasiado pequeña.")

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # Common chart colors: green/turquoise bullish and red bearish.
    green = cv2.inRange(hsv, np.array([35, 45, 45]), np.array([100, 255, 255]))
    red1 = cv2.inRange(hsv, np.array([0, 55, 45]), np.array([12, 255, 255]))
    red2 = cv2.inRange(hsv, np.array([165, 55, 45]), np.array([180, 255, 255]))
    red = cv2.bitwise_or(red1, red2)

    kernel = np.ones((3, 3), np.uint8)
    green = cv2.morphologyEx(green, cv2.MORPH_OPEN, kernel)
    red = cv2.morphologyEx(red, cv2.MORPH_OPEN, kernel)

    # Aggregate colored pixels by x-column; use weighted vertical centers.
    xs, centers, directions = [], [], []
    for x in range(0, w, max(1, w // 180)):
        gys = np.where(green[:, x] > 0)[0]
        rys = np.where(red[:, x] > 0)[0]
        if len(gys) >= 5 and len(gys) > len(rys) * 1.25:
            ys = gys
            direction = 1
        elif len(rys) >= 5 and len(rys) > len(gys) * 1.25:
            ys = rys
            direction = -1
        else:
            continue
        if len(ys) > h * 0.35:  # likely a large UI region, not a candle
            continue
        xs.append(x)
        centers.append(float(np.median(ys)))
        directions.append(direction)

    # De-duplicate neighboring x-columns into approximate candle observations.
    candles = []
    for x, y, d in zip(xs, centers, directions):
        if not candles or x - candles[-1][0] > max(3, w // 100):
            candles.append([x, y, d])
        else:
            old = candles[-1]
            old[1] = (old[1] + y) / 2
            old[2] = d

    if len(candles) < 8:
        raise ValueError("No se detectaron suficientes cuerpos de velas. Selecciona solo el área del gráfico y verifica los colores.")

    # Chart y-axis is inverted: smaller y means visually higher price.
    prices = np.array([-c[1] for c in candles], dtype=float)
    dirs = np.array([c[2] for c in candles], dtype=float)
    delta = np.diff(prices)
    gains = np.maximum(delta, 0)
    losses = np.maximum(-delta, 0)
    period = min(14, len(delta))
    avg_gain = gains[-period:].mean() if period else 0
    avg_loss = losses[-period:].mean() if period else 0
    if avg_loss == 0:
        rsi = 100.0 if avg_gain > 0 else 50.0
    else:
        rsi = 100 - (100 / (1 + avg_gain / avg_loss))

    fast = np.mean(prices[-min(9, len(prices)):])
    slow = np.mean(prices[-min(21, len(prices)):])
    slope = prices[-1] - prices[max(0, len(prices)-6)]
    if fast > slow and slope > 0:
        trend = "ALCISTA"
    elif fast < slow and slope < 0:
        trend = "BAJISTA"
    else:
        trend = "LATERAL"

    # Conservative signal: agreement of trend, momentum and non-extreme RSI.
    bullish = trend == "ALCISTA" and dirs[-1] > 0 and rsi < 70
    bearish = trend == "BAJISTA" and dirs[-1] < 0 and rsi > 30
    if bullish:
        signal = "CALL"
        confidence = min(85, 55 + int(abs(fast - slow) / max(1, h) * 300) + int(max(0, 55-rsi) / 5))
    elif bearish:
        signal = "PUT"
        confidence = min(85, 55 + int(abs(fast - slow) / max(1, h) * 300) + int(max(0, rsi-45) / 5))
    else:
        signal, confidence = "ESPERAR", 50

    # Calculate recommended expiration timeframe based on momentum and volatility
    volatility = float(np.std(delta)) if len(delta) > 0 else 1.0
    diff_val = abs(fast - slow) / max(1.0, float(h))

    if signal in ("CALL", "PUT"):
        if diff_val > 0.05 or volatility > 12:
            recommended_time = "1 MIN"
            duration_seconds = 60
        elif diff_val > 0.025 or volatility > 6:
            recommended_time = "2 MIN"
            duration_seconds = 120
        else:
            recommended_time = "5 MIN"
            duration_seconds = 300
    else:
        recommended_time = "—"
        duration_seconds = 0

    explanation = (
        f"Señal {signal} a {recommended_time}. Tendencia: {trend} | RSI: {rsi:.1f}. "
        f"Cuerpos detectados: {len(candles)}."
    )
    return {
        "signal": signal, "confidence": confidence, "rsi": round(rsi, 1),
        "trend": trend, "count": len(candles),
        "recommended_time": recommended_time,
        "duration_seconds": duration_seconds,
        "explanation": explanation,
        "time": datetime.now().strftime("%H:%M:%S")
    }

class RegionPicker(QWidget):
    selected = Signal(object)
    cancelled = Signal()
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
        else:
            self.setWindowState(Qt.WindowFullScreen)
        self.setCursor(Qt.CrossCursor)
        self.setWindowOpacity(0.28)
        self.origin = None
        self.current = QRect()
        self.setStyleSheet("background:black;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 90))
        painter.setPen(QPen(QColor(40, 220, 150), 3))
        painter.drawRect(self.current)

    def mousePressEvent(self, event):
        self.origin = event.position().toPoint()
        self.current = QRect(self.origin, self.origin)
        self.update()

    def mouseMoveEvent(self, event):
        if self.origin is not None:
            self.current = QRect(self.origin, event.position().toPoint()).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if self.origin is None:
            return
        rect = self.current.normalized()
        self.close()
        if rect.width() > 80 and rect.height() > 60:
            self.selected.emit(rect)
        else:
            self.cancelled.emit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
            self.cancelled.emit()
