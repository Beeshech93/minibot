"""
Risk Management Engine for Pocket Mini Bot Pro.
Enforces strict capital protection, loss limits, and Anti-Martingale rules.
NEVER executes trades automatically.
"""
from typing import Dict, Any
from .config import RISK_DEFAULTS


class RiskManager:
    """Calculates manual risk thresholds and pauses alerts when limits are breached."""

    def __init__(
        self,
        capital: float = RISK_DEFAULTS["initial_capital"],
        max_consecutive_losses: int = RISK_DEFAULTS["max_consecutive_losses"],
        daily_loss_limit_pct: float = RISK_DEFAULTS["daily_loss_limit_pct"]
    ):
        self.capital = capital
        self.max_consecutive_losses = max_consecutive_losses
        self.daily_loss_limit_pct = daily_loss_limit_pct
        self.consecutive_losses: int = 0
        self.daily_pnl: float = 0.0
        self.is_paused: bool = False
        self.pause_reason: str = ""

    def register_trade_outcome(self, outcome: str, profit_loss: float):
        """Update risk metrics after an outcome is resolved."""
        if outcome == "LOSS":
            self.consecutive_losses += 1
            self.daily_pnl += profit_loss
        elif outcome == "WIN":
            self.consecutive_losses = 0
            self.daily_pnl += profit_loss

        # Check circuit breakers
        if self.consecutive_losses >= self.max_consecutive_losses:
            self.is_paused = True
            self.pause_reason = f"Límite alcanzado: {self.consecutive_losses} pérdidas consecutivas."

        max_daily_loss = -(self.capital * (self.daily_loss_limit_pct / 100.0))
        if self.daily_pnl <= max_daily_loss:
            self.is_paused = True
            self.pause_reason = f"Límite de pérdida diaria alcanzado ({self.daily_loss_limit_pct}%)."

    def get_suggested_stake(self) -> float:
        """Suggested fixed stake strictly at 1% of capital (No Martingale)."""
        stake = self.capital * (RISK_DEFAULTS["max_risk_per_trade_pct"] / 100.0)
        return max(1.0, round(stake, 2))

    def reset_limits(self):
        """Manual reset by user."""
        self.consecutive_losses = 0
        self.daily_pnl = 0.0
        self.is_paused = False
        self.pause_reason = ""

    def get_status(self) -> Dict[str, Any]:
        return {
            "capital": self.capital,
            "suggested_stake": self.get_suggested_stake(),
            "consecutive_losses": self.consecutive_losses,
            "max_consecutive_losses": self.max_consecutive_losses,
            "daily_pnl": round(self.daily_pnl, 2),
            "is_paused": self.is_paused,
            "pause_reason": self.pause_reason
        }

