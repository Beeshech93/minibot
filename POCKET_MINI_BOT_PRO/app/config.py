"""
Configuration and Global Constants for Pocket Mini Bot Pro.
"""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
SOUNDS_DIR = ASSETS_DIR / "sounds"
DB_PATH = DATA_DIR / "signals.db"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
ICONS_DIR.mkdir(parents=True, exist_ok=True)
SOUNDS_DIR.mkdir(parents=True, exist_ok=True)

# Window Dimensions (Strict requirement: 350x500 px, always on top)
WINDOW_WIDTH = 350
WINDOW_HEIGHT = 500
WINDOW_RESIZABLE = False
ALWAYS_ON_TOP = True

# Trading Timeframes
TIMEFRAMES = ["5s", "15s", "30s", "1m", "5m"]
DEFAULT_TIMEFRAME = "1m"
TIMEFRAME_SECONDS = {
    "5s": 5,
    "15s": 15,
    "30s": 30,
    "1m": 60,
    "5m": 300,
}

# Monitoring intervals (Visual sampling frequency)
MONITORING_INTERVALS = [1, 2, 3, 5]
DEFAULT_MONITORING_INTERVAL = 5  # 5 seconds default as per prompt

# Markets
MARKET_NORMAL = "NORMAL"
MARKET_OTC = "OTC"
DEFAULT_MARKET = MARKET_OTC

# Six Filters Thresholds
FILTER_RULES = {
    "ema_fast": 9,
    "ema_slow": 21,
    "ema_trend": 50,
    "rsi_period": 14,
    "rsi_call_min": 50.0,
    "rsi_call_max": 68.0,
    "rsi_put_min": 32.0,
    "rsi_put_max": 50.0,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "bb_period": 20,
    "bb_std": 2.0,
    "atr_period": 14,
    "min_required_filters": 5,  # At least 5 of 6 filters required for CALL or PUT
    "total_filters": 6
}

# Risk Management Defaults
RISK_DEFAULTS = {
    "max_risk_per_trade_pct": 1.0,  # 1% of capital
    "max_consecutive_losses": 3,
    "daily_loss_limit_pct": 5.0,
    "initial_capital": 100.0,
    "allow_martingale": False  # Strictly forbidden
}

# Sound and Notification Settings
SOUND_ENABLED_DEFAULT = True
TELEGRAM_ENABLED_DEFAULT = False
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""
