"""
Signal Manager for Pocket Mini Bot Pro.
Handles signal deduplication, persistence, and pending outcome resolution.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from .database import DatabaseManager
from .candle_detector import Candle


class SignalManager:
    """Manages trading signals, prevents duplicate alerts, and evaluates outcomes."""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.last_signal_time: Optional[datetime] = None
        self.last_candle_x: Optional[float] = None
        self.active_signals: List[Dict[str, Any]] = []

    def process_evaluation(
        self,
        eval_result: Dict[str, Any],
        candles: List[Candle],
        asset_symbol: str,
        timeframe: str,
        data_quality_label: str
    ) -> Optional[Dict[str, Any]]:
        """
        Process a new strategy evaluation.
        Only emit a new CALL/PUT signal if not duplicate for the current candle.
        """
        if not candles:
            return None

        current_candle = candles[-1]
        direction = eval_result["direction"]

        # Deduplication check: Avoid multiple signals on the same candle
        is_same_candle = (self.last_candle_x is not None) and (abs(current_candle.x - self.last_candle_x) < 4.0)
        
        now = datetime.now()
        timestamp_str = now.strftime("%H:%M:%S")

        if direction in ("CALL", "PUT"):
            if is_same_candle:
                # Same candle, do not duplicate audio or alert
                return None

            self.last_candle_x = current_candle.x
            self.last_signal_time = now

            asset_id = self.db.get_or_create_asset(asset_symbol, eval_result.get("market_type", "OTC"))
            filters_passed = [
                k for k, v in eval_result.get("filters_status", {}).items()
                if (direction == "CALL" and v.get("call")) or (direction == "PUT" and v.get("put"))
            ]

            sig_id = self.db.insert_signal(
                asset_id=asset_id,
                timeframe=timeframe,
                direction=direction,
                indicator_values=eval_result.get("indicator_values", {}),
                filters_passed=filters_passed,
                technical_score=eval_result["technical_score"],
                data_quality=data_quality_label,
                candle_reference=f"Candle_X_{int(current_candle.x)}",
                reason=eval_result["reason"],
                timestamp=now.isoformat()
            )

            record = {
                "id": sig_id,
                "direction": direction,
                "timeframe": timeframe,
                "timestamp": timestamp_str,
                "score": eval_result["technical_score"],
                "reason": eval_result["reason"],
                "asset": asset_symbol,
                "entry_price": current_candle.close,
                "created_at": now
            }
            self.active_signals.append(record)
            return record

        return None

    def check_outcomes(self, current_price: float):
        """
        Check active signals and resolve their WIN/LOSS outcome once their horizon passes.
        """
        now = datetime.now()
        unresolved = []
        for sig in self.active_signals:
            elapsed = (now - sig["created_at"]).total_seconds()
            # If 60 seconds passed for 1m signal
            if elapsed >= 58.0:
                entry = sig["entry_price"]
                diff = current_price - entry
                if sig["direction"] == "CALL":
                    outcome = "WIN" if diff > 0.05 else "LOSS" if diff < -0.05 else "TIE"
                else:  # PUT
                    outcome = "WIN" if diff < -0.05 else "LOSS" if diff > 0.05 else "TIE"

                self.db.update_outcome(
                    signal_id=sig["id"],
                    outcome=outcome,
                    entry_price=entry,
                    exit_price=current_price
                )
            else:
                unresolved.append(sig)
        self.active_signals = unresolved

