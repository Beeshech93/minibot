"""
Unit Tests for Signal Deduplication and Outcome Evaluation.
"""
import unittest
from pathlib import Path
from app.database import DatabaseManager
from app.signal_manager import SignalManager
from app.candle_detector import Candle


class TestSignalManager(unittest.TestCase):

    def setUp(self):
        self.test_db_path = Path("/tmp/test_signal_mgr.db")
        if self.test_db_path.exists():
            self.test_db_path.unlink()
        self.db = DatabaseManager(self.test_db_path)
        self.mgr = SignalManager(self.db)

    def tearDown(self):
        if self.test_db_path.exists():
            self.test_db_path.unlink()

    def test_deduplication_on_same_candle(self):
        candle = Candle(
            x=100.0, open=10.0, high=12.0, low=9.0, close=11.5,
            color=1, body_size=1.5, upper_wick=0.5, lower_wick=1.0, range_size=3.0
        )
        eval_res = {
            "direction": "CALL",
            "technical_score": 83,
            "reason": "Test Bullish",
            "filters_status": {"f1": {"call": True}}
        }

        # First dispatch: Should return a new signal
        sig1 = self.mgr.process_evaluation(eval_res, [candle], "EUR/USD (OTC)", "1m", "Alta")
        self.assertIsNotNone(sig1)

        # Immediate second dispatch on same candle: Must be deduplicated (return None)
        sig2 = self.mgr.process_evaluation(eval_res, [candle], "EUR/USD (OTC)", "1m", "Alta")
        self.assertIsNone(sig2)

    def test_wait_does_not_create_signal(self):
        candle = Candle(x=150.0, open=10.0, high=12.0, low=9.0, close=10.5, color=1, body_size=0.5, upper_wick=1.5, lower_wick=1.0, range_size=3.0)
        eval_res = {"direction": "WAIT", "technical_score": 33, "reason": "Wait test"}
        sig = self.mgr.process_evaluation(eval_res, [candle], "EUR/USD (OTC)", "1m", "Alta")
        self.assertIsNone(sig)


if __name__ == "__main__":
    unittest.main()
