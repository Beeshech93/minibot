from datetime import datetime
import numpy as np
import cv2
import mss
from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import QWidget, QApplication

try:
    from ai_agents import extract_candles_from_data, ConsensusMasterAgent
except ImportError:
    from pocket_mini_bot.ai_agents import extract_candles_from_data, ConsensusMasterAgent

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

    # Aggregate colored pixels by x-column; extract centers and heights
    xs, centers, directions, heights = [], [], [], []
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
        heights.append(float(len(ys)))

    # De-duplicate neighboring x-columns into approximate candle observations.
    c_xs, c_centers, c_dirs, c_heights = [], [], [], []
    for x, y, d, h_val in zip(xs, centers, directions, heights):
        if not c_xs or x - c_xs[-1] > max(3, w // 100):
            c_xs.append(x)
            c_centers.append(y)
            c_dirs.append(d)
            c_heights.append(h_val)
        else:
            c_centers[-1] = (c_centers[-1] + y) / 2.0
            c_dirs[-1] = d
            c_heights[-1] = max(c_heights[-1], h_val)

    if len(c_xs) < 8:
        raise ValueError("No se detectaron suficientes cuerpos de velas. Selecciona solo el área del gráfico y verifica los colores.")

    # Convert to structured candles and run Multi-Agent consensus evaluation
    candles = extract_candles_from_data(c_xs, c_centers, c_dirs, c_heights)
    master = ConsensusMasterAgent()
    res = master.evaluate(candles)
    res["time"] = datetime.now().strftime("%H:%M:%S")
    return res

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
