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
        self.setFixedSize(340, 570)
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

        agents_header = QLabel("🤖 Consenso de Agentes IA (4 especialistas)")
        agents_header.setObjectName("agentsHeader")
        agents_layout.addWidget(agents_header)

        self.agent_pa = QLabel("• Acción del Precio: Esperando datos")
        self.agent_pa.setObjectName("agentRow")
        self.agent_st = QLabel("• Estructura S/R: Mapeando niveles")
        self.agent_st.setObjectName("agentRow")
        self.agent_ind = QLabel("• Indicadores & EMA: Calculando")
        self.agent_ind.setObjectName("agentRow")
        self.agent_mom = QLabel("• Volumen & Flujo: Monitoreando")
        self.agent_mom.setObjectName("agentRow")

        agents_layout.addWidget(self.agent_pa)
        agents_layout.addWidget(self.agent_st)
        agents_layout.addWidget(self.agent_ind)
        agents_layout.addWidget(self.agent_mom)
        root.addWidget(self.agents_frame)

        # Timeframe mode selector (Auto vs Fixed 1m, 2m, 3m, 5m)
        self.time_mode = QComboBox()
        self.time_mode.setObjectName("comboInput")
        self.time_mode.addItems([
            "⏱️ Tiempo: Automático (IA)",
            "⏱️ Fijar a 1 min (M1)",
            "⏱️ Fijar a 2 min (M2)",
            "⏱️ Fijar a 3 min (M3)",
            "⏱️ Fijar a 5 min (M5)"
        ])
        root.addWidget(self.time_mode)

        # Interval Selector
        self.interval = QComboBox()
        self.interval.setObjectName("comboInput")
        self.interval.addItems([
            "🔄 Análisis: Cada 5 segundos",
            "🔄 Análisis: Cada 10 segundos",
            "🔄 Análisis: Cada 15 segundos",
            "🔄 Análisis: Cada 30 segundos"
        ])
        root.addWidget(self.interval)

        # Action Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.pick_btn = QPushButton("🎯 Seleccionar")
        self.pick_btn.setObjectName("secondaryBtn")
        self.pick_btn.clicked.connect(self.pick_region)
        self.start_btn = QPushButton("▶ Iniciar")
        self.start_btn.setObjectName("primaryBtn")
        self.start_btn.clicked.connect(self.toggle)
        btn_row.addWidget(self.pick_btn)
        btn_row.addWidget(self.start_btn)
        root.addLayout(btn_row)

        sub_row = QHBoxLayout()
        sub_row.setSpacing(8)
        self.once_btn = QPushButton("⚡ Analizar")
        self.once_btn.setObjectName("subtleBtn")
        self.once_btn.clicked.connect(self.analyze)

        self.demo_btn = QPushButton("🧪 Probar Demo")
        self.demo_btn.setObjectName("demoBtn")
        self.demo_btn.clicked.connect(self.simulate_demo)

        sub_row.addWidget(self.once_btn)
        sub_row.addWidget(self.demo_btn)
        root.addLayout(sub_row)

        # Footer timestamp
        self.footer = QLabel("Sin capturas registradas")
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
            QLabel#signalText {
                font-size: 34px;
                font-weight: 800;
                letter-spacing: 1.5px;
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
            self.start_btn.setText("▶ Iniciar")
            self.status.setText("Pausado")
            return
        if not self.region:
            QMessageBox.information(self, "Seleccionar gráfico", "Pulsa «🎯 Seleccionar» y marca la zona de velas.")
            return
        intervals = [5, 10, 15, 30]
        seconds = intervals[self.interval.currentIndex()]
        self.timer.start(seconds * 1000)
        self.start_btn.setText("⏸ Pausar")
        self.status.setText("En vivo")
        self.analyze()

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
            sig = result["signal"]
            self.signal.setText(sig)
            self.confidence.setText(f"Confianza: {result['confidence']}%")
            self.update_signal_style(sig)

            # Determine duration based on user preference or AI recommendation
            mode_idx = self.time_mode.currentIndex()
            if mode_idx == 1:
                duration_label = "1 MIN"
                duration_sec = 60
            elif mode_idx == 2:
                duration_label = "2 MIN"
                duration_sec = 120
            elif mode_idx == 3:
                duration_label = "3 MIN"
                duration_sec = 180
            elif mode_idx == 4:
                duration_label = "5 MIN"
                duration_sec = 300
            else:
                duration_label = result.get("recommended_time", "1 MIN")
                duration_sec = result.get("duration_seconds", 60)

            if sig in ("CALL", "PUT"):
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
        pa = agents_dict.get("price_action", {})
        st = agents_dict.get("structure", {})
        ind = agents_dict.get("indicators", {})
        mom = agents_dict.get("momentum", {})

        def fmt(tag, d, key):
            vote = d.get("vote", "—")
            sub = d.get(key, d.get("reason", ""))
            icon = "🟢" if vote == "CALL" else "🔴" if vote == "PUT" else "⚪"
            return f"{icon} {tag}: {vote} ({sub[:28]})"

        self.agent_pa.setText(fmt("Patrones", pa, "pattern"))
        self.agent_st.setText(fmt("Estructura S/R", st, "zone"))
        self.agent_ind.setText(fmt("Indicadores", ind, "reason"))
        self.agent_mom.setText(fmt("Flujo/Volumen", mom, "state"))

    def simulate_demo(self):
        is_call = getattr(self, "_demo_toggle", False)
        self._demo_toggle = not is_call
        sig = "CALL" if is_call else "PUT"
        conf = random.randint(78, 88)
        rsi = random.uniform(32.0, 44.0) if sig == "CALL" else random.uniform(62.0, 76.0)
        trend = "Alcista" if sig == "CALL" else "Bajista"
        candles = random.randint(22, 35)

        mode_idx = self.time_mode.currentIndex()
        if mode_idx == 1:
            dur_label, dur_sec = "1 MIN", 60
        elif mode_idx == 2:
            dur_label, dur_sec = "2 MIN", 120
        elif mode_idx == 3:
            dur_label, dur_sec = "3 MIN", 180
        elif mode_idx == 4:
            dur_label, dur_sec = "5 MIN", 300
        else:
            dur_label, dur_sec = random.choice([("1 MIN", 60), ("2 MIN", 120), ("5 MIN", 300)])

        self.signal.setText(sig)
        self.confidence.setText(f"Confianza: {conf}%")
        self.update_signal_style(sig)

        self.exp_badge.setText(f"⏱️ Tiempo: {dur_label}")
        self.time_val.setText(dur_label)
        self.rsi_val.setText(f"{rsi:.1f}")
        self.trend_val.setText(trend)
        self.candles_val.setText(str(candles))

        self.status.setText("Modo Demo")
        self.info_banner.setText(f"Simulación de prueba: Señal {sig} a {dur_label} con tendencia {trend.lower()}.")
        self.footer.setText(f"Prueba: {datetime.now().strftime('%H:%M:%S')}")

        # Start countdown
        self.total_seconds = dur_sec
        self.remaining_seconds = dur_sec
        self.progress_bar.setValue(100)
        self.countdown_timer.start()
        mins = self.remaining_seconds // 60
        secs = self.remaining_seconds % 60
        self.countdown_label.setText(f"⏳ Restante: {mins:02d}:{secs:02d}")

        # Update Agent Display in Demo
        pa_pat = "Martillo Alcista" if sig == "CALL" else "Estrella Fugaz"
        st_zone = "Rebote en Soporte" if sig == "CALL" else "Rechazo en Resistencia"
        ind_txt = "EMA9 > EMA21 > EMA50" if sig == "CALL" else "EMA9 < EMA21 < EMA50"
        self.update_agent_display({
            "price_action": {"vote": sig, "pattern": pa_pat},
            "structure": {"vote": sig, "zone": st_zone},
            "indicators": {"vote": sig, "reason": ind_txt},
            "momentum": {"vote": sig, "state": "Intención Institucional"}
        })

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MiniBot()
    window.show()
    sys.exit(app.exec())
