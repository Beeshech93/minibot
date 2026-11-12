"""
SQLite Database Layer for Pocket Mini Bot Pro.
Implements the required schema for assets, signals, outcomes, and settings.
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from .config import DB_PATH


class DatabaseManager:
    """Thread-safe SQLite database manager for signals, assets, outcomes, and settings."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Create tables if they do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Assets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL UNIQUE,
                    market_type TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            # 2. Signals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id INTEGER,
                    timeframe TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    indicator_values TEXT,
                    filters_passed TEXT,
                    technical_score INTEGER NOT NULL,
                    data_quality TEXT NOT NULL,
                    candle_reference TEXT,
                    reason TEXT,
                    FOREIGN KEY (asset_id) REFERENCES assets(id)
                )
            """)

            # 3. Outcomes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id INTEGER NOT NULL UNIQUE,
                    evaluation_horizon INTEGER NOT NULL,
                    outcome TEXT NOT NULL, -- 'WIN', 'LOSS', 'TIE', 'PENDING'
                    evaluated_at TEXT,
                    entry_price REAL,
                    exit_price REAL,
                    FOREIGN KEY (signal_id) REFERENCES signals(id)
                )
            """)

            # 4. Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT NOT NULL UNIQUE,
                    setting_value TEXT NOT NULL
                )
            """)

            # Pre-populate default asset if table empty
            cursor.execute("SELECT COUNT(*) FROM assets")
            if cursor.fetchone()[0] == 0:
                now_str = datetime.now().isoformat()
                cursor.execute(
                    "INSERT INTO assets (symbol, market_type, created_at) VALUES (?, ?, ?)",
                    ("EUR/USD (OTC)", "OTC", now_str)
                )
            conn.commit()

    # Asset operations
    def get_or_create_asset(self, symbol: str, market_type: str = "OTC") -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM assets WHERE symbol = ?", (symbol,))
            row = cursor.fetchone()
            if row:
                return row["id"]
            now_str = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO assets (symbol, market_type, created_at) VALUES (?, ?, ?)",
                (symbol, market_type, now_str)
            )
            conn.commit()
            return cursor.lastrowid

    # Signal operations
    def insert_signal(
        self,
        asset_id: int,
        timeframe: str,
        direction: str,
        indicator_values: Dict[str, Any],
        filters_passed: List[str],
        technical_score: int,
        data_quality: str,
        candle_reference: str,
        reason: str = "",
        timestamp: Optional[str] = None
    ) -> int:
        ts = timestamp or datetime.now().isoformat()
        ind_json = json.dumps(indicator_values)
        filt_json = json.dumps(filters_passed)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO signals (
                    asset_id, timeframe, direction, timestamp, indicator_values,
                    filters_passed, technical_score, data_quality, candle_reference, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                asset_id, timeframe, direction, ts, ind_json, filt_json,
                technical_score, data_quality, candle_reference, reason
            ))
            sig_id = cursor.lastrowid

            # Create default pending outcome record if it is CALL or PUT
            if direction in ("CALL", "PUT"):
                cursor.execute("""
                    INSERT OR IGNORE INTO outcomes (signal_id, evaluation_horizon, outcome, evaluated_at)
                    VALUES (?, ?, ?, ?)
                """, (sig_id, 60, "PENDING", None))

            conn.commit()
            return sig_id

    def update_outcome(
        self,
        signal_id: int,
        outcome: str,
        entry_price: Optional[float] = None,
        exit_price: Optional[float] = None
    ):
        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE outcomes
                SET outcome = ?, evaluated_at = ?, entry_price = ?, exit_price = ?
                WHERE signal_id = ?
            """, (outcome, now_str, entry_price, exit_price, signal_id))
            conn.commit()

    def get_recent_signals(self, limit: int = 15) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    s.id, s.timeframe, s.direction, s.timestamp, s.technical_score,
                    s.data_quality, s.reason, a.symbol, a.market_type,
                    COALESCE(o.outcome, '—') AS outcome
                FROM signals s
                LEFT JOIN assets a ON s.asset_id = a.id
                LEFT JOIN outcomes o ON s.id = o.signal_id
                ORDER BY s.id DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # Statistics operations
    def get_statistics(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM signals")
            total_signals = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM signals WHERE direction = 'CALL'")
            calls = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM signals WHERE direction = 'PUT'")
            puts = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM signals WHERE direction = 'WAIT'")
            waits = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM outcomes WHERE outcome = 'WIN'")
            wins = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM outcomes WHERE outcome = 'LOSS'")
            losses = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM outcomes WHERE outcome = 'PENDING'")
            pending = cursor.fetchone()[0]

            resolved = wins + losses
            win_rate = round((wins / resolved * 100.0), 1) if resolved > 0 else 0.0

            return {
                "total_signals": total_signals,
                "calls": calls,
                "puts": puts,
                "waits": waits,
                "wins": wins,
                "losses": losses,
                "pending": pending,
                "resolved": resolved,
                "win_rate": win_rate
            }

    # Settings operations
    def get_setting(self, key: str, default: str = "") -> str:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT setting_value FROM settings WHERE setting_key = ?", (key,))
            row = cursor.fetchone()
            return row["setting_value"] if row else default

    def set_setting(self, key: str, value: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO settings (setting_key, setting_value)
                VALUES (?, ?)
                ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value
            """, (key, str(value)))
            conn.commit()
