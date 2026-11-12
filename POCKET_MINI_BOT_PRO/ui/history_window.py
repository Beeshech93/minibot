"""
Signal History and Performance Statistics Dialog for Pocket Mini Bot Pro.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QFrame, QGridLayout
)
from PySide6.QtCore import Qt
from app.statistics import StatisticsAggregator


class HistoryDialog(QDialog):
    """Visual dialog presenting signal log and historical win rate analytics."""

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.stats_aggregator = StatisticsAggregator(self.db)
        self.setWindowTitle("📜 Historial de Señales y Rendimiento")
        self.resize(340, 480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 1. Performance Overview Frame
        stats_frame = QFrame()
        stats_frame.setStyleSheet("background-color: #111827; border: 1px solid #1f2937; border-radius: 6px; padding: 6px;")
        grid = QGridLayout(stats_frame)
        grid.setSpacing(4)

        self.val_total = QLabel("0")
        self.val_calls = QLabel("0")
        self.val_puts = QLabel("0")
        self.val_wins = QLabel("0")
        self.val_losses = QLabel("0")
        self.val_wr = QLabel("0.0%")

        for lbl in (self.val_total, self.val_calls, self.val_puts, self.val_wins, self.val_losses, self.val_wr):
            lbl.setStyleSheet("font-weight: 800; color: #f8fafc;")

        grid.addWidget(QLabel("Total:"), 0, 0)
        grid.addWidget(self.val_total, 0, 1)
        grid.addWidget(QLabel("CALLs:"), 0, 2)
        grid.addWidget(self.val_calls, 0, 3)

        grid.addWidget(QLabel("PUTs:"), 1, 0)
        grid.addWidget(self.val_puts, 1, 1)
        grid.addWidget(QLabel("Wins:"), 1, 2)
        grid.addWidget(self.val_wins, 1, 3)

        grid.addWidget(QLabel("Losses:"), 2, 0)
        grid.addWidget(self.val_losses, 2, 1)
        grid.addWidget(QLabel("Win Rate:"), 2, 2)
        grid.addWidget(self.val_wr, 2, 3)

        layout.addWidget(stats_frame)

        # 2. Signals Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Hora", "Activo", "Señal", "Resultado"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #0b0f17;
                border: 1px solid #1e293b;
                gridline-color: #1e293b;
                color: #e2e8f0;
                font-size: 10px;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #94a3b8;
                font-weight: 700;
                border: none;
                padding: 4px;
            }
        """)
        layout.addWidget(self.table)

        # 3. Close Button
        btn_close = QPushButton("Cerrar")
        btn_close.setObjectName("secondaryBtn")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def load_data(self):
        summary = self.stats_aggregator.get_summary()
        self.val_total.setText(str(summary["total_signals"]))
        self.val_calls.setText(str(summary["calls"]))
        self.val_puts.setText(str(summary["puts"]))
        self.val_wins.setText(str(summary["wins"]))
        self.val_losses.setText(str(summary["losses"]))
        self.val_wr.setText(summary["display_win_rate"])

        signals = self.db.get_recent_signals(limit=25)
        self.table.setRowCount(len(signals))

        for row_idx, sig in enumerate(signals):
            ts = sig.get("timestamp", "")
            time_part = ts.split("T")[-1][:8] if "T" in ts else ts[-8:]
            sym = sig.get("symbol", "OTC")
            direction = sig.get("direction", "")
            outcome = sig.get("outcome", "—")

            item_time = QTableWidgetItem(time_part)
            item_sym = QTableWidgetItem(sym)
            item_dir = QTableWidgetItem(direction)
            item_out = QTableWidgetItem(outcome)

            for it in (item_time, item_sym, item_dir, item_out):
                it.setTextAlignment(Qt.AlignCenter)

            if direction == "CALL":
                item_dir.setForeground(Qt.green)
            elif direction == "PUT":
                item_dir.setForeground(Qt.red)

            if outcome == "WIN":
                item_out.setForeground(Qt.green)
            elif outcome == "LOSS":
                item_out.setForeground(Qt.red)

            self.table.setItem(row_idx, 0, item_time)
            self.table.setItem(row_idx, 1, item_sym)
            self.table.setItem(row_idx, 2, item_dir)
            self.table.setItem(row_idx, 3, item_out)
