"""
Main Dashboard View Widget for Pocket Mini Bot Pro.
"""
from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QProgressBar, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPen

from app.config import TIMEFRAMES, DEFAULT_TIMEFRAME, MONITORING_INTERVALS, DEFAULT_MONITORING_INTERVAL
from app.candle_detector import Candle


class VisionRadarWidget(QFrame):
    """Mini visual radar drawing exactly what candles the computer vision engine sees."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.candles: List[Candle] = []
        self.setFixedHeight(55)
        self.setStyleSheet("background-color: #070b12; border: 1px solid #1e293b; border-radius: 6px;")

    def update_candles(self, candles: List[Candle]):
        self.candles = candles
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        if not self.candles:
            painter.setPen(QColor(100, 116, 139))
            painter.drawText(self.rect(), Qt.AlignCenter, "Esperando recorte de velas...")
            return

        min_x = min(c.x for c in self.candles)
        max_x = max(c.x for c in self.candles)
        span_x = max(1.0, max_x - min_x)

        all_highs = [c.high for c in self.candles]
        all_lows = [c.low for c in self.candles]
        max_price = max(all_highs)
        min_price = min(all_lows)
        span_price = max(1.0, max_price - min_price)

        for c in self.candles:
            draw_x = int(8 + (c.x - min_x) / span_x * (w - 24))
            draw_high_y = int(h - 4 - ((c.high - min_price) / span_price) * (h - 12))
            draw_low_y = int(h - 4 - ((c.low - min_price) / span_price) * (h - 12))
            draw_open_y = int(h - 4 - ((c.open - min_price) / span_price) * (h - 12))
            draw_close_y = int(h - 4 - ((c.close - min_price) / span_price) * (h - 12))

            color = QColor(16, 185, 129) if c.color > 0 else QColor(244, 63, 94)

            # Wick line
            painter.setPen(QPen(color, 1))
            painter.drawLine(draw_x, draw_high_y, draw_x, draw_low_y)

            # Body rectangle
            top_y = min(draw_open_y, draw_close_y)
            bot_y = max(draw_open_y, draw_close_y)
            body_h = max(2, bot_y - top_y)
            body_w = max(3, int((w / max(1, len(self.candles))) * 0.55))

            painter.setBrush(color)
            painter.drawRect(draw_x - body_w // 2, top_y, body_w, body_h)


class DashboardView(QWidget):
    """Main dashboard layout hosting all status badges, signals, indicators and buttons."""

    # UI Event Signals
    pick_region_requested = Signal()
    toggle_analysis_requested = Signal()
    analyze_now_requested = Signal()
    reset_capture_requested = Signal()
    open_settings_requested = Signal()
    open_history_requested = Signal()
    timeframe_changed = Signal(str)
    interval_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 6, 8, 6)
        root.setSpacing(5)

        # 1. Header Frame
        header = QFrame()
        header.setObjectName("headerFrame")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(2, 2, 2, 2)
        h_layout.setSpacing(4)

        self.title_label = QLabel("POCKET MINI BOT PRO")
        self.title_label.setObjectName("appTitle")

        self.mode_badge = QLabel("OTC")
        self.mode_badge.setObjectName("modeBadge")

        self.status_badge = QLabel("Desconectado")
        self.status_badge.setObjectName("statusBadge")

        h_layout.addWidget(self.title_label)
        h_layout.addStretch()
        h_layout.addWidget(self.mode_badge)
        h_layout.addWidget(self.status_badge)
        root.addWidget(header)

        # 2. Asset & Timeframe Selectors Row
        meta_row = QHBoxLayout()
        meta_row.setSpacing(4)

        self.asset_label = QLabel("EUR/USD (OTC)")
        self.asset_label.setStyleSheet("font-weight: 800; color: #f8fafc; font-size: 10px;")

        self.tf_combo = QComboBox()
        self.tf_combo.addItems([f"⏱️ {tf}" for tf in TIMEFRAMES])
        self.tf_combo.setCurrentText(f"⏱️ {DEFAULT_TIMEFRAME}")
        self.tf_combo.currentTextChanged.connect(lambda t: self.timeframe_changed.emit(t.replace("⏱️ ", "")))

        self.interval_combo = QComboBox()
        self.interval_combo.addItems([f"⚡ {i}s" for i in MONITORING_INTERVALS])
        self.interval_combo.setCurrentText(f"⚡ {DEFAULT_MONITORING_INTERVAL}s")
        self.interval_combo.currentTextChanged.connect(lambda t: self.interval_changed.emit(int(t.replace("⚡ ", "").replace("s", ""))))

        meta_row.addWidget(self.asset_label)
        meta_row.addStretch()
        meta_row.addWidget(self.tf_combo)
        meta_row.addWidget(self.interval_combo)
        root.addLayout(meta_row)

        # 3. Main Signal Card
        self.signal_card = QFrame()
        self.signal_card.setObjectName("signalCard")
        sc_layout = QVBoxLayout(self.signal_card)
        sc_layout.setContentsMargins(6, 6, 6, 6)
        sc_layout.setSpacing(3)

        self.signal_text = QLabel("WAIT")
        self.signal_text.setObjectName("signalText")
        self.signal_text.setAlignment(Qt.AlignCenter)

        self.score_text = QLabel("Concordancia Técnica: —")
        self.score_text.setObjectName("scoreText")
        self.score_text.setAlignment(Qt.AlignCenter)

        badges_row = QHBoxLayout()
        badges_row.setSpacing(4)
        self.time_badge = QLabel("⏱️ Vigencia: 1m")
        self.time_badge.setObjectName("timeBadge")
        self.countdown_badge = QLabel("⏳ Restante: —")
        self.countdown_badge.setObjectName("countdownBadge")
        badges_row.addWidget(self.time_badge)
        badges_row.addWidget(self.countdown_badge)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        sc_layout.addWidget(self.signal_text)
        sc_layout.addWidget(self.score_text)
        sc_layout.addLayout(badges_row)
        sc_layout.addWidget(self.progress_bar)
        root.addWidget(self.signal_card)

        # 4. Metrics Grid (RSI, ATR, Tendencia, Velas)
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(4)

        self.tile_rsi, self.val_rsi = self._create_tile("RSI (14)", "50.0")
        self.tile_atr, self.val_atr = self._create_tile("ATR (14)", "—")
        self.tile_trend, self.val_trend = self._create_tile("TENDENCIA", "Lateral")
        self.tile_candles, self.val_candles = self._create_tile("VELAS", "0")

        metrics_grid.addWidget(self.tile_rsi, 0, 0)
        metrics_grid.addWidget(self.tile_atr, 0, 1)
        metrics_grid.addWidget(self.tile_trend, 0, 2)
        metrics_grid.addWidget(self.tile_candles, 0, 3)
        root.addLayout(metrics_grid)

        # 5. The Six-Filters Indicator Panel
        self.filters_panel = QFrame()
        self.filters_panel.setObjectName("filtersPanel")
        fp_layout = QVBoxLayout(self.filters_panel)
        fp_layout.setContentsMargins(6, 4, 6, 4)
        fp_layout.setSpacing(2)

        self.fp_header = QLabel("FILTROS CUANTITATIVOS (5 de 6 Requeridos)")
        self.fp_header.setObjectName("filtersHeader")
        fp_layout.addWidget(self.fp_header)

        self.row_f1 = QLabel("⚪ 1. Tendencia (EMA 9/21): Lateral")
        self.row_f1.setObjectName("filterRow")
        self.row_f2 = QLabel("⚪ 2. RSI (32-50 PUT | 50-68 CALL): —")
        self.row_f2.setObjectName("filterRow")
        self.row_f3 = QLabel("⚪ 3. MACD Momentum: —")
        self.row_f3.setObjectName("filterRow")
        self.row_f4 = QLabel("⚪ 4. Patrón de Vela Cerrada: —")
        self.row_f4.setObjectName("filterRow")
        self.row_f5 = QLabel("⚪ 5. Soporte & Resistencia: —")
        self.row_f5.setObjectName("filterRow")
        self.row_f6 = QLabel("⚪ 6. Volatilidad / ATR: —")
        self.row_f6.setObjectName("filterRow")

        fp_layout.addWidget(self.row_f1)
        fp_layout.addWidget(self.row_f2)
        fp_layout.addWidget(self.row_f3)
        fp_layout.addWidget(self.row_f4)
        fp_layout.addWidget(self.row_f5)
        fp_layout.addWidget(self.row_f6)
        root.addWidget(self.filters_panel)

        # 6. Reason / Decision Banner
        self.reason_banner = QLabel("Selecciona el área de velas del gráfico para iniciar el análisis.")
        self.reason_banner.setObjectName("reasonBanner")
        self.reason_banner.setWordWrap(True)
        root.addWidget(self.reason_banner)

        # 7. Vision Radar
        self.radar = VisionRadarWidget()
        root.addWidget(self.radar)

        # 8. Control Buttons
        btn_grid = QGridLayout()
        btn_grid.setSpacing(4)

        self.btn_pick = QPushButton("🎯 Seleccionar Área")
        self.btn_pick.setObjectName("secondaryBtn")
        self.btn_pick.clicked.connect(self.pick_region_requested.emit)

        self.btn_start = QPushButton("▶ Iniciar")
        self.btn_start.setObjectName("primaryBtn")
        self.btn_start.clicked.connect(self.toggle_analysis_requested.emit)

        self.btn_analyze = QPushButton("⚡ Analizar Ya")
        self.btn_analyze.setObjectName("subtleBtn")
        self.btn_analyze.clicked.connect(self.analyze_now_requested.emit)

        self.btn_history = QPushButton("📜 Historial")
        self.btn_history.setObjectName("subtleBtn")
        self.btn_history.clicked.connect(self.open_history_requested.emit)

        self.btn_settings = QPushButton("⚙️ Ajustes")
        self.btn_settings.setObjectName("subtleBtn")
        self.btn_settings.clicked.connect(self.open_settings_requested.emit)

        btn_grid.addWidget(self.btn_pick, 0, 0)
        btn_grid.addWidget(self.btn_start, 0, 1)
        btn_grid.addWidget(self.btn_analyze, 1, 0)
        btn_grid.addWidget(self.btn_history, 1, 1)
        btn_grid.addWidget(self.btn_settings, 1, 2)
        root.addLayout(btn_grid)

    def _create_tile(self, title: str, initial_val: str):
        tile = QFrame()
        tile.setObjectName("tile")
        layout = QVBoxLayout(tile)
        layout.setContentsMargins(2, 3, 2, 3)
        layout.setSpacing(1)

        t = QLabel(title)
        t.setObjectName("tileTitle")
        t.setAlignment(Qt.AlignCenter)

        v = QLabel(initial_val)
        v.setObjectName("tileVal")
        v.setAlignment(Qt.AlignCenter)

        layout.addWidget(t)
        layout.addWidget(v)
        return tile, v

    def update_signal_display(self, direction: str, score: int, reason: str, filters_status: dict, indicators: dict):
        """Update dashboard display elements with latest signal evaluation."""
        self.signal_text.setText(direction)
        self.score_text.setText(f"Concordancia Técnica: {score}% ({direction})")
        self.reason_banner.setText(reason)

        # Style signal card based on direction
        self.signal_card.setProperty("class", direction)
        self.signal_card.style().unpolish(self.signal_card)
        self.signal_card.style().polish(self.signal_card)

        # Update metrics tiles
        if "rsi" in indicators:
            self.val_rsi.setText(str(indicators["rsi"]))
        if "atr" in indicators:
            self.val_atr.setText(str(indicators["atr"]))

        # Update 6-filters checklist
        def fmt_row(num: str, name: str, f_data: dict) -> str:
            if not f_data:
                return f"⚪ {num}. {name}: —"
            c = f_data.get("call", False)
            p = f_data.get("put", False)
            status = f_data.get("status", "")
            icon = "🟢" if c else "🔴" if p else "⚪"
            return f"{icon} {num}. {name}: {status}"

        self.row_f1.setText(fmt_row("1", "Tendencia EMA 9/21", filters_status.get("f1_trend", {})))
        self.row_f2.setText(fmt_row("2", "RSI Momentum", filters_status.get("f2_rsi", {})))
        self.row_f3.setText(fmt_row("3", "MACD Histograma", filters_status.get("f3_macd", {})))
        self.row_f4.setText(fmt_row("4", "Patrón Vela", filters_status.get("f4_candle", {})))
        self.row_f5.setText(fmt_row("5", "Soporte/Resistencia", filters_status.get("f5_sr", {})))
        self.row_f6.setText(fmt_row("6", "Volatilidad ATR", filters_status.get("f6_volatility", {})))
