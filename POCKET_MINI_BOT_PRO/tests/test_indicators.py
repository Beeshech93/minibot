"""
Unit Tests for Technical Indicators and Price Action.
"""
import unittest
from app.indicators import TechnicalIndicators
from app.candle_detector import Candle


class TestTechnicalIndicators(unittest.TestCase):

    def test_ema_calculation(self):
        prices = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0]
        ema = TechnicalIndicators.calc_ema(prices, 3)
        self.assertEqual(len(ema), len(prices))
        self.assertGreater(ema[-1], ema[0])

    def test_rsi_bounds(self):
        prices = [100.0 + i * 2.0 for i in range(20)]
        rsi_bull = TechnicalIndicators.calc_rsi(prices, 14)
        self.assertGreaterEqual(rsi_bull, 50.0)
        self.assertLessEqual(rsi_bull, 100.0)

        prices_down = [100.0 - i * 2.0 for i in range(20)]
        rsi_bear = TechnicalIndicators.calc_rsi(prices_down, 14)
        self.assertLessEqual(rsi_bear, 50.0)
        self.assertGreaterEqual(rsi_bear, 0.0)

    def test_macd_momentum(self):
        prices = [10.0 + i * 0.5 for i in range(35)]
        res = TechnicalIndicators.calc_macd(prices, 12, 26, 9)
        self.assertIn("macd", res)
        self.assertIn("signal", res)
        self.assertIn("hist", res)
        self.assertIn("strengthening", res)

    def test_bollinger_bands(self):
        prices = [100.0, 102.0, 99.0, 101.0, 103.0, 100.0, 102.0]
        upper, mid, lower = TechnicalIndicators.calc_bollinger(prices, 5, 2.0)
        self.assertGreater(upper, mid)
        self.assertLess(lower, mid)

    def test_atr(self):
        candles = [
            Candle(x=10, open=100.0, high=105.0, low=98.0, close=104.0, color=1, body_size=4.0, upper_wick=1.0, lower_wick=2.0, range_size=7.0),
            Candle(x=20, open=104.0, high=108.0, low=102.0, close=107.0, color=1, body_size=3.0, upper_wick=1.0, lower_wick=2.0, range_size=6.0),
            Candle(x=30, open=107.0, high=110.0, low=105.0, close=106.0, color=-1, body_size=1.0, upper_wick=3.0, lower_wick=1.0, range_size=5.0)
        ]
        atr = TechnicalIndicators.calc_atr(candles, 2)
        self.assertGreater(atr, 0.0)

    def test_hammer_detection(self):
        hammer = Candle(
            x=50, open=102.0, high=103.0, low=90.0, close=102.5,
            color=1, body_size=0.5, upper_wick=0.5, lower_wick=12.0, range_size=13.0
        )
        res = TechnicalIndicators.detect_price_action_patterns([hammer, hammer])
        self.assertEqual(res["bias"], "CALL")
        self.assertTrue(res["is_confirmed"])


if __name__ == "__main__":
    unittest.main()
