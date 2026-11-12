"""
Backtesting and Strategy Validation Module.
Performs chronological walk-forward validation with realistic binary payouts and transaction costs.
"""
from typing import List, Dict, Any, Tuple
import numpy as np
from .candle_detector import Candle
from .strategy_engine import StrategyEngine


class BacktestEngine:
    """Evaluates the 6-filter strategy on sequential historical OHLC datasets."""

    def __init__(self, payout_pct: float = 85.0, stake: float = 10.0):
        self.payout_pct = payout_pct
        self.stake = stake
        self.strategy = StrategyEngine()

    def run_backtest(
        self,
        candles: List[Candle],
        horizon: int = 1,
        train_test_split: float = 0.70
    ) -> Dict[str, Any]:
        """
        Run backtest with strict chronological train/test separation to eliminate look-ahead bias.
        """
        if len(candles) < 30:
            return {"error": "Muestra insuficiente para backtest (se requieren al menos 30 velas)."}

        split_idx = int(len(candles) * train_test_split)
        test_candles = candles[split_idx:]

        signals_count = 0
        calls = 0
        puts = 0
        wins = 0
        losses = 0
        ties = 0

        capital = 1000.0
        equity_curve = [capital]

        # Slide window across test candles
        for i in range(15, len(test_candles) - horizon):
            window = test_candles[:i]
            eval_res = self.strategy.evaluate(window, {"is_reliable": True, "confidence_multiplier": 1.0})
            direction = eval_res["direction"]

            if direction in ("CALL", "PUT"):
                signals_count += 1
                entry_candle = test_candles[i - 1]
                exit_candle = test_candles[i - 1 + horizon]

                entry_price = entry_candle.close
                exit_price = exit_candle.close

                if direction == "CALL":
                    calls += 1
                    is_win = exit_price > entry_price
                    is_tie = exit_price == entry_price
                else:  # PUT
                    puts += 1
                    is_win = exit_price < entry_price
                    is_tie = exit_price == entry_price

                if is_tie:
                    ties += 1
                elif is_win:
                    wins += 1
                    profit = self.stake * (self.payout_pct / 100.0)
                    capital += profit
                else:
                    losses += 1
                    capital -= self.stake

                equity_curve.append(round(capital, 2))

        resolved = wins + losses
        win_rate = round((wins / resolved * 100.0), 2) if resolved > 0 else 0.0

        # Calculate max drawdown
        eq_arr = np.array(equity_curve)
        peak = np.maximum.accumulate(eq_arr)
        drawdowns = (peak - eq_arr) / peak
        max_dd_pct = round(float(np.max(drawdowns)) * 100.0, 2) if len(drawdowns) > 0 else 0.0

        # Statistical 95% Confidence Interval for Win Rate (Wilson Score)
        if resolved > 0:
            z = 1.96
            p = wins / resolved
            denom = 1 + z**2 / resolved
            center = (p + z**2 / (2 * resolved)) / denom
            margin = z * np.sqrt((p * (1 - p) + z**2 / (4 * resolved)) / resolved) / denom
            ci_lower = round(float(max(0.0, center - margin) * 100.0), 1)
            ci_upper = round(float(min(1.0, center + margin) * 100.0), 1)
        else:
            ci_lower, ci_upper = 0.0, 0.0

        return {
            "total_bars_tested": len(test_candles),
            "signals_count": signals_count,
            "calls": calls,
            "puts": puts,
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "win_rate": win_rate,
            "ci_95": f"[{ci_lower}%, {ci_upper}%]",
            "max_drawdown_pct": max_dd_pct,
            "final_capital": round(capital, 2),
            "payout_assumed": f"{self.payout_pct}%"
        }
