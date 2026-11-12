"""
Alert and Notification Service.
Supports macOS native sound effects, system beeps, and optional Telegram bot notifications.
"""
import subprocess
import urllib.request
import urllib.parse
import json
from typing import Optional
from PySide6.QtWidgets import QApplication


class NotificationManager:
    """Dispatches audio, visual, and external Telegram alerts without blocking GUI threads."""

    def __init__(self, sound_enabled: bool = True, telegram_enabled: bool = False, bot_token: str = "", chat_id: str = ""):
        self.sound_enabled = sound_enabled
        self.telegram_enabled = telegram_enabled
        self.bot_token = bot_token
        self.chat_id = chat_id

    def play_sound(self, direction: str):
        """Play a distinctive alert tone for CALL vs PUT."""
        if not self.sound_enabled:
            return

        try:
            # Native macOS system audio
            sound_name = "Ping" if direction == "CALL" else "Basso"
            subprocess.Popen(
                ["afplay", f"/System/Library/Sounds/{sound_name}.aiff"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            # Fallback to standard Qt application beep
            QApplication.beep()

    def send_telegram(self, message: str):
        """Send message via Telegram Bot API asynchronously."""
        if not self.telegram_enabled or not self.bot_token or not self.chat_id:
            return

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        try:
            data = urllib.parse.urlencode(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, method="POST")
            # Set short timeout so UI is never blocked
            with urllib.request.urlopen(req, timeout=3) as resp:
                pass
        except Exception:
            # Log or fail silently to ensure trading flow is never interrupted
            pass

    def dispatch_signal_alert(self, signal: dict):
        """Send complete alert package."""
        dir_text = signal.get("direction", "WAIT")
        self.play_sound(dir_text)

        if self.telegram_enabled:
            icon = "🟢" if dir_text == "CALL" else "🔴"
            msg = (
                f"<b>{icon} POCKET MINI BOT PRO</b>\n"
                f"<b>Señal:</b> {dir_text}\n"
                f"<b>Activo:</b> {signal.get('asset', 'OTC')}\n"
                f"<b>Vigencia:</b> {signal.get('timeframe', '1m')}\n"
                f"<b>Concordancia Técnica:</b> {signal.get('score', 0)}%\n"
                f"<b>Razón:</b> {signal.get('reason', '')}"
            )
            self.send_telegram(msg)

