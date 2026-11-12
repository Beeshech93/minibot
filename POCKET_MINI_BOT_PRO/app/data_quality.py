"""
Data Quality and Visual Reconstruction Integrity Evaluator.
Ensures signals are only generated when screen visual quality is reliable.
"""
from typing import List, Dict, Any, Tuple
import numpy as np
from .candle_detector import Candle


class DataQualityEvaluator:
    """
    Evaluates visual reconstruction fidelity.
    Classifies data as 'Alta', 'Media', or 'Baja (Estimado Visual)'.
    """

    def evaluate(self, candles: List[Candle], frame_shape: Tuple[int, int]) -> Dict[str, Any]:
        """
        Assess candle count, distribution, spacing consistency, and wick sanity.
        """
        h, w = frame_shape
        count = len(candles)

        if count < 4:
            return {
                "quality": "Baja (Estimado Visual)",
                "confidence_multiplier": 0.40,
                "is_reliable": False,
                "reason": f"Muestra insuficiente ({count} velas detectadas, mínimo 4)."
            }

        if count < 8:
            return {
                "quality": "Media",
                "confidence_multiplier": 0.75,
                "is_reliable": True,
                "reason": f"Muestra moderada ({count} velas detectadas)."
            }

        # Check horizontal spacing consistency
        xs = [c.x for c in candles]
        diffs = np.diff(xs)
        std_spacing = float(np.std(diffs)) if len(diffs) > 1 else 0.0
        mean_spacing = float(np.mean(diffs)) if len(diffs) > 0 else 1.0
        cv_spacing = std_spacing / max(1.0, mean_spacing)

        # Check for abnormal wicks or visual corruption
        ranges = [c.range_size for c in candles]
        median_range = float(np.median(ranges))
        abnormal_candles = sum(1 for r in ranges if r > median_range * 4.5 or r < 1.0)
        abnormal_ratio = abnormal_candles / count

        if cv_spacing > 1.2 or abnormal_ratio > 0.25:
            return {
                "quality": "Media",
                "confidence_multiplier": 0.75,
                "is_reliable": True,
                "reason": "Varianza espacial en velas; calidad estimada aceptable."
            }

        return {
            "quality": "Alta",
            "confidence_multiplier": 1.0,
            "is_reliable": True,
            "reason": f"Reconstrucción óptima ({count} velas con espaciado uniforme)."
        }
