"""
Candlestick Visual Extraction Engine.
Extracts candle bodies, wicks, direction and geometric prices using Computer Vision.
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np
import cv2


@dataclass
class Candle:
    x: float
    open: float
    high: float
    low: float
    close: float
    color: int  # +1 for bullish (green), -1 for bearish (red)
    body_size: float
    upper_wick: float
    lower_wick: float
    range_size: float
    px_body_top: float = 0.0
    px_body_bottom: float = 0.0
    px_wick_top: float = 0.0
    px_wick_bottom: float = 0.0


class CandleDetector:
    """Detects and reconstructs candlestick entities from visual chart regions."""

    def __init__(self):
        # Morphological kernel for noise filtering
        self.kernel = np.ones((3, 3), np.uint8)

    def extract_candles(self, chart_image: np.ndarray) -> List[Candle]:
        """
        Segment bullish and bearish candlesticks, compute wick/body geometry,
        and return chronologically ordered Candles (left to right).
        """
        h, w = chart_image.shape[:2]
        if h < 30 or w < 40:
            return []

        hsv = cv2.cvtColor(chart_image, cv2.COLOR_BGR2HSV)

        # 1. Bullish Candle Mask (Green)
        hsv_green = cv2.inRange(hsv, np.array([32, 35, 35]), np.array([105, 255, 255]))
        diff_green = (chart_image[:, :, 1].astype(np.int16) - np.maximum(chart_image[:, :, 0], chart_image[:, :, 2])) > 12
        green_mask = cv2.bitwise_or(hsv_green, (diff_green.astype(np.uint8) * 255))
        green_clean = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, self.kernel)

        # 2. Bearish Candle Mask (Red)
        hsv_red1 = cv2.inRange(hsv, np.array([0, 35, 35]), np.array([16, 255, 255]))
        hsv_red2 = cv2.inRange(hsv, np.array([160, 35, 35]), np.array([180, 255, 255]))
        diff_red = (chart_image[:, :, 2].astype(np.int16) - np.maximum(chart_image[:, :, 0], chart_image[:, :, 1])) > 12
        red_mask = cv2.bitwise_or(cv2.bitwise_or(hsv_red1, hsv_red2), (diff_red.astype(np.uint8) * 255))
        red_clean = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, self.kernel)

        raw_candidates = []

        def process_mask(mask: np.ndarray, direction: int):
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                bx, by, bw, bh = cv2.boundingRect(cnt)
                # Filter noise and huge container borders
                if bh < 4 or bw > max(45, int(w * 0.12)) or bh > h * 0.85:
                    continue

                roi = mask[by:by + bh, bx:bx + bw]
                row_widths = np.sum(roi > 0, axis=1)
                if len(row_widths) == 0:
                    continue

                max_width = np.max(row_widths)
                thresh = max(2, int(max_width * 0.52))
                body_rows = np.where(row_widths >= thresh)[0]

                if len(body_rows) > 0:
                    body_top = float(by + body_rows[0])
                    body_bottom = float(by + body_rows[-1])
                else:
                    body_top = float(by + bh * 0.25)
                    body_bottom = float(by + bh * 0.75)

                wick_top = float(by)
                wick_bottom = float(by + bh)
                center_x = float(bx + bw / 2.0)

                raw_candidates.append({
                    "x": center_x,
                    "direction": direction,
                    "body_top": body_top,
                    "body_bottom": body_bottom,
                    "wick_top": wick_top,
                    "wick_bottom": wick_bottom,
                    "width": bw
                })

        process_mask(green_clean, 1)
        process_mask(red_clean, -1)

        if not raw_candidates:
            return []

        # Sort left to right
        raw_candidates.sort(key=lambda item: item["x"])

        # Cluster items within 4 pixels horizontal distance
        clustered = []
        for cand in raw_candidates:
            if not clustered or (cand["x"] - clustered[-1]["x"] > 4.5):
                clustered.append(cand)
            else:
                last = clustered[-1]
                # Merge wicks and take larger body
                last["wick_top"] = min(last["wick_top"], cand["wick_top"])
                last["wick_bottom"] = max(last["wick_bottom"], cand["wick_bottom"])
                last["body_top"] = min(last["body_top"], cand["body_top"])
                last["body_bottom"] = max(last["body_bottom"], cand["body_bottom"])

        candles: List[Candle] = []
        for item in clustered:
            body_h = max(2.5, item["body_bottom"] - item["body_top"])
            # Note: Screen Y is inverted (0 is top = highest price)
            # We map -Y so higher screen coordinate = higher numeric price
            price_body_top = -item["body_top"]
            price_body_bottom = -item["body_bottom"]
            price_wick_top = -item["wick_top"]
            price_wick_bottom = -item["wick_bottom"]

            if item["direction"] > 0:  # Bullish (Green)
                c_open = price_body_bottom
                c_close = price_body_top
            else:  # Bearish (Red)
                c_open = price_body_top
                c_close = price_body_bottom

            c_high = price_wick_top
            c_low = price_wick_bottom
            rng = max(1.0, c_high - c_low)

            upper_wick = max(0.1, c_high - max(c_open, c_close))
            lower_wick = max(0.1, min(c_open, c_close) - c_low)

            candles.append(Candle(
                x=item["x"],
                open=c_open,
                high=c_high,
                low=c_low,
                close=c_close,
                color=item["direction"],
                body_size=body_h,
                upper_wick=upper_wick,
                lower_wick=lower_wick,
                range_size=rng,
                px_body_top=item["body_top"],
                px_body_bottom=item["body_bottom"],
                px_wick_top=item["wick_top"],
                px_wick_bottom=item["wick_bottom"]
            ))

        return candles
