from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QFrame, QLabel, QLineEdit, QVBoxLayout

from .theme import apply_shadow


class GlassCard(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("glassCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        apply_shadow(self)


class MetricTile(QFrame):
    def __init__(self, caption: str, value: str, detail: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("metricTile")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        self.caption_label = QLabel(caption)
        self.caption_label.setObjectName("metricCaption")
        layout.addWidget(self.caption_label)

        self.value_label = QLabel(value)
        self.value_label.setObjectName("metricValue")
        layout.addWidget(self.value_label)

        self.detail_label = QLabel(detail)
        self.detail_label.setWordWrap(True)
        self.detail_label.setObjectName("metricDetail")
        layout.addWidget(self.detail_label)

    def set_content(self, caption: str, value: str, detail: str) -> None:
        self.caption_label.setText(caption)
        self.value_label.setText(value)
        self.detail_label.setText(detail)


class DropLineEdit(QLineEdit):
    pathDropped = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if not urls:
            super().dropEvent(event)
            return

        local_path = urls[0].toLocalFile()
        if local_path:
            self.setText(local_path)
            self.pathDropped.emit(local_path)
            event.acceptProposedAction()
            return

        super().dropEvent(event)
