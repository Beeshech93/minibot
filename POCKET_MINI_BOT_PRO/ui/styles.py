"""
Dark Trading UI Stylesheets for PySide6 (Pocket Mini Bot Pro).
Optimized for 350x500 px compact layout.
"""

MAIN_STYLESHEET = """
QWidget {
    background-color: #0b0f17;
    color: #e2e8f0;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 11px;
}

/* Header */
QFrame#headerFrame {
    background-color: #111827;
    border-bottom: 1px solid #1f2937;
    padding: 2px 4px;
}
QLabel#appTitle {
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.8px;
    color: #38bdf8;
}
QLabel#statusBadge {
    background-color: #1e293b;
    color: #94a3b8;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 2px 6px;
    font-size: 9px;
    font-weight: 700;
}
QLabel#modeBadge {
    background-color: #312e81;
    color: #c7d2fe;
    border: 1px solid #4338ca;
    border-radius: 8px;
    padding: 2px 6px;
    font-size: 9px;
    font-weight: 700;
}

/* Main Signal Card */
QFrame#signalCard {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 10px;
    padding: 6px;
}
QFrame#signalCard.CALL {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #064e3b, stop:1 #022c22);
    border: 1.5px solid #10b981;
}
QFrame#signalCard.PUT {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4c0519, stop:1 #2e0814);
    border: 1.5px solid #f43f5e;
}
QLabel#signalText {
    font-size: 20px;
    font-weight: 900;
    letter-spacing: 1px;
    color: #f1f5f9;
}
QLabel#scoreText {
    font-size: 11px;
    font-weight: 700;
    color: #94a3b8;
}
QLabel#timeBadge, QLabel#countdownBadge {
    background-color: #0f172a;
    color: #cbd5e1;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 3px 6px;
    font-size: 10px;
    font-weight: 600;
}

/* Metrics Grid Tiles */
QFrame#tile {
    background-color: #111827;
    border: 1px solid #1f2937;
    border-radius: 6px;
    padding: 4px 2px;
}
QLabel#tileTitle {
    font-size: 8px;
    font-weight: 700;
    color: #64748b;
    letter-spacing: 0.5px;
}
QLabel#tileVal {
    font-size: 11px;
    font-weight: 800;
    color: #f8fafc;
}

/* Indicators 6-Filter Panel */
QFrame#filtersPanel {
    background-color: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 6px;
}
QLabel#filtersHeader {
    font-size: 9px;
    font-weight: 800;
    color: #818cf8;
    letter-spacing: 0.5px;
}
QLabel#filterRow {
    font-size: 9px;
    color: #94a3b8;
}

/* Alert / Reason Banner */
QLabel#reasonBanner {
    background-color: #111827;
    border: 1px solid #1f2937;
    border-left: 3px solid #38bdf8;
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 9px;
    color: #cbd5e1;
    line-height: 1.2;
}

/* Buttons */
QPushButton {
    border-radius: 6px;
    font-size: 10px;
    font-weight: 700;
    padding: 6px;
}
QPushButton#primaryBtn {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
}
QPushButton#primaryBtn:hover {
    background-color: #1d4ed8;
}
QPushButton#secondaryBtn {
    background-color: #1e293b;
    color: #e2e8f0;
    border: 1px solid #334155;
}
QPushButton#secondaryBtn:hover {
    background-color: #334155;
}
QPushButton#subtleBtn {
    background-color: transparent;
    color: #94a3b8;
    border: 1px solid #1e293b;
}
QPushButton#subtleBtn:hover {
    background-color: #1e293b;
    color: #f1f5f9;
}

/* Input & Combos */
QComboBox {
    background-color: #111827;
    border: 1px solid #1f2937;
    border-radius: 6px;
    padding: 3px 6px;
    color: #e2e8f0;
    font-size: 10px;
    font-weight: 600;
}
QComboBox::drop-down {
    border: none;
}
QComboBox QAbstractItemView {
    background-color: #111827;
    color: #f1f5f9;
    selection-background-color: #2563eb;
}

/* Progress bar */
QProgressBar {
    background-color: #1e293b;
    border: none;
    border-radius: 2px;
    height: 3px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #38bdf8;
    border-radius: 2px;
}
"""

