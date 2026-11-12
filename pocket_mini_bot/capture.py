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
    """
    Advanced Computer Vision Candlestick Reconstruction:
    - Dual-Space Adaptive Segmentation (HSV + RGB Differential)
    - Connected Component Contour Geometry (exact body + wick extraction)
    - Fallback column-slice projection for extreme chart conditions
    """
    h, w = image.shape[:2]
    if h < 60 or w < 80:
        raise ValueError("La región seleccionada es demasiado pequeña.")

    # 1. Dual-Space Segmentation (illumination and theme invariant)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Green candle masks (Bullish)
    hsv_green = cv2.inRange(hsv, np.array([32, 35, 35]), np.array([105, 255, 255]))
    diff_green = (image[:, :, 1].astype(np.int16) - np.maximum(image[:, :, 0], image[:, :, 2])) > 12
    green_mask = cv2.bitwise_or(hsv_green, (diff_green.astype(np.uint8) * 255))
    
    # Red candle masks (Bearish)
    hsv_red1 = cv2.inRange(hsv, np.array([0, 35, 35]), np.array([16, 255, 255]))
    hsv_red2 = cv2.inRange(hsv, np.array([160, 35, 35]), np.array([180, 255, 255]))
    diff_red = (image[:, :, 2].astype(np.int16) - np.maximum(image[:, :, 0], image[:, :, 1])) > 12
    red_mask = cv2.bitwise_or(cv2.bitwise_or(hsv_red1, hsv_red2), (diff_red.astype(np.uint8) * 255))

    kernel = np.ones((3, 3), np.uint8)
    green_clean = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, kernel)
    red_clean = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)

    # 2. Contour Extraction for Millimeter-Accurate Candlesticks
    raw_obs = []

    def extract_from_mask(mask, direction):
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            bx, by, bw, bh = cv2.boundingRect(c)
            # Filter noise and huge UI containers (e.g. green CALL / red PUT buttons)
            if bh < 4 or bw > max(40, int(w * 0.10)) or bh > h * 0.80:
                continue
            roi = mask[by:by+bh, bx:bx+bw]
            row_widths = np.sum(roi > 0, axis=1)
            thresh = max(2, int(np.max(row_widths) * 0.55))
            body_rows = np.where(row_widths >= thresh)[0]
            if len(body_rows) > 0:
                body_top = float(by + body_rows[0])
                body_bottom = float(by + body_rows[-1])
            else:
                body_top = float(by + bh * 0.2)
                body_bottom = float(by + bh * 0.8)

            center_y = (body_top + body_bottom) / 2.0
            height_val = max(2.5, body_bottom - body_top)
            center_x = float(bx + bw / 2.0)
            wick_top = float(by)
            wick_bot = float(by + bh)

            raw_obs.append((center_x, center_y, direction, height_val, wick_top, wick_bot))

    extract_from_mask(green_clean, 1)
    extract_from_mask(red_clean, -1)

    # 3. Sort contours chronologically from left to right
    raw_obs.sort(key=lambda item: item[0])

    # De-duplicate close observations
    c_xs, c_centers, c_dirs, c_heights, c_tops, c_bots = [], [], [], [], [], []
    for x, y, d, h_val, ty, by in raw_obs:
        if not c_xs or x - c_xs[-1] > max(3.0, w / 120.0):
            c_xs.append(x)
            c_centers.append(y)
            c_dirs.append(d)
            c_heights.append(h_val)
            c_tops.append(ty)
            c_bots.append(by)
        else:
            c_centers[-1] = (c_centers[-1] + y) / 2.0
            c_dirs[-1] = d
            c_heights[-1] = max(c_heights[-1], h_val)
            c_tops[-1] = min(c_tops[-1], ty)
            c_bots[-1] = max(c_bots[-1], by)

    # 4. Fallback Column Projection if contours were sparse (< 4)
    if len(c_xs) < 4:
        c_xs, c_centers, c_dirs, c_heights, c_tops, c_bots = [], [], [], [], [], []
        step = max(1, w // 180)
        for x in range(0, w, step):
            gys = np.where(green_clean[:, x] > 0)[0]
            rys = np.where(red_clean[:, x] > 0)[0]
            if len(gys) >= 3 and len(gys) > len(rys) * 1.15:
                ys = gys
                direction = 1
            elif len(rys) >= 3 and len(rys) > len(gys) * 1.15:
                ys = rys
                direction = -1
            else:
                continue
            if len(ys) > h * 0.45:
                continue
            x_f = float(x)
            y_f = float(np.median(ys))
            h_f = float(len(ys))
            ty_f = float(np.min(ys))
            by_f = float(np.max(ys))
            if not c_xs or x_f - c_xs[-1] > max(3.0, w / 100.0):
                c_xs.append(x_f)
                c_centers.append(y_f)
                c_dirs.append(direction)
                c_heights.append(h_f)
                c_tops.append(ty_f)
                c_bots.append(by_f)
            else:
                c_centers[-1] = (c_centers[-1] + y_f) / 2.0
                c_dirs[-1] = direction
                c_heights[-1] = max(c_heights[-1], h_f)
                c_tops[-1] = min(c_tops[-1], ty_f)
                c_bots[-1] = max(c_bots[-1], by_f)

    if len(c_xs) < 4:
        raise ValueError("No se detectaron suficientes velas. Asegúrate de encuadrar las velas del gráfico.")

    # Convert to structured candles and evaluate with Bayesian Multi-Agent Engine
    candles = extract_candles_from_data(c_xs, c_centers, c_dirs, c_heights, c_tops, c_bots)
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
