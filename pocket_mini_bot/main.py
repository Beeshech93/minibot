import sys
from datetime import datetime
import random
from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QProgressBar, QMessageBox
)
try:
    from capture import capture_region, analyze_chart, RegionPicker
except ImportError:
    from pocket_mini_bot.capture import capture_region, analyze_chart, RegionPicker

class MiniBot(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pocket Mini Bot")
        self.setFixedSize(340, 590)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.region = None
        self.last_result = None

        # Analysis loop timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.analyze)

        # 1-second countdown timer
        self.countdown_timer = QTimer(self)
        self.countdown_timer.setInterval(1000)
        self.countdown_timer.timeout.connect(self.tick_countdown)
        self.total_seconds = 0
        self.remaining_seconds = 0

        # Wall-clock candle synchronizer timer (1s interval)
        self.clock_timer = QTimer(self)
        self.clock_timer.setInterval(1000)
        self.clock_timer.timeout.connect(self.tick_candle_clock)
        self.clock_timer.start()
        self._current_sig = "ESPERAR"

        # Main Layout
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        # Header: Title + Status Pill
        header = QHBoxLayout()
        header.setSpacing(6)
        title = QLabel("POCKET BOT")
        title.setObjectName("title")
        self.status = QLabel("Listo")
        self.status.setObjectName("status")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.status)
        root.addLayout(header)

        # Hero Card: Signal + Expiration Time + Live Countdown
        self.signal_card = QFrame()
        self.signal_card.setObjectName("signalCard")
        card_layout = QVBoxLayout(self.signal_card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(6)

        # Signal Type (CALL / PUT / ESPERAR)
        self.next_candle_badge = QLabel("🔮 PRÓXIMA VELA: EVALUANDO")
        self.next_candle_badge.setAlignment(Qt.AlignCenter)
        self.next_candle_badge.setObjectName("nextCandleBadge")
        card_layout.addWidget(self.next_candle_badge)

        self.signal = QLabel("ESPERAR")
        self.signal.setAlignment(Qt.AlignCenter)
        self.signal.setObjectName("signalText")
        card_layout.addWidget(self.signal)

        # Confidence
        self.confidence = QLabel("Confianza: —")
        self.confidence.setAlignment(Qt.AlignCenter)
        self.confidence.setObjectName("confidenceText")
        card_layout.addWidget(self.confidence)

        # Time banner inside signal card
        time_row = QHBoxLayout()
        time_row.setSpacing(8)

        self.exp_badge = QLabel("⏱️ Tiempo: —")
        self.exp_badge.setObjectName("expBadge")
        self.exp_badge.setAlignment(Qt.AlignCenter)

        self.countdown_label = QLabel("⏳ Restante: —")
        self.countdown_label.setObjectName("countdownBadge")
        self.countdown_label.setAlignment(Qt.AlignCenter)

        time_row.addWidget(self.exp_badge)
        time_row.addWidget(self.countdown_label)
        card_layout.addLayout(time_row)

        # Alert Badge for Last 5 Seconds
        self.alert_badge = QLabel("⏳ Formando vela... Alerta activa a los :55s")
        self.alert_badge.setObjectName("alertBadge")
        self.alert_badge.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.alert_badge)

        # Progress bar for signal expiration
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("signalProgress")
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(5)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        card_layout.addWidget(self.progress_bar)

        root.addWidget(self.signal_card)

        # 4 Metric Tiles (RSI, Tendencia, Tiempo, Velas)
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(6)
        rsi_tile, self.rsi_title, self.rsi_val = self.create_tile("RSI", "—")
        trend_tile, self.trend_title, self.trend_val = self.create_tile("TENDENCIA", "—")
        time_tile, self.time_title, self.time_val = self.create_tile("TIEMPO", "—")
        candles_tile, self.candles_title, self.candles_val = self.create_tile("VELAS", "—")
        metrics_layout.addWidget(rsi_tile)
        metrics_layout.addWidget(trend_tile)
        metrics_layout.addWidget(time_tile)
        metrics_layout.addWidget(candles_tile)
        root.addLayout(metrics_layout)

        # Info / Instruction Banner
        self.info_banner = QLabel("Selecciona el área de velas del gráfico para iniciar.")
        self.info_banner.setObjectName("infoBanner")
        self.info_banner.setWordWrap(True)
        root.addWidget(self.info_banner)

        # Multi-Agent Intelligence Status Panel
        self.agents_frame = QFrame()
        self.agents_frame.setObjectName("agentsFrame")
        agents_layout = QVBoxLayout(self.agents_frame)
        agents_layout.setContentsMargins(10, 8, 10, 8)
        agents_layout.setSpacing(3)

        agents_header = QLabel("🤖 Confluencia Triple: Velas + Tendencia + Manipulación")
        agents_header.setObjectName("agentsHeader")
        agents_layout.addWidget(agents_header)

        self.agent_candles = QLabel("• 📊 Velas Anteriores: Analizando secuencia")
        self.agent_candles.setObjectName("agentRow")
        self.agent_trend = QLabel("• 📈 Tendencia Macro: Mapeando medias EMA")
        self.agent_trend.setObjectName("agentRow")
        self.agent_manipulation = QLabel("• 🛡️ Anti-Manipulación: Verificando OTC")
        self.agent_manipulation.setObjectName("agentRow")
        self.agent_confluence = QLabel("• 🎯 Confluencia Global: Esperando alineación")
        self.agent_confluence.setObjectName("agentRow")

        agents_layout.addWidget(self.agent_candles)
        agents_layout.addWidget(self.agent_trend)
        agents_layout.addWidget(self.agent_manipulation)
        agents_layout.addWidget(self.agent_confluence)
        root.addWidget(self.agents_frame)

        # Timeframe mode selector (MTF: 5m Analysis + 1m Entry default)
        self.time_mode = QComboBox()
        self.time_mode.setObjectName("comboInput")
        self.time_mode.addItems([
            "🎯 MTF: Análisis 5m + Señal 1m (Recomendado)",
            "⏱️ Fijar a 1 min (M1)",
            "⏱️ Fijar a 2 min (M2)",
            "⏱️ Fijar a 3 min (M3)",
            "⏱️ Fijar a 5 min (M5)"
        ])
        root.addWidget(self.time_mode)

        # Fast Sampling Interval Selector (1s, 2s, 3s, 5s)
        self.interval = QComboBox()
        self.interval.setObjectName("comboInput")
        self.interval.addItems([
            "⚡ Confirmación: 1 seg (Ultra rápido)",
            "⚡ Confirmación: 2 seg (Rápido)",
            "🔄 Confirmación: 3 seg",
            "🔄 Confirmación: 5 seg"
        ])
        root.addWidget(self.interval)

        # Action Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.pick_btn = QPushButton("🎯 Seleccionar área")
        self.pick_btn.setObjectName("secondaryBtn")
        self.pick_btn.clicked.connect(self.pick_region)
        self.start_btn = QPushButton("▶ Iniciar En Vivo")
        self.start_btn.setObjectName("primaryBtn")
        self.start_btn.clicked.connect(self.toggle)
        btn_row.addWidget(self.pick_btn)
        btn_row.addWidget(self.start_btn)
        root.addLayout(btn_row)

        self.once_btn = QPushButton("⚡ Analizar ahora")
        self.once_btn.setObjectName("subtleBtn")
        self.once_btn.clicked.connect(self.analyze)
        root.addWidget(self.once_btn)

        # Footer timestamp
        self.footer = QLabel("Modo En Vivo · Conectado a pantalla")
        self.footer.setObjectName("footerText")
        self.footer.setAlignment(Qt.AlignCenter)
        root.addWidget(self.footer)

        root.addStretch()

        self.apply_styles()

    def create_tile(self, title_text, val_text):
        tile = QFrame()
        tile.setObjectName("tile")
        layout = QVBoxLayout(tile)
        layout.setContentsMargins(4, 7, 4, 7)
        layout.setSpacing(2)
        
        t = QLabel(title_text)
        t.setObjectName("tileTitle")
        t.setAlignment(Qt.AlignCenter)
        
        v = QLabel(val_text)
        v.setObjectName("tileVal")
        v.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(t)
        layout.addWidget(v)
        return tile, t, v

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #0e131b;
                color: #e2e8f0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            }
            QLabel#title {
                font-size: 13px;
                font-weight: 800;
                letter-spacing: 0.8px;
                color: #94a3b8;
            }
            QLabel#status {
                background: #1e293b;
                color: #94a3b8;
                border: 1px solid #334155;
                border-radius: 9px;
                padding: 3px 9px;
                font-size: 11px;
                font-weight: 600;
            }
            QFrame#signalCard {
                background: #161f2e;
                border: 1px solid #253347;
                border-radius: 12px;
            }
            QLabel#nextCandleBadge {
                background: #0f172a;
                color: #38bdf8;
                border: 1px solid #1e293b;
                border-radius: 8px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 0.5px;
            }
            QLabel#signalText {
                font-size: 30px;
                font-weight: 800;
                letter-spacing: 1.2px;
                color: #94a3b8;
            }
            QLabel#confidenceText {
                font-size: 12px;
                font-weight: 500;
                color: #64748b;
            }
            QLabel#expBadge, QLabel#countdownBadge {
                background: #0f172a;
                color: #cbd5e1;
                border: 1px solid #1e293b;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 600;
            }
            QProgressBar#signalProgress {
                background-color: #1e293b;
                border: none;
                border-radius: 2px;
            }
            QProgressBar#signalProgress::chunk {
                background-color: #3b82f6;
                border-radius: 2px;
            }
            QFrame#tile {
                background: #161f2e;
                border: 1px solid #253347;
                border-radius: 8px;
            }
            QLabel#tileTitle {
                font-size: 8px;
                font-weight: 700;
                color: #64748b;
                letter-spacing: 0.5px;
            }
            QLabel#tileVal {
                font-size: 13px;
                font-weight: 700;
                color: #f1f5f9;
            }
            QLabel#infoBanner {
                background: #141b27;
                border: 1px solid #1e293b;
                border-left: 3px solid #38bdf8;
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 11px;
                color: #94a3b8;
                line-height: 1.3;
            }
            QComboBox#comboInput {
                background: #161f2e;
                color: #cbd5e1;
                border: 1px solid #253347;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
            }
            QComboBox#comboInput:hover {
                border-color: #3b82f6;
            }
            QPushButton {
                border-radius: 8px;
                padding: 9px 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton#primaryBtn {
                background: #2563eb;
                color: #ffffff;
                border: 1px solid #3b82f6;
            }
            QPushButton#primaryBtn:hover {
                background: #1d4ed8;
            }
            QPushButton#primaryBtn:pressed {
                background: #1e40af;
            }
            QPushButton#secondaryBtn {
                background: #1e293b;
                color: #cbd5e1;
                border: 1px solid #334155;
            }
            QPushButton#secondaryBtn:hover {
                background: #334155;
                color: #f8fafc;
            }
            QPushButton#subtleBtn {
                background: transparent;
                color: #64748b;
                border: 1px solid #1e293b;
                padding: 6px;
                font-size: 11px;
            }
            QPushButton#subtleBtn:hover {
                background: #161f2e;
                color: #cbd5e1;
                border-color: #334155;
            }
            QPushButton#demoBtn {
                background: #1e1b4b;
                color: #c7d2fe;
                border: 1px solid #4338ca;
                padding: 6px;
                font-size: 11px;
            }
            QPushButton#demoBtn:hover {
                background: #312e81;
                color: #e0e7ff;
            }
            QFrame#agentsFrame {
                background: #111722;
                border: 1px solid #1e293b;
                border-radius: 8px;
            }
            QLabel#agentsHeader {
                font-size: 10px;
                font-weight: 700;
                color: #818cf8;
                letter-spacing: 0.5px;
            }
            QLabel#agentRow {
                font-size: 10px;
                color: #94a3b8;
            }
            QLabel#footerText {
                font-size: 10px;
                color: #475569;
            }
        """)

    def update_signal_style(self, signal_type):
        if signal_type == "CALL":
            self.signal_card.setStyleSheet("""
                QFrame#signalCard {
                    background: #064e3b;
                    border: 1px solid #10b981;
                    border-radius: 12px;
                }
                QLabel#nextCandleBadge {
                    background: #042f2e;
                    color: #6ee7b7;
                    border: 1px solid #10b981;
                    border-radius: 8px;
                    padding: 4px 8px;
                    font-size: 11px;
                    font-weight: 800;
                }
                QLabel#signalText {
                    color: #34d399;
                }
                QLabel#confidenceText {
                    color: #a7f3d0;
                }
                QLabel#expBadge, QLabel#countdownBadge {
                    background: #042f2e;
                    color: #6ee7b7;
                    border: 1px solid #0d9488;
                }
            """)
            self.progress_bar.setStyleSheet("QProgressBar#signalProgress::chunk { background-color: #10b981; }")
            self.status.setStyleSheet("background:#064e3b; color:#34d399; border:1px solid #10b981; border-radius:9px; padding:3px 9px; font-size:11px; font-weight:600;")
        elif signal_type == "PUT":
            self.signal_card.setStyleSheet("""
                QFrame#signalCard {
                    background: #4c0519;
                    border: 1px solid #f43f5e;
                    border-radius: 12px;
                }
                QLabel#nextCandleBadge {
                    background: #2e0814;
                    color: #fda4af;
                    border: 1px solid #f43f5e;
                    border-radius: 8px;
                    padding: 4px 8px;
                    font-size: 11px;
                    font-weight: 800;
                }
                QLabel#signalText {
                    color: #fb7185;
                }
                QLabel#confidenceText {
                    color: #fecdd3;
                }
                QLabel#expBadge, QLabel#countdownBadge {
                    background: #2e0814;
                    color: #fda4af;
                    border: 1px solid #e11d48;
                }
            """)
            self.progress_bar.setStyleSheet("QProgressBar#signalProgress::chunk { background-color: #f43f5e; }")
            self.status.setStyleSheet("background:#4c0519; color:#fb7185; border:1px solid #f43f5e; border-radius:9px; padding:3px 9px; font-size:11px; font-weight:600;")
        else:
            self.signal_card.setStyleSheet("""
                QFrame#signalCard {
                    background: #161f2e;
                    border: 1px solid #253347;
                    border-radius: 12px;
                }
                QLabel#nextCandleBadge {
                    background: #0f172a;
                    color: #94a3b8;
                    border: 1px solid #253347;
                    border-radius: 8px;
                    padding: 4px 8px;
                    font-size: 11px;
                    font-weight: 800;
                }
                QLabel#signalText {
                    color: #94a3b8;
                }
                QLabel#confidenceText {
                    color: #64748b;
                }
                QLabel#expBadge, QLabel#countdownBadge {
                    background: #0f172a;
                    color: #cbd5e1;
                    border: 1px solid #1e293b;
                }
            """)
            self.progress_bar.setStyleSheet("QProgressBar#signalProgress::chunk { background-color: #3b82f6; }")
            self.status.setStyleSheet("background:#1e293b; color:#94a3b8; border:1px solid #334155; border-radius:9px; padding:3px 9px; font-size:11px; font-weight:600;")

    def pick_region(self):
        self.hide()
        self.picker = RegionPicker()
        self.picker.selected.connect(self.region_selected)
        self.picker.cancelled.connect(self.show)
        self.picker.show()

    def region_selected(self, rect):
        self.region = rect
        self.show()
        self.status.setText("Listo")
        self.info_banner.setText(f"Área: {rect.width()} × {rect.height()} px seleccionada.")

    def toggle(self):
        if self.timer.isActive():
            self.timer.stop()
            self.countdown_timer.stop()
            self.start_btn.setText("▶ Iniciar En Vivo")
            self.status.setText("Pausado")
            return
        if not self.region:
            screen = QApplication.primaryScreen()
            if screen:
                geom = screen.geometry()
                w = int(geom.width() * 0.75)
                h = int(geom.height() * 0.70)
                x = int((geom.width() - w) / 2)
                y = int((geom.height() - h) / 2)
                self.region = QRect(x, y, w, h)
                self.info_banner.setText(f"Área automática configurada ({w}x{h} px). Analizando pantalla en vivo.")
            else:
                self.pick_region()
                return
        intervals = [1, 2, 3, 5]
        seconds = intervals[self.interval.currentIndex()]
        self.timer.start(seconds * 1000)
        self.start_btn.setText("⏸ Pausar")
        self.status.setText("EN VIVO")
        self.analyze()

    def tick_candle_clock(self):
        now = datetime.now()
        sec = now.second
        min_val = now.minute

        mode_idx = self.time_mode.currentIndex()
        if mode_idx == 2:   # 2 MIN (M2)
            tf_sec = 120
            secs_left = 120 - ((min_val % 2) * 60 + sec)
        elif mode_idx == 3: # 3 MIN (M3)
            tf_sec = 180
            secs_left = 180 - ((min_val % 3) * 60 + sec)
        elif mode_idx == 4: # 5 MIN (M5)
            tf_sec = 300
            secs_left = 300 - ((min_val % 5) * 60 + sec)
        else:               # 0 (MTF: Análisis 5m + Señal 1m) o 1 (Fijar 1m)
            tf_sec = 60
            secs_left = 60 - sec

        if secs_left == tf_sec:
            secs_left = 0

        pct = int(((tf_sec - secs_left) / tf_sec) * 100) if tf_sec > 0 else 0
        self.progress_bar.setValue(pct)

        # VENTANA DE CONFIRMACIÓN Y ALERTA FINAL (ÚLTIMOS 5 SEGUNDOS: :55s - :59s)
        if 1 <= secs_left <= 5:
            if self.region and self.timer.isActive():
                self.analyze()

            sig = getattr(self, "_current_sig", "ESPERAR")
            self.alert_badge.setText(f"🚨 ¡ALERTA 1M EN {secs_left}s! ENTRAR EN: {sig} (1 MIN)")
            self.alert_badge.setStyleSheet("background: #dc2626; color: #ffffff; font-weight: 800; border-radius: 6px; padding: 4px; font-size: 11px;")
            self.countdown_label.setText(f"⏱️ Fin vela: {secs_left}s")
            self.countdown_label.setStyleSheet("background: #450a0a; color: #fca5a5; border: 1px solid #ef4444; border-radius: 6px; padding: 4px; font-size: 11px; font-weight: 800;")
            QApplication.beep()
        elif secs_left == 0:
            sig = getattr(self, "_current_sig", "ESPERAR")
            self.alert_badge.setText(f"🎯 ¡ENTRA AHORA EN LA VELA DE 1 MIN! ({sig})")
            self.alert_badge.setStyleSheet("background: #059669; color: #ffffff; font-weight: 900; border-radius: 6px; padding: 4px; font-size: 11px;")
            self.countdown_label.setText("🎯 ¡00s AHORA!")
            self.countdown_label.setStyleSheet("background: #022c22; color: #6ee7b7; border: 1px solid #10b981; border-radius: 6px; padding: 4px; font-size: 11px; font-weight: 800;")
            QApplication.beep()
        else:
            self.countdown_label.setText(f"⏳ Cierra en: {secs_left}s")
            self.countdown_label.setStyleSheet("background: #0f172a; color: #cbd5e1; border: 1px solid #1e293b; border-radius: 6px; padding: 4px 8px; font-size: 11px; font-weight: 600;")
            self.alert_badge.setText(f"🛡️ Análisis 5M + Señal 1M · Cierre en :{secs_left:02d}s")
            self.alert_badge.setStyleSheet("background: #0f172a; color: #94a3b8; border: 1px solid #1e293b; border-radius: 6px; padding: 3px 6px; font-size: 10px; font-weight: 600;")

    def tick_countdown(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            mins = self.remaining_seconds // 60
            secs = self.remaining_seconds % 60
            self.countdown_label.setText(f"⏳ Restante: {mins:02d}:{secs:02d}")
            if self.total_seconds > 0:
                pct = int((self.remaining_seconds / self.total_seconds) * 100)
                self.progress_bar.setValue(pct)
        else:
            self.countdown_timer.stop()
            self.countdown_label.setText("⏳ Tiempo cumplido")
            self.progress_bar.setValue(0)

    def analyze(self):
        if not self.region:
            return
        try:
            image = capture_region(self.region)
            result = analyze_chart(image)
            self.last_result = result
            
            next_c = result.get("next_candle", {})
            next_label = next_c.get("label", "🔮 PRÓXIMA VELA: EVALUANDO")
            self.next_candle_badge.setText(next_label)

            sig = result["signal"]
            if sig == "CALL":
                self.signal.setText("SUBIR (CALL)")
                self._current_sig = "SUBIR (CALL)"
            elif sig == "PUT":
                self.signal.setText("BAJAR (PUT)")
                self._current_sig = "BAJAR (PUT)"
            else:
                self.signal.setText("ESPERAR")
                self._current_sig = "ESPERAR"

            prob_call = result.get("prob_call", 50.0)
            prob_put = result.get("prob_put", 50.0)
            self.confidence.setText(f"Probabilidad Bayesiana: {result['confidence']}% · (🟢 {prob_call}% | 🔴 {prob_put}%)")
            self.update_signal_style(sig)

            # Determine duration based on user preference or AI recommendation
            mode_idx = self.time_mode.currentIndex()
            if mode_idx == 2:
                duration_label = "2 MIN"
                duration_sec = 120
            elif mode_idx == 3:
                duration_label = "3 MIN"
                duration_sec = 180
            elif mode_idx == 4:
                duration_label = "5 MIN"
                duration_sec = 300
            else:
                # Default MTF: 1 min signal
                duration_label = "1 MIN"
                duration_sec = 60

            if sig in ("CALL", "PUT"):
                if getattr(self, "_last_sig", "") != sig:
                    QApplication.beep()
                    self._last_sig = sig
                self.exp_badge.setText(f"⏱️ Tiempo: {duration_label}")
                self.time_val.setText(duration_label)
                # Restart countdown
                self.total_seconds = max(10, duration_sec)
                self.remaining_seconds = self.total_seconds
                self.progress_bar.setValue(100)
                self.countdown_timer.start()
                mins = self.remaining_seconds // 60
                secs = self.remaining_seconds % 60
                self.countdown_label.setText(f"⏳ Restante: {mins:02d}:{secs:02d}")
            else:
                self.exp_badge.setText("⏱️ Tiempo: Esperar")
                self.time_val.setText("—")
                self.countdown_label.setText("⏳ Restante: —")
                self.countdown_timer.stop()
                self.progress_bar.setValue(0)

            self.rsi_val.setText(str(result["rsi"]))
            self.trend_val.setText(result["trend"].capitalize())
            self.candles_val.setText(str(result["count"]))

            self.info_banner.setText(result["explanation"])
            if "agents" in result:
                self.update_agent_display(result["agents"])
            self.footer.setText(f"Actualizado: {result['time']}")
        except Exception as exc:
            self.status.setText("Alerta")
            self.info_banner.setText(f"Aviso de captura: {exc}")

    def update_agent_display(self, agents_dict):
        if not agents_dict:
            return
        cd = agents_dict.get("candles", {})
        tr = agents_dict.get("trend", {})
        mn = agents_dict.get("manipulation", {})
        cf = agents_dict.get("confluence", {})

        def fmt(tag, d):
            vote = d.get("vote", "—")
            detail = d.get("detail", d.get("status", ""))
            icon = "🟢" if vote == "CALL" else "🔴" if vote == "PUT" else "⚪"
            return f"{icon} {tag}: {vote} ({detail[:28]})"

        self.agent_candles.setText(fmt("Velas Anteriores", cd))
        self.agent_trend.setText(fmt("Tendencia Macro", tr))
        self.agent_manipulation.setText(fmt("Anti-Manipulación", mn))
        self.agent_confluence.setText(fmt("Confluencia Triple", cf))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MiniBot()
    window.show()
    sys.exit(app.exec())
