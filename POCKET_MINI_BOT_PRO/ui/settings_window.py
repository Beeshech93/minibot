"""
Settings and Risk Configuration Dialog for Pocket Mini Bot Pro.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QCheckBox, QPushButton, QComboBox, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt
from app.config import MARKET_OTC, MARKET_NORMAL


class SettingsDialog(QDialog):
    """Settings modal allowing customization of alerts, risk limits, and market mode."""

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle("⚙️ Ajustes y Gestión de Riesgo")
        self.setFixedWidth(320)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.init_ui()
        self.load_values()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # 1. Market & Asset
        group_market = QGroupBox("Mercado y Activo")
        market_layout = QFormLayout(group_market)
        self.asset_edit = QLineEdit("EUR/USD (OTC)")
        self.market_combo = QComboBox()
        self.market_combo.addItems([MARKET_OTC, MARKET_NORMAL])
        market_layout.addRow("Activo:", self.asset_edit)
        market_layout.addRow("Modo:", self.market_combo)
        layout.addWidget(group_market)

        # 2. Risk Management Panel
        group_risk = QGroupBox("Gestión de Riesgo (Estricto)")
        risk_layout = QFormLayout(group_risk)
        self.capital_edit = QLineEdit("100.0")
        self.max_losses_edit = QLineEdit("3")
        self.daily_loss_edit = QLineEdit("5.0")
        risk_layout.addRow("Capital ($):", self.capital_edit)
        risk_layout.addRow("Pérdidas Max Seguidas:", self.max_losses_edit)
        risk_layout.addRow("Pérdida Diaria Max (%):", self.daily_loss_edit)
        layout.addWidget(group_risk)

        # 3. Alerts & Telegram
        group_alerts = QGroupBox("Notificaciones")
        alert_layout = QFormLayout(group_alerts)
        self.sound_check = QCheckBox("Sonidos nativos de macOS")
        self.sound_check.setChecked(True)
        self.telegram_check = QCheckBox("Notificaciones Telegram")
        self.tg_token = QLineEdit()
        self.tg_token.setPlaceholderText("Token del Bot")
        self.tg_chat = QLineEdit()
        self.tg_chat.setPlaceholderText("Chat ID")
        alert_layout.addRow(self.sound_check)
        alert_layout.addRow(self.telegram_check)
        alert_layout.addRow("Bot Token:", self.tg_token)
        alert_layout.addRow("Chat ID:", self.tg_chat)
        layout.addWidget(group_alerts)

        # 4. Compliance Notice
        notice = QLabel(
            "🔒 Aviso de Seguridad:\n"
            "Pocket Mini Bot Pro opera 100% de forma local mediante visión por computadora. "
            "Nunca solicita contraseñas ni ejecuta operaciones automáticamente."
        )
        notice.setWordWrap(True)
        notice.setStyleSheet("font-size: 8px; color: #64748b; padding: 4px;")
        layout.addWidget(notice)

        # 5. Buttons
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Guardar")
        self.btn_save.setObjectName("primaryBtn")
        self.btn_save.clicked.connect(self.save_and_close)
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setObjectName("secondaryBtn")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def load_values(self):
        self.asset_edit.setText(self.db.get_setting("symbol", "EUR/USD (OTC)"))
        self.market_combo.setCurrentText(self.db.get_setting("market_type", MARKET_OTC))
        self.capital_edit.setText(self.db.get_setting("capital", "100.0"))
        self.max_losses_edit.setText(self.db.get_setting("max_losses", "3"))
        self.daily_loss_edit.setText(self.db.get_setting("daily_loss_limit", "5.0"))
        self.sound_check.setChecked(self.db.get_setting("sound_enabled", "1") == "1")
        self.telegram_check.setChecked(self.db.get_setting("telegram_enabled", "0") == "1")
        self.tg_token.setText(self.db.get_setting("telegram_token", ""))
        self.tg_chat.setText(self.db.get_setting("telegram_chat", ""))

    def save_and_close(self):
        self.db.set_setting("symbol", self.asset_edit.text().strip())
        self.db.set_setting("market_type", self.market_combo.currentText())
        self.db.set_setting("capital", self.capital_edit.text().strip())
        self.db.set_setting("max_losses", self.max_losses_edit.text().strip())
        self.db.set_setting("daily_loss_limit", self.daily_loss_edit.text().strip())
        self.db.set_setting("sound_enabled", "1" if self.sound_check.isChecked() else "0")
        self.db.set_setting("telegram_enabled", "1" if self.telegram_check.isChecked() else "0")
        self.db.set_setting("telegram_token", self.tg_token.text().strip())
        self.db.set_setting("telegram_chat", self.tg_chat.text().strip())
        self.accept()
