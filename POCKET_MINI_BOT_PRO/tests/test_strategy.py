"""
Unit Tests for the Six-Filter Strategy Engine.
"""
import unittest
from app.strategy_engine import StrategyEngine
from app.candle_detector import Candle


class TestStrategyEngine(unittest.TestCase):

    def setUp(self):
        self.strategy = StrategyEngine(market_type="OTC")

    def test_insufficient_candles_waits(self):
        candles = [
            Candle(x=10, open=100.0, high=102.0, low=99.0, close=101.0, color=1, body_size=1.0, upper_wick=1.0, lower_wick=1.0, range_size=3.0)
        ]
        quality = {"is_reliable": True, "confidence_multiplier": 1.0}
        res = self.strategy.evaluate(candles, quality)
        self.assertEqual(res["direction"], "WAIT")
        self.assertIn("insuficiente", res["reason"].lower())

    def test_unreliable_data_quality_waits(self):
        candles = [
            Candle(x=10*i, open=100.0+i, high=102.0+i, low=99.0+i, close=101.0+i, color=1, body_size=1.0, upper_wick=1.0, lower_wick=1.0, range_size=3.0)
            for i in range(10)
        ]
        quality = {"is_reliable": False, "reason": "Demasiado ruido visual"}
        res = self.strategy.evaluate(candles, quality)
        self.assertEqual(res["direction"], "WAIT")

    def test_filter_tally_and_score(self):
        # Create a series of bullish candles
        candles = [
            Candle(x=10*i, open=100.0+i*2.0, high=103.0+i*2.0, low=99.0+i*2.0, close=102.5+i*2.0, color=1, body_size=2.5, upper_wick=0.5, lower_wick=1.0, range_size=4.0)
            for i in range(15)
        ]
        quality = {"is_reliable": True, "confidence_multiplier": 1.0}
        res = self.strategy.evaluate(candles, quality)
        self.assertIn(res["direction"], ["CALL", "PUT", "WAIT"])
        self.assertGreaterEqual(res["technical_score"], 0)
        self.assertLessEqual(res["technical_score"], 100)
        self.assertIn("filters_status", res)
        self.assertEqual(len(res["filters_status"]), 6)


if __name__ == "__main__":
    unittest.main()
