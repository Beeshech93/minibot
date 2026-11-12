"""
Unit Tests for SQLite Database Operations.
"""
import unittest
from pathlib import Path
from app.database import DatabaseManager


class TestDatabaseManager(unittest.TestCase):

    def setUp(self):
        self.test_db_path = Path("/tmp/test_pocket_signals.db")
        if self.test_db_path.exists():
            self.test_db_path.unlink()
        self.db = DatabaseManager(self.test_db_path)

    def tearDown(self):
        if self.test_db_path.exists():
            self.test_db_path.unlink()

    def test_asset_creation(self):
        a_id = self.db.get_or_create_asset("EUR/USD (OTC)", "OTC")
        self.assertGreater(a_id, 0)
        # Re-fetching returns same id
        a_id2 = self.db.get_or_create_asset("EUR/USD (OTC)", "OTC")
        self.assertEqual(a_id, a_id2)

    def test_insert_and_retrieve_signal(self):
        a_id = self.db.get_or_create_asset("GBP/USD (OTC)", "OTC")
        sig_id = self.db.insert_signal(
            asset_id=a_id,
            timeframe="1m",
            direction="CALL",
            indicator_values={"rsi": 55.4},
            filters_passed=["f1_trend", "f2_rsi", "f3_macd", "f4_candle", "f5_sr"],
            technical_score=83,
            data_quality="Alta",
            candle_reference="Ref_1",
            reason="Test signal"
        )
        self.assertGreater(sig_id, 0)

        signals = self.db.get_recent_signals(limit=5)
        self.assertGreaterEqual(len(signals), 1)
        self.assertEqual(signals[0]["direction"], "CALL")
        self.assertEqual(signals[0]["outcome"], "PENDING")

    def test_update_outcome(self):
        a_id = self.db.get_or_create_asset("USD/JPY (OTC)", "OTC")
        sig_id = self.db.insert_signal(
            asset_id=a_id, timeframe="1m", direction="PUT",
            indicator_values={}, filters_passed=[], technical_score=83,
            data_quality="Alta", candle_reference="Ref_2"
        )
        self.db.update_outcome(sig_id, "WIN", entry_price=150.0, exit_price=149.0)

        stats = self.db.get_statistics()
        self.assertEqual(stats["wins"], 1)
        self.assertEqual(stats["win_rate"], 100.0)

    def test_settings_persistence(self):
        self.db.set_setting("sound_enabled", "1")
        val = self.db.get_setting("sound_enabled")
        self.assertEqual(val, "1")


if __name__ == "__main__":
    unittest.main()

