"""
Screen Capture Engine for macOS (Intel & Apple Silicon).
Handles Retina display scaling, coordinate translation, and graceful error recovery.
"""
import sys
import numpy as np
import cv2
import mss
from typing import Optional, Tuple, Dict, Any
from PySide6.QtCore import QRect, QPoint, Qt
from PySide6.QtGui import QGuiApplication


class CaptureEngine:
    """
    Robust macOS screen capture engine with Retina display adaptation.
    Translates Qt logical coordinates to MSS physical pixel monitors.
    """

    def __init__(self):
        self._mss_factory = getattr(mss, "MSS", None) or mss.mss
        self.selected_rect: Optional[QRect] = None
        self.device_pixel_ratio: float = 1.0
        self._update_scaling()

    def _update_scaling(self):
        """Detect macOS Retina display scale factor."""
        primary_screen = QGuiApplication.primaryScreen()
        if primary_screen:
            self.device_pixel_ratio = float(primary_screen.devicePixelRatio())
        else:
            self.device_pixel_ratio = 2.0 if sys.platform == "darwin" else 1.0

    def set_region(self, rect: QRect):
        """Set the user-selected logical capture region."""
        self._update_scaling()
        self.selected_rect = rect

    def get_physical_monitor(self, rect: QRect) -> Dict[str, int]:
        """Convert Qt logical coordinates to MSS physical monitor coordinates."""
        dpr = self.device_pixel_ratio
        left = int(rect.x() * dpr)
        top = int(rect.y() * dpr)
        width = int(rect.width() * dpr)
        height = int(rect.height() * dpr)
        return {"left": left, "top": top, "width": width, "height": height}

    def capture(self) -> Optional[np.ndarray]:
        """
        Capture the current selected region.
        Returns a BGR NumPy array (OpenCV format) or None on failure.
        """
        if not self.selected_rect or self.selected_rect.isEmpty():
            return None

        try:
            with self._mss_factory() as sct:
                monitor = self.get_physical_monitor(self.selected_rect)
                raw_shot = sct.grab(monitor)
                frame_rgba = np.array(raw_shot, dtype=np.uint8)
                if frame_rgba.size == 0:
                    return None
                frame_bgr = cv2.cvtColor(frame_rgba, cv2.COLOR_BGRA2BGR)
                return frame_bgr
        except Exception as e:
            # Handle display server / permission / coordinate errors gracefully
            return None

    def capture_fullscreen(self) -> Optional[np.ndarray]:
        """Capture the primary monitor full screen."""
        try:
            with self._mss_factory() as sct:
                monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                raw_shot = sct.grab(monitor)
                frame_rgba = np.array(raw_shot, dtype=np.uint8)
                return cv2.cvtColor(frame_rgba, cv2.COLOR_BGRA2BGR)
        except Exception:
            return None

