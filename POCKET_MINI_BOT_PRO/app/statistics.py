"""
Performance and Statistical Aggregator for Pocket Mini Bot Pro.
"""
from typing import Dict, Any, List
from .database import DatabaseManager


class StatisticsAggregator:
    """Aggregates win-rates, breakdown by asset, timeframe and session."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_summary(self) -> Dict[str, Any]:
        """Fetch general summary metrics from the SQLite database."""
        stats = self.db.get_statistics()
        has_sufficient_data = stats["resolved"] >= 5
        return {
            **stats,
            "has_sufficient_data": has_sufficient_data,
            "display_win_rate": f"{stats['win_rate']}%" if has_sufficient_data else "Esperando datos (mínimo 5)"
        }

    def get_asset_breakdown(self) -> List[Dict[str, Any]]:
        """Compute win rate by symbol."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    a.symbol,
                    COUNT(s.id) AS total,
                    SUM(CASE WHEN o.outcome = 'WIN' THEN 1 ELSE 0 END) AS wins,
                    SUM(CASE WHEN o.outcome = 'LOSS' THEN 1 ELSE 0 END) AS losses
                FROM signals s
                JOIN assets a ON s.asset_id = a.id
                LEFT JOIN outcomes o ON s.id = o.signal_id
                WHERE o.outcome IN ('WIN', 'LOSS')
                GROUP BY a.symbol
            """)
            rows = cursor.fetchall()
            result = []
            for r in rows:
                tot = r["wins"] + r["losses"]
                wr = round((r["wins"] / tot * 100.0), 1) if tot > 0 else 0.0
                result.append({
                    "symbol": r["symbol"],
                    "total": tot,
                    "wins": r["wins"],
                    "losses": r["losses"],
                    "win_rate": wr
                })
            return result
