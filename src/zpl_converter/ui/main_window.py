from __future__ import annotations

import platform
from pathlib import Path

from PySide6.QtCore import QObject, QSettings, Qt, QThread, QUrl, Signal
from PySide6.QtGui import QCloseEvent, QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from ..conversion import convert_zpl
from ..models import (
    APP_DISPLAY_NAME,
    APP_NAME,
    APP_ORGANIZATION,
    ConversionConfig,
    ConversionResult,
    PRESET_SIZES,
    QUALITY_SCALES,
)
from ..runtime import get_runtime_status
from ..zpl_parser import analyze_zpl_text
from .theme import build_stylesheet
from .widgets import DropLineEdit, GlassCard, MetricTile


class ConversionWorker(QObject):
    progress = Signal(int, str)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, config: ConversionConfig):
        super().__init__()
        self.config = config

    def run(self) -> None:
        try:
            result = convert_zpl(self.config, progress=self.progress.emit)
            self.finished.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))


def format_platform_name() -> str:
    system_name = platform.system()
    if system_name == "Darwin":
        return "macOS"
    return system_name or "Sistema"


def set_badge_variant(label: QLabel, variant: str) -> None:
    label.setProperty("badgeVariant", variant)
    style = label.style()
    style.unpolish(label)
    style.polish(label)


