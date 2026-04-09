from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget


def build_stylesheet() -> str:
    return """
    QWidget#appRoot {
        background:
            qradialgradient(cx: 0.15, cy: 0.1, radius: 0.9, fx: 0.15, fy: 0.1,
                stop: 0 rgba(206, 229, 255, 255),
                stop: 0.45 rgba(241, 246, 252, 255),
                stop: 1 rgba(232, 238, 245, 255));
        color: #152238;
    }

    QFrame#glassCard {
        background-color: rgba(255, 255, 255, 214);
        border: 1px solid rgba(255, 255, 255, 185);
        border-radius: 26px;
    }

    QFrame#metricTile {
        background-color: rgba(248, 251, 255, 228);
        border: 1px solid rgba(198, 212, 230, 150);
        border-radius: 20px;
    }

    QLabel#heroTitle {
        font-size: 28px;
        font-weight: 700;
        color: #112036;
    }

    QLabel#heroSubtitle {
        font-size: 13px;
        color: rgba(17, 32, 54, 175);
    }

    QLabel#sectionTitle {
        font-size: 16px;
        font-weight: 700;
        color: #112036;
    }

    QLabel#sectionHint {
        font-size: 12px;
        color: rgba(17, 32, 54, 160);
    }

    QLabel#badge {
        padding: 6px 12px;
        border-radius: 14px;
        font-size: 12px;
        font-weight: 600;
        color: #143861;
        background-color: rgba(220, 230, 244, 210);
        border: 1px solid rgba(181, 196, 216, 160);
    }

    QLabel#badge[badgeVariant="success"] {
        color: #0a5a44;
        background-color: rgba(207, 244, 233, 225);
        border: 1px solid rgba(149, 217, 194, 190);
    }

    QLabel#badge[badgeVariant="warning"] {
        color: #7c4700;
        background-color: rgba(255, 238, 209, 230);
        border: 1px solid rgba(241, 206, 142, 195);
    }

    QLabel#badge[badgeVariant="danger"] {
        color: #8a2438;
        background-color: rgba(255, 223, 230, 230);
        border: 1px solid rgba(239, 177, 191, 195);
    }

    QLabel#metricCaption {
        font-size: 11px;
        font-weight: 600;
        color: rgba(21, 34, 56, 145);
    }

    QLabel#metricValue {
        font-size: 22px;
        font-weight: 700;
        color: #102036;
    }

    QLabel#metricDetail,
    QLabel#infoLabel,
    QLabel#helperLabel {
        font-size: 12px;
        color: rgba(16, 32, 54, 165);
    }

    QLabel#statusLabel {
        font-size: 13px;
        font-weight: 600;
        color: #102036;
    }

    QLineEdit,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox {
        min-height: 22px;
        padding: 10px 12px;
        border-radius: 15px;
        border: 1px solid rgba(173, 188, 211, 165);
        background-color: rgba(248, 251, 255, 235);
        color: #102036;
        selection-background-color: rgba(0, 122, 255, 155);
    }

    QLineEdit:hover,
    QComboBox:hover,
    QSpinBox:hover,
    QDoubleSpinBox:hover {
        border: 1px solid rgba(120, 152, 197, 185);
        background-color: rgba(252, 254, 255, 240);
    }

    QLineEdit:focus,
    QComboBox:focus,
    QSpinBox:focus,
    QDoubleSpinBox:focus {
        border: 1px solid rgba(0, 122, 255, 200);
        background-color: rgba(255, 255, 255, 245);
    }

    QPushButton {
        min-height: 20px;
        padding: 11px 16px;
        border-radius: 16px;
        font-size: 13px;
        font-weight: 600;
    }

    QPushButton#primaryButton {
        color: white;
        border: none;
        background:
            qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 #1186ff,
                stop: 0.55 #0f6bff,
                stop: 1 #31b4ff);
    }

    QPushButton#primaryButton:hover {
        background:
            qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 #2d97ff,
                stop: 0.55 #217bff,
                stop: 1 #4bc0ff);
    }

    QPushButton#secondaryButton {
        color: #12345b;
        border: 1px solid rgba(170, 188, 210, 170);
        background-color: rgba(255, 255, 255, 205);
    }

    QPushButton#secondaryButton:hover {
        background-color: rgba(255, 255, 255, 235);
        border: 1px solid rgba(137, 166, 201, 190);
    }

    QCheckBox {
        spacing: 8px;
        color: #12345b;
    }

    QCheckBox::indicator {
        width: 20px;
        height: 20px;
        border-radius: 10px;
        border: 1px solid rgba(170, 188, 210, 180);
        background-color: rgba(248, 251, 255, 235);
    }

    QCheckBox::indicator:checked {
        border: none;
        background-color: #0f76ff;
    }

    QProgressBar {
        min-height: 16px;
        border-radius: 10px;
        padding: 2px;
        border: 1px solid rgba(178, 197, 220, 170);
        background-color: rgba(244, 248, 252, 230);
        text-align: center;
        color: rgba(16, 32, 54, 170);
    }

    QProgressBar::chunk {
        border-radius: 8px;
        background:
            qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 #86d5ff,
                stop: 0.45 #43a5ff,
                stop: 1 #0f76ff);
    }
    """


def apply_shadow(widget: QWidget, blur_radius: int = 28, y_offset: int = 10) -> None:
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur_radius)
    shadow.setOffset(0, y_offset)
    shadow.setColor(QColor(22, 35, 58, 38))
    widget.setGraphicsEffect(shadow)
