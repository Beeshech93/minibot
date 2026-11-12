"""
Chart Detector and ROI Boundary Preprocessing.
Filters out non-chart broker UI containers (buttons, balance, menu) and verifies chart animation.
"""
import numpy as np
import cv2
from typing import Tuple, Optional


class ChartDetector:
    """Preprocesses cropped images to locate the active candlestick plotting canvas."""

    def __init__(self):
        self._prev_gray: Optional[np.ndarray] = None

    def refine_chart_roi(self, image: np.ndarray) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
        """
        Crop away broker UI borders (top header, right trading buttons, left tools).
        Returns cropped_image, (x_offset, y_offset, crop_w, crop_h).
        """
        h, w = image.shape[:2]
        if h < 40 or w < 60:
            return image, (0, 0, w, h)

        # Optimized Pocket Option chart margin cropping:
        # Top 8% (tabs/pair name), Right 27% (strictly excludes CALL/PUT buttons, payout & timer), Left 5% (tool menu), Bottom 11% (time scale)
        y_start = int(h * 0.08)
        y_end = int(h * 0.89)
        x_start = int(w * 0.05)
        x_end = int(w * 0.73)

        if (x_end - x_start) < 40 or (y_end - y_start) < 40:
            return image, (0, 0, w, h)

        roi = image[y_start:y_end, x_start:x_end]
        return roi, (x_start, y_start, x_end - x_start, y_end - y_start)

    def detect_chart_movement(self, image: np.ndarray, threshold: float = 0.5) -> bool:
        """
        Detect whether the price chart is moving between consecutive frames.
        Returns True if movement detected, False if static/paused.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if self._prev_gray is None or self._prev_gray.shape != gray.shape:
            self._prev_gray = gray
            return True

        diff = cv2.absdiff(self._prev_gray, gray)
        mean_diff = float(np.mean(diff))
        self._prev_gray = gray
        return mean_diff > threshold