def suggest_output_paths(file_path: str) -> tuple[str, str]:
    source = Path(file_path)
    stem = source.stem or "etiquetas"
    base_dir = source.parent if source.parent.exists() else Path.cwd()
    return (
        str(base_dir / f"{stem}_png"),
        str(base_dir / f"{stem}_etiquetas.pdf"),
    )


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_DISPLAY_NAME)
        self.setMinimumSize(980, 760)
        if platform.system() == "Darwin":
            self.setUnifiedTitleAndToolBarOnMac(True)

        self.settings = QSettings(APP_ORGANIZATION, APP_NAME)
        self.worker_thread: QThread | None = None
        self.worker: ConversionWorker | None = None
        self.last_result: ConversionResult | None = None
        self.last_png_output = ""
        self.last_pdf_output = ""
        self.current_stats_labels = 0
        self.current_total_quantity = 0

        root = QWidget()
        root.setObjectName("appRoot")
        root.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCentralWidget(root)
        self.setStyleSheet(build_stylesheet())

        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(22, 22, 22, 22)
        main_layout.setSpacing(18)

        main_layout.addWidget(self.build_header_card())

        content_layout = QHBoxLayout()
        content_layout.setSpacing(18)
        content_layout.addWidget(self.build_file_card(), 6)
        content_layout.addWidget(self.build_options_card(), 5)
        main_layout.addLayout(content_layout)

        main_layout.addWidget(self.build_footer_card())

        self.connect_live_updates()
        self.load_settings()
        self.refresh_runtime_status()
        self.refresh_file_summary()
        self.refresh_live_summary()

    def build_header_card(self) -> GlassCard:
        card = GlassCard()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        title_column = QVBoxLayout()
        title_column.setSpacing(6)

        title = QLabel("Local, rápido y listo para distribución")
        title.setObjectName("heroTitle")
        title_column.addWidget(title)

        subtitle = QLabel(
            "Conversión ZPL a PDF o PNG con renderer local, resumen en vivo y "
            "una interfaz inspirada en la estética translúcida de macOS Tahoe."
        )
        subtitle.setWordWrap(True)
        subtitle.setObjectName("heroSubtitle")
        title_column.addWidget(subtitle)
        top_row.addLayout(title_column, 1)

        badge_row = QHBoxLayout()
        badge_row.setSpacing(8)

        self.runtime_badge = QLabel("Motor")
        self.runtime_badge.setObjectName("badge")
        badge_row.addWidget(self.runtime_badge)

        self.platform_badge = QLabel(format_platform_name())
        self.platform_badge.setObjectName("badge")
        set_badge_variant(self.platform_badge, "success")
        badge_row.addWidget(self.platform_badge)

        self.version_badge = QLabel(f"v{__version__}")
        self.version_badge.setObjectName("badge")
        badge_row.addWidget(self.version_badge)

        top_row.addLayout(badge_row)
        layout.addLayout(top_row)

        self.runtime_detail_label = QLabel("")
        self.runtime_detail_label.setObjectName("infoLabel")
        self.runtime_detail_label.setWordWrap(True)
        layout.addWidget(self.runtime_detail_label)
        return card

    def build_file_card(self) -> GlassCard:
        card = GlassCard()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        title = QLabel("Entrada y salida")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        hint = QLabel("Arrastra un archivo `.txt`, ajusta el destino y deja que la app recuerde tus ultimas rutas.")
        hint.setObjectName("sectionHint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        file_caption = QLabel("Archivo ZPL")
        file_caption.setObjectName("helperLabel")
        layout.addWidget(file_caption)

        file_row = QHBoxLayout()
        file_row.setSpacing(10)
        self.file_input = DropLineEdit()
        self.file_input.setPlaceholderText("Arrastra aqui el archivo .txt o escribe una ruta")
        file_row.addWidget(self.file_input, 1)

        self.browse_file_btn = QPushButton("Seleccionar")
        self.browse_file_btn.setObjectName("secondaryButton")
        file_row.addWidget(self.browse_file_btn)
        layout.addLayout(file_row)

        self.file_summary_label = QLabel("Selecciona un archivo para ver cuantas etiquetas se detectan.")
        self.file_summary_label.setObjectName("infoLabel")
        self.file_summary_label.setWordWrap(True)
        layout.addWidget(self.file_summary_label)

        output_grid = QGridLayout()
        output_grid.setHorizontalSpacing(12)
        output_grid.setVerticalSpacing(10)

        format_label = QLabel("Formato de salida")
        format_label.setObjectName("helperLabel")
        output_grid.addWidget(format_label, 0, 0)

        self.format_input = QComboBox()
        self.format_input.addItems(["pdf", "png"])
        output_grid.addWidget(self.format_input, 0, 1)

        path_label = QLabel("Destino")
        path_label.setObjectName("helperLabel")
        output_grid.addWidget(path_label, 1, 0)

        path_row = QHBoxLayout()
        path_row.setSpacing(10)
        self.output_input = QLineEdit()
        self.output_input.setPlaceholderText("Ruta del PDF o carpeta para PNG")
        path_row.addWidget(self.output_input, 1)

        self.browse_output_btn = QPushButton("Explorar")
        self.browse_output_btn.setObjectName("secondaryButton")
        path_row.addWidget(self.browse_output_btn)
        output_grid.addLayout(path_row, 1, 1)

        prefix_label = QLabel("Prefijo PNG")
        prefix_label.setObjectName("helperLabel")
        output_grid.addWidget(prefix_label, 2, 0)

        self.png_prefix_input = QLineEdit("etiqueta")
        output_grid.addWidget(self.png_prefix_input, 2, 1)

        layout.addLayout(output_grid)

        action_row = QHBoxLayout()
        action_row.setSpacing(10)

        self.suggest_output_btn = QPushButton("Ruta sugerida")
        self.suggest_output_btn.setObjectName("secondaryButton")
        action_row.addWidget(self.suggest_output_btn)

        self.open_output_checkbox = QCheckBox("Abrir resultado al terminar")
        action_row.addWidget(self.open_output_checkbox)
        action_row.addStretch(1)
        layout.addLayout(action_row)
        return card

    def build_options_card(self) -> GlassCard:
        card = GlassCard()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        title = QLabel("Render y composición")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        hint = QLabel(
            "Ajusta tamaño, densidad y cantidad de canales. El resumen se recalcula en vivo para reducir errores antes de exportar."
        )
        hint.setObjectName("sectionHint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        preset_label = QLabel("Preset de etiqueta")
        preset_label.setObjectName("helperLabel")
        grid.addWidget(preset_label, 0, 0)

        self.size_preset = QComboBox()
        self.size_preset.addItems(PRESET_SIZES.keys())
        grid.addWidget(self.size_preset, 0, 1, 1, 3)

        width_label = QLabel("Ancho (in)")
        width_label.setObjectName("helperLabel")
        grid.addWidget(width_label, 1, 0)

        self.width_input = QDoubleSpinBox()
        self.width_input.setRange(0.5, 20.0)
        self.width_input.setDecimals(2)
        self.width_input.setSingleStep(0.1)
        self.width_input.setValue(4.0)
        grid.addWidget(self.width_input, 1, 1)

        height_label = QLabel("Alto (in)")
        height_label.setObjectName("helperLabel")
        grid.addWidget(height_label, 1, 2)

        self.height_input = QDoubleSpinBox()
        self.height_input.setRange(0.5, 20.0)
        self.height_input.setDecimals(2)
        self.height_input.setSingleStep(0.1)
        self.height_input.setValue(6.0)
        grid.addWidget(self.height_input, 1, 3)

        dpmm_label = QLabel("Resolución (dpmm)")
        dpmm_label.setObjectName("helperLabel")
        grid.addWidget(dpmm_label, 2, 0)

        self.dpmm_input = QSpinBox()
        self.dpmm_input.setRange(6, 48)
        self.dpmm_input.setValue(12)
        grid.addWidget(self.dpmm_input, 2, 1)

        quality_label = QLabel("Calidad de render")
        quality_label.setObjectName("helperLabel")
        grid.addWidget(quality_label, 2, 2)

        self.quality_input = QComboBox()
        self.quality_input.addItems(QUALITY_SCALES.keys())
        self.quality_input.setCurrentText("Alta (2x recomendada)")
        grid.addWidget(self.quality_input, 2, 3)

        channels_label = QLabel("Canales por fila")
        channels_label.setObjectName("helperLabel")
        grid.addWidget(channels_label, 3, 0)

        self.channels_input = QSpinBox()
        self.channels_input.setRange(1, 6)
        self.channels_input.setValue(1)
        grid.addWidget(self.channels_input, 3, 1)
        layout.addLayout(grid)

        metrics_title = QLabel("Resumen en vivo")
        metrics_title.setObjectName("helperLabel")
        layout.addWidget(metrics_title)

        metrics_grid = QGridLayout()
        metrics_grid.setHorizontalSpacing(12)
        metrics_grid.setVerticalSpacing(12)

        self.labels_tile = MetricTile("ETIQUETAS", "--", "Sin archivo cargado")
        metrics_grid.addWidget(self.labels_tile, 0, 0)

        self.quantity_tile = MetricTile("COPIAS", "--", "Sin analizar")
        metrics_grid.addWidget(self.quantity_tile, 0, 1)

        self.quality_tile = MetricTile("CALIDAD", "--", "Resolución efectiva")
        metrics_grid.addWidget(self.quality_tile, 1, 0)

        self.output_tile = MetricTile("SALIDA", "--", "Formato y composición")
        metrics_grid.addWidget(self.output_tile, 1, 1)
        layout.addLayout(metrics_grid)

        self.live_hint_label = QLabel(
            "Consejo: para texto más nítido, sube la resolución o usa la calidad Alta/Ultra antes de exportar."
        )
        self.live_hint_label.setObjectName("infoLabel")
        self.live_hint_label.setWordWrap(True)
        layout.addWidget(self.live_hint_label)

        layout.addStretch(1)
        return card

    def build_footer_card(self) -> GlassCard:
        card = GlassCard()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        self.status_label = QLabel("Listo para convertir.")
        self.status_label.setObjectName("statusLabel")
        layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        footer_row = QHBoxLayout()
        footer_row.setSpacing(10)

        self.footer_hint_label = QLabel(
            "Compatibilidad mantenida para Windows y macOS. El build puede usar Node embebido o externo."
        )
        self.footer_hint_label.setObjectName("infoLabel")
        self.footer_hint_label.setWordWrap(True)
        self.footer_hint_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        footer_row.addWidget(self.footer_hint_label, 1)

        self.open_last_output_btn = QPushButton("Abrir salida")
        self.open_last_output_btn.setObjectName("secondaryButton")
        self.open_last_output_btn.setEnabled(False)
        footer_row.addWidget(self.open_last_output_btn)

        self.convert_btn = QPushButton("Convertir")
        self.convert_btn.setObjectName("primaryButton")
        footer_row.addWidget(self.convert_btn)

        layout.addLayout(footer_row)
        return card

    def connect_live_updates(self) -> None:
        self.browse_file_btn.clicked.connect(self.select_file)
        self.browse_output_btn.clicked.connect(self.select_output)
        self.suggest_output_btn.clicked.connect(self.apply_suggested_output_path)
        self.open_last_output_btn.clicked.connect(self.open_last_output)
        self.convert_btn.clicked.connect(self.start_conversion)

        self.file_input.pathDropped.connect(self.on_file_selected)
        self.file_input.textChanged.connect(self.on_file_selected)
        self.output_input.textChanged.connect(self.on_output_changed)
        self.format_input.currentTextChanged.connect(self.on_format_changed)
        self.size_preset.currentTextChanged.connect(self.on_size_preset_changed)

        self.width_input.valueChanged.connect(self.refresh_live_summary)
        self.height_input.valueChanged.connect(self.refresh_live_summary)
        self.dpmm_input.valueChanged.connect(self.refresh_live_summary)
        self.quality_input.currentTextChanged.connect(self.refresh_live_summary)
        self.channels_input.valueChanged.connect(self.refresh_live_summary)
        self.format_input.currentTextChanged.connect(self.refresh_live_summary)

    def refresh_runtime_status(self) -> None:
        status = get_runtime_status()
        self.runtime_badge.setText(status.description)
        self.runtime_detail_label.setText(status.detail)
        if status.available and status.using_embedded_runtime:
            set_badge_variant(self.runtime_badge, "success")
        elif status.available:
            set_badge_variant(self.runtime_badge, "warning")
        else:
            set_badge_variant(self.runtime_badge, "danger")

    def select_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo ZPL",
            self.file_input.text().strip(),
            "Text files (*.txt);;All files (*.*)",
        )
        if file_path:
            self.file_input.setText(file_path)

    def select_output(self) -> None:
        if self.format_input.currentText() == "png":
            output_dir = QFileDialog.getExistingDirectory(
                self,
                "Seleccionar carpeta destino",
                self.output_input.text().strip(),
            )
            if output_dir:
                self.output_input.setText(output_dir)
        else:
            output_file, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar PDF",
                self.output_input.text().strip() or "etiquetas.pdf",
                "PDF files (*.pdf)",
            )
            if output_file:
                self.output_input.setText(output_file)

    def on_file_selected(self, _: str) -> None:
        self.apply_suggested_output_path(only_if_empty=True)
        self.refresh_file_summary()
        self.refresh_live_summary()

    def on_output_changed(self, text: str) -> None:
        if self.format_input.currentText() == "png":
            self.last_png_output = text.strip()
        else:
            self.last_pdf_output = text.strip()
        self.refresh_live_summary()

    def on_size_preset_changed(self, selected: str) -> None:
        size = PRESET_SIZES[selected]
        is_custom = size is None
        self.width_input.setEnabled(is_custom)
        self.height_input.setEnabled(is_custom)
        if size is not None:
            self.width_input.setValue(size[0])
            self.height_input.setValue(size[1])
        self.refresh_live_summary()

    def on_format_changed(self, output_format: str) -> None:
        is_png = output_format == "png"
        self.png_prefix_input.setEnabled(is_png)
        self.png_prefix_input.setVisible(is_png)
        self.output_input.setPlaceholderText(
            "Carpeta destino para PNG" if is_png else "Ruta destino para el PDF"
        )

        remembered = self.last_png_output if is_png else self.last_pdf_output
        if remembered:
            self.output_input.setText(remembered)
        else:
            self.apply_suggested_output_path(only_if_empty=False)

        self.refresh_live_summary()

    def apply_suggested_output_path(self, only_if_empty: bool = False) -> None:
        file_path = self.file_input.text().strip()
        if not file_path:
            return

        current_output = self.output_input.text().strip()
        if only_if_empty and current_output:
            return

        png_output, pdf_output = suggest_output_paths(file_path)
        self.output_input.setText(
            (self.last_png_output or png_output)
            if self.format_input.currentText() == "png"
            else (self.last_pdf_output or pdf_output)
        )

    def refresh_file_summary(self) -> None:
        file_path = self.file_input.text().strip()
        if not file_path:
            self.file_summary_label.setText("Selecciona un archivo para inspeccionar su contenido ZPL.")
            self.current_stats_labels = 0
            self.current_total_quantity = 0
            return

        source = Path(file_path)
        if not source.is_file():
            self.file_summary_label.setText("La ruta indicada no existe o no es un archivo.")
            self.current_stats_labels = 0
            self.current_total_quantity = 0
            return

        try:
            content = source.read_text(encoding="utf-8", errors="replace")
            stats = analyze_zpl_text(content)
        except OSError as exc:
            self.file_summary_label.setText(f"No se pudo leer el archivo: {exc}")
            self.current_stats_labels = 0
            self.current_total_quantity = 0
            return

        self.current_stats_labels = stats.label_count
        self.current_total_quantity = stats.total_quantity
        size_kb = source.stat().st_size / 1024
        quantity_note = "con ^PQ" if stats.has_quantity_commands else "sin ^PQ"
        self.file_summary_label.setText(
            f"{stats.label_count} etiquetas detectadas, {stats.total_quantity} salidas estimadas, "
            f"{size_kb:.1f} KB y {quantity_note}."
        )

    def refresh_live_summary(self) -> None:
        quality_scale = QUALITY_SCALES[self.quality_input.currentText()]
        effective_dpmm = self.dpmm_input.value() * quality_scale
        effective_dpi = effective_dpmm * 25.4
        width_mm = self.width_input.value() * 25.4
        height_mm = self.height_input.value() * 25.4
        channels = self.channels_input.value()

        self.labels_tile.set_content(
            "ETIQUETAS",
            str(self.current_stats_labels or "--"),
            "ZPL detectadas en el archivo actual",
        )
        self.quantity_tile.set_content(
            "COPIAS",
            str(self.current_total_quantity or "--"),
            "Cantidad total considerando ^PQ",
        )
        self.quality_tile.set_content(
            "CALIDAD",
            f"{effective_dpi:.0f} DPI",
            f"{effective_dpmm} dpmm efectivos · {width_mm:.1f} x {height_mm:.1f} mm",
        )

        output_mode = self.format_input.currentText().upper()
        channel_text = "fila unica" if channels == 1 else f"{channels} canales por fila"
        output_target = self.output_input.text().strip() or "sin destino"
        self.output_tile.set_content(
            "SALIDA",
            output_mode,
            f"{channel_text} · {Path(output_target).name or output_target}",
        )

        if effective_dpi >= 900:
            self.live_hint_label.setText(
                "Modo Ultra: obtendras una salida muy nítida, pero con archivos más pesados y tiempos mayores."
            )
        elif channels > 1:
            self.live_hint_label.setText(
                "Modo multicanal activo: la app agrupara etiquetas horizontalmente antes de exportar."
            )
        else:
            self.live_hint_label.setText(
                "Consejo: para texto más nítido, sube la resolución o usa la calidad Alta/Ultra antes de exportar."
            )

    def start_conversion(self) -> None:
        file_path = self.file_input.text().strip()
        output_path = self.output_input.text().strip()
        output_format = self.format_input.currentText()
        png_prefix = self.png_prefix_input.text().strip() or "etiqueta"

        if not file_path or not Path(file_path).is_file():
            QMessageBox.warning(self, "Falta archivo", "Selecciona un archivo .txt valido.")
            return

        if not output_path:
            if output_format == "png":
                QMessageBox.warning(self, "Falta destino", "Selecciona una carpeta destino para PNG.")
            else:
                QMessageBox.warning(self, "Falta destino", "Selecciona la ruta de salida del PDF.")
            return

        config = ConversionConfig(
            file_path=file_path,
            width_in=self.width_input.value(),
            height_in=self.height_input.value(),
            dpmm=self.dpmm_input.value(),
            quality_scale=QUALITY_SCALES[self.quality_input.currentText()],
            channels_per_row=self.channels_input.value(),
            output_format=output_format,
            output_path=output_path,
            png_prefix=png_prefix,
            open_output_on_complete=self.open_output_checkbox.isChecked(),
        )
        self.run_worker(config)

    def run_worker(self, config: ConversionConfig) -> None:
        self.convert_btn.setEnabled(False)
        self.open_last_output_btn.setEnabled(False)
        self.progress.setValue(0)
        self.status_label.setText("Iniciando conversion...")

        self.worker_thread = QThread(self)
        self.worker = ConversionWorker(config)
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.failed.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.cleanup_worker)

        self.worker_thread.start()

    def cleanup_worker(self) -> None:
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
        if self.worker_thread:
            self.worker_thread.deleteLater()
            self.worker_thread = None
        self.convert_btn.setEnabled(True)

    def on_progress(self, value: int, text: str) -> None:
        self.progress.setValue(value)
        self.status_label.setText(text)

    def on_finished(self, result: ConversionResult) -> None:
        self.last_result = result
        self.progress.setValue(100)
        self.status_label.setText("Conversión finalizada.")
        self.open_last_output_btn.setEnabled(True)

        if result.output_format == "png":
            self.last_png_output = result.output_path
        else:
            self.last_pdf_output = result.output_path

        QMessageBox.information(self, "Listo", result.message)

        if self.open_output_checkbox.isChecked():
            self.open_output(result.output_path)

    def on_failed(self, error_message: str) -> None:
        self.status_label.setText("Error durante la conversion.")
        QMessageBox.critical(self, "Error", error_message)

    def open_output(self, output_path: str) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(output_path).resolve())))

    def open_last_output(self) -> None:
        if self.last_result:
            self.open_output(self.last_result.output_path)

    def load_settings(self) -> None:
        geometry = self.settings.value("window/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)

        self.file_input.setText(self.settings.value("paths/file_path", "", str))
        self.last_png_output = self.settings.value("paths/png_output", "", str)
        self.last_pdf_output = self.settings.value("paths/pdf_output", "", str)
        self.output_input.setText(self.settings.value("paths/current_output", "", str))

        self.size_preset.setCurrentText(self.settings.value("options/size_preset", "4 x 6 in (envios)", str))
        self.width_input.setValue(float(self.settings.value("options/width_in", 4.0)))
        self.height_input.setValue(float(self.settings.value("options/height_in", 6.0)))
        self.dpmm_input.setValue(int(self.settings.value("options/dpmm", 12)))
        self.quality_input.setCurrentText(self.settings.value("options/quality", "Alta (2x recomendada)", str))
        self.channels_input.setValue(int(self.settings.value("options/channels", 1)))
        self.format_input.setCurrentText(self.settings.value("options/output_format", "pdf", str))
        self.png_prefix_input.setText(self.settings.value("options/png_prefix", "etiqueta", str))
        self.open_output_checkbox.setChecked(self.settings.value("options/open_output", False, bool))
        self.on_format_changed(self.format_input.currentText())

    def save_settings(self) -> None:
        self.settings.setValue("window/geometry", self.saveGeometry())
        self.settings.setValue("paths/file_path", self.file_input.text().strip())
        self.settings.setValue("paths/png_output", self.last_png_output)
        self.settings.setValue("paths/pdf_output", self.last_pdf_output)
        self.settings.setValue("paths/current_output", self.output_input.text().strip())
        self.settings.setValue("options/size_preset", self.size_preset.currentText())
        self.settings.setValue("options/width_in", self.width_input.value())
        self.settings.setValue("options/height_in", self.height_input.value())
        self.settings.setValue("options/dpmm", self.dpmm_input.value())
        self.settings.setValue("options/quality", self.quality_input.currentText())
        self.settings.setValue("options/channels", self.channels_input.value())
        self.settings.setValue("options/output_format", self.format_input.currentText())
        self.settings.setValue("options/png_prefix", self.png_prefix_input.text().strip())
        self.settings.setValue("options/open_output", self.open_output_checkbox.isChecked())
        self.settings.sync()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.save_settings()
        super().closeEvent(event)
