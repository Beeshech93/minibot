"""
Main Window Controller for Pocket Mini Bot Pro.
Enforces 350x500 px floating dimensions, Always-on-top, and visual pipeline scheduling.
"""
from datetime import datetime
from typing import Optional
from PySide6.QtWidgets import QMainWindow, QWidget, QApplication
from PySide6.QtCore import Qt, QTimer, QRect, Signal, QPoint
from PySide6.QtGui import QPainter, QColor, QPen

from app.config import WINDOW_WIDTH, WINDOW_HEIGHT, ALWAYS_ON_TOP, TIMEFRAME_SECONDS, MARKET_OTC
from app.database import DatabaseManager
from app.capture_engine import CaptureEngine
from app.chart_detector import ChartDetector
from app.candle_detector import CandleDetector
from app.data_quality import DataQualityEvaluator
from app.strategy_engine import StrategyEngine
from app.signal_manager import SignalManager
from app.risk_manager import RiskManager
from app.notifications import NotificationManager

from .styles import MAIN_STYLESHEET
from .dashboard import DashboardView
from .settings_window import SettingsDialog
from .history_window import HistoryDialog


class RegionPicker(QWidget):
    """Transparent full-screen overlay for user chart region selection."""
    region_selected = Signal(QRect)
    cancelled = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
        else:
            self.setWindowState(Qt.WindowFullScreen)
        self.setCursor(Qt.CrossCursor)
        self.setWindowOpacity(0.28)
        self.origin: Optional[QPoint] = None
        self.current_rect = QRect()
        self.setStyleSheet("background: black;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 90))
        painter.setPen(QPen(QColor(56, 189, 248), 3))
        painter.drawRect(self.current_rect)

    def mousePressEvent(self, event):
        self.origin = event.position().toPoint()
        self.current_rect = QRect(self.origin, self.origin)
        self.update()

    def mouseMoveEvent(self, event):
        if self.origin is not None:
            self.current_rect = QRect(self.origin, event.position().toPoint()).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if self.origin is None:
            return
        rect = self.current_rect.normalized()
        self.close()
        if rect.width() > 50 and rect.height() > 40:
            self.region_selected.emit(rect)
        else:
            self.cancelled.emit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
            self.cancelled.emit()


class MainWindow(QMainWindow):
    """Primary application window for Pocket Mini Bot Pro."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pocket Mini Bot Pro")
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)

        # Window flags: Always on top, non-resizable
        flags = Qt.Window
        if ALWAYS_ON_TOP:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)

        self.setStyleSheet(MAIN_STYLESHEET)

        # Initialize App Modules
        self.db = DatabaseManager()
        self.capture_engine = CaptureEngine()
        self.chart_detector = ChartDetector()
        self.candle_detector = CandleDetector()
        self.quality_evaluator = DataQualityEvaluator()
        self.strategy_engine = StrategyEngine(market_type=MARKET_OTC)
        self.signal_manager = SignalManager(self.db)
        self.risk_manager = RiskManager()
        self.notifications = NotificationManager()

        # UI Components
        self.dashboard = DashboardView(self)
        self.setCentralWidget(self.dashboard)

        # Connect Dashboard Signals
        self.dashboard.pick_region_requested.connect(self.start_region_pick)
        self.dashboard.toggle_analysis_requested.connect(self.toggle_analysis)
        self.dashboard.analyze_now_requested.connect(self.perform_analysis_cycle)
        self.dashboard.open_settings_requested.connect(self.open_settings)
        self.dashboard.open_history_requested.connect(self.open_history)
        self.dashboard.timeframe_changed.connect(self.on_timeframe_changed)
        self.dashboard.interval_changed.connect(self.on_interval_changed)

        # Runtime State
        self.is_running = False
        self.active_timeframe = "1m"
        self.monitoring_interval_sec = 5
        self.total_countdown_sec = 60
        self.remaining_countdown_sec = 60

        # Analysis Timers
        self.analysis_timer = QTimer(self)
        self.analysis_timer.timeout.connect(self.perform_analysis_cycle)

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.on_second_tick)
        self.clock_timer.start(1000)

        self.picker: Optional[RegionPicker] = None

    def start_region_pick(self):
        """Launch screen overlay picker."""
        self.picker = RegionPicker()
        self.picker.region_selected.connect(self.on_region_selected)
        self.picker.cancelled.connect(self.on_region_cancelled)
        self.picker.show()

    def on_region_selected(self, rect: QRect):
        self.capture_engine.set_region(rect)
        self.dashboard.status_badge.setText("Calibrado")
        self.dashboard.reason_banner.setText("Área seleccionada con éxito. Presiona «▶ Iniciar» para comenzar.")
        self.perform_analysis_cycle()

    def on_region_cancelled(self):
        self.dashboard.reason_banner.setText("Selección cancelada. Vuelve a intentarlo cuando estés listo.")

    def toggle_analysis(self):
        """Start or Pause real-time analysis."""
        if self.is_running:
            self.stop_analysis()
        else:
            self.start_analysis()

    def start_analysis(self):
        if not self.capture_engine.selected_rect:
            self.start_region_pick()
            return
        self.is_running = True
        self.dashboard.btn_start.setText("⏸ Pausar")
        self.dashboard.status_badge.setText("EN VIVO")
        self.analysis_timer.start(self.monitoring_interval_sec * 1000)
        self.perform_analysis_cycle()

    def stop_analysis(self):
        self.is_running = False
        self.dashboard.btn_start.setText("▶ Iniciar")
        self.dashboard.status_badge.setText("Pausado")
        self.analysis_timer.stop()

    def on_timeframe_changed(self, tf: str):
        self.active_timeframe = tf
        self.total_countdown_sec = TIMEFRAME_SECONDS.get(tf, 60)
        self.dashboard.time_badge.setText(f"⏱️ Vigencia: {tf}")

    def on_interval_changed(self, sec: int):
        self.monitoring_interval_sec = sec
        if self.is_running:
            self.analysis_timer.start(self.monitoring_interval_sec * 1000)

    def on_second_tick(self):
        """Handles candle lifecycle timing, alerts in the last 5 seconds, and visual progress bar."""
        now = datetime.now()
        secs = now.second
        secs_left = 60 - secs if secs != 0 else 0

        # Trigger quick analysis on final 5-second candle close confirmation
        if 1 <= secs_left <= 5 and self.is_running:
            self.perform_analysis_cycle()

        if self.remaining_countdown_sec > 0:
            self.remaining_countdown_sec -= 1
            self.dashboard.countdown_badge.setText(f"⏳ Restante: {self.remaining_countdown_sec}s")
            pct = int((self.remaining_countdown_sec / max(1, self.total_countdown_sec)) * 100)
            self.dashboard.progress_bar.setValue(pct)
        else:
            self.remaining_countdown_sec = self.total_countdown_sec
            self.dashboard.progress_bar.setValue(100)

    def perform_analysis_cycle(self):
        """Execute full visual pipeline: capture -> filter -> detect -> indicators -> evaluate -> display."""
        frame = self.capture_engine.capture()
        if frame is None:
            return

        # 1. Preprocess & Refine Chart ROI
        chart_roi, _ = self.chart_detector.refine_chart_roi(frame)

        # 2. Extract Candlesticks
        candles = self.candle_detector.extract_candles(chart_roi)
        self.dashboard.val_candles.setText(str(len(candles)))
        self.dashboard.radar.update_candles(candles)

        # 3. Evaluate Data Quality
        quality = self.quality_evaluator.evaluate(candles, chart_roi.shape[:2])

        # 4. Run Strategy Engine (Six Filters)
        eval_result = self.strategy_engine.evaluate(candles, quality)

        # 5. Update UI
        direction = eval_result["direction"]
        score = eval_result["technical_score"]
        reason = eval_result["reason"]
        filters_status = eval_result.get("filters_status", {})
        indicators = eval_result.get("indicator_values", {})

        self.dashboard.update_signal_display(direction, score, reason, filters_status, indicators)

        # 6. Check Active Signal Outcomes
        if candles:
            self.signal_manager.check_outcomes(candles[-1].close)

        # 7. Process New Signal (Deduplicated)
        new_sig = self.signal_manager.process_evaluation(
            eval_result=eval_result,
            candles=candles,
            asset_symbol=self.dashboard.asset_label.text(),
            timeframe=self.active_timeframe,
            data_quality_label=quality["quality"]
        )

        if new_sig:
            self.notifications.dispatch_signal_alert(new_sig)
            self.remaining_countdown_sec = self.total_countdown_sec

    def open_settings(self):
        dlg = SettingsDialog(self.db, self)
        if dlg.exec():
            # Refresh settings
            sym = self.db.get_setting("symbol", "EUR/USD (OTC)")
            m_type = self.db.get_setting("market_type", MARKET_OTC)
            self.dashboard.asset_label.setText(sym)
            self.dashboard.mode_badge.setText(m_type)
            self.strategy_engine.market_type = m_type
            self.notifications.sound_enabled = (self.db.get_setting("sound_enabled", "1") == "1")
            self.notifications.telegram_enabled = (self.db.get_setting("telegram_enabled", "0") == "1")
            self.notifications.bot_token = self.db.get_setting("telegram_token", "")
            self.notifications.chat_id = self.db.get_setting("telegram_chat", "")

    def open_history(self):
        dlg = HistoryDialog(self.db, self)
        dlg.exec()
