import io
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

from PIL import Image
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_RENDERER_SCRIPT = PROJECT_ROOT / "renderer" / "render_zpl_local.mjs"


@dataclass
class ConversionConfig:
    file_path: str
    width_in: float
    height_in: float
    dpmm: int
    quality_scale: int
    channels_per_row: int
    output_format: str
    output_path: str
    png_prefix: str


def ensure_pdf_extension(output_file: str) -> str:
    if output_file.lower().endswith(".pdf"):
        return output_file
    return output_file + ".pdf"


def save_pdf_file(image_paths: Sequence[str], output_file: str, dpi: float) -> str:
    output_file = ensure_pdf_extension(output_file)

    pil_images = []
    for image_path in image_paths:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        pil_images.append(image)

    if not pil_images:
        raise ValueError("No se encontraron imagenes para crear el PDF.")

    first, *rest = pil_images
    first.save(output_file, save_all=True, append_images=rest, resolution=dpi)

    for image in pil_images:
        image.close()

    return output_file


def apply_png_dpi_metadata(image_paths: Sequence[str], dpi: float) -> None:
    dpi_pair = (dpi, dpi)
    for image_path in image_paths:
        with Image.open(image_path) as image:
            image.save(image_path, dpi=dpi_pair)


def compose_labels_side_by_side(
    image_paths: Sequence[str],
    output_dir: str,
    output_prefix: str,
    channels_per_row: int,
) -> List[str]:
    if channels_per_row <= 1:
        return [str(Path(p)) for p in image_paths]

    arranged_files: List[str] = []
    os.makedirs(output_dir, exist_ok=True)

    total_labels = len(image_paths)
    row_index = 0
    for start in range(0, total_labels, channels_per_row):
        row_index += 1
        row_paths = image_paths[start : start + channels_per_row]

        row_images = []
        max_width = 0
        max_height = 0
        for row_path in row_paths:
            with Image.open(row_path) as image:
                rgb = image.convert("RGB")
                row_images.append(rgb)
                max_width = max(max_width, rgb.width)
                max_height = max(max_height, rgb.height)

        canvas_width = max_width * channels_per_row
        canvas = Image.new("RGB", (canvas_width, max_height), "white")

        for col, image in enumerate(row_images):
            x = col * max_width + (max_width - image.width) // 2
            y = (max_height - image.height) // 2
            canvas.paste(image, (x, y))
            image.close()

        file_name = f"{output_prefix}_fila_{row_index:04d}.png"
        output_path = str(Path(output_dir) / file_name)
        canvas.save(output_path, format="PNG")
        canvas.close()
        arranged_files.append(output_path)

    return arranged_files


def parse_renderer_output(stdout_text: str) -> List[str]:
    if not stdout_text.strip():
        raise RuntimeError("El renderer local no devolvio salida.")

    payload = None
    for raw_line in reversed(stdout_text.splitlines()):
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
            break
        except json.JSONDecodeError:
            continue

    if not isinstance(payload, dict):
        raise RuntimeError("No se pudo interpretar la salida del renderer local.")

    files = payload.get("files")
    if not isinstance(files, list) or not files:
        raise RuntimeError("El renderer local no genero imagenes.")

    normalized = [str(Path(file_path)) for file_path in files]
    return normalized


def run_local_renderer(
    input_file: str,
    width_in: float,
    height_in: float,
    dpmm: int,
    output_dir: str,
    prefix: str,
) -> List[str]:
    if not LOCAL_RENDERER_SCRIPT.is_file():
        raise RuntimeError(
            "No se encontro el renderer local. Falta el archivo renderer/render_zpl_local.mjs."
        )

    width_mm = width_in * 25.4
    height_mm = height_in * 25.4

    command = [
        "node",
        str(LOCAL_RENDERER_SCRIPT),
        "--input",
        input_file,
        "--output-dir",
        output_dir,
        "--prefix",
        prefix,
        "--width-mm",
        f"{width_mm:.2f}",
        "--height-mm",
        f"{height_mm:.2f}",
        "--dpmm",
        str(dpmm),
    ]

    try:
        completed = subprocess.run(
            command,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "Node.js no esta instalado o no esta en PATH. Instala Node.js 20+."
        ) from exc

    if completed.returncode != 0:
        details = (completed.stderr or completed.stdout or "").strip()
        if len(details) > 500:
            details = details[:500] + "..."
        raise RuntimeError(
            "Fallo el renderer local.\n"
            "Asegurate de ejecutar 'npm install' dentro de la carpeta 'renderer'.\n"
            f"Detalle: {details or 'sin detalle'}"
        )

    files = parse_renderer_output(completed.stdout)
    return files


class ConversionWorker(QObject):
    progress = Signal(int, str)
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, config: ConversionConfig):
        super().__init__()
        self.config = config

    def run(self) -> None:
        try:
            self.progress.emit(10, "Validando archivo ZPL")
            with open(self.config.file_path, "r", encoding="utf-8", errors="replace") as f:
                zpl_text = f.read().strip()

            if not zpl_text:
                raise ValueError("El archivo esta vacio.")

            self.progress.emit(20, "Renderizando etiquetas en motor local")
            effective_dpmm = self.config.dpmm * self.config.quality_scale
            effective_dpi = effective_dpmm * 25.4

            if self.config.output_format == "png":
                output_dir = self.config.output_path
                os.makedirs(output_dir, exist_ok=True)
                if self.config.channels_per_row <= 1:
                    rendered_files = run_local_renderer(
                        input_file=self.config.file_path,
                        width_in=self.config.width_in,
                        height_in=self.config.height_in,
                        dpmm=effective_dpmm,
                        output_dir=output_dir,
                        prefix=self.config.png_prefix,
                    )
                    final_files = rendered_files
                else:
                    with tempfile.TemporaryDirectory(prefix="zpl_local_render_channels_") as temp_dir:
                        rendered_files = run_local_renderer(
                            input_file=self.config.file_path,
                            width_in=self.config.width_in,
                            height_in=self.config.height_in,
                            dpmm=effective_dpmm,
                            output_dir=temp_dir,
                            prefix="label",
                        )
                        self.progress.emit(70, "Armando etiquetas multicanal")
                        final_files = compose_labels_side_by_side(
                            image_paths=rendered_files,
                            output_dir=output_dir,
                            output_prefix=self.config.png_prefix,
                            channels_per_row=self.config.channels_per_row,
                        )
                self.progress.emit(85, "Ajustando metadatos de imagen")
                apply_png_dpi_metadata(final_files, dpi=effective_dpi)
                if self.config.channels_per_row <= 1:
                    message = (
                        f"Exportacion completada. Se generaron {len(final_files)} PNG en:\n"
                        f"{output_dir}"
                    )
                else:
                    message = (
                        "Exportacion multicanal completada. "
                        f"Se distribuyeron {len(rendered_files)} etiquetas en {len(final_files)} PNG "
                        f"({self.config.channels_per_row} canales por fila) en:\n{output_dir}"
                    )
            else:
                with tempfile.TemporaryDirectory(prefix="zpl_local_render_") as temp_dir:
                    rendered_files = run_local_renderer(
                        input_file=self.config.file_path,
                        width_in=self.config.width_in,
                        height_in=self.config.height_in,
                        dpmm=effective_dpmm,
                        output_dir=temp_dir,
                        prefix="label",
                    )
                    if self.config.channels_per_row > 1:
                        self.progress.emit(70, "Armando etiquetas multicanal")
                        pdf_source_files = compose_labels_side_by_side(
                            image_paths=rendered_files,
                            output_dir=temp_dir,
                            output_prefix="canales",
                            channels_per_row=self.config.channels_per_row,
                        )
                    else:
                        pdf_source_files = rendered_files
                    self.progress.emit(85, "Generando PDF")
                    pdf_path = save_pdf_file(
                        pdf_source_files,
                        self.config.output_path,
                        dpi=effective_dpi,
                    )
                if self.config.channels_per_row <= 1:
                    message = f"Exportacion completada. PDF guardado en:\n{pdf_path}"
                else:
                    message = (
                        "Exportacion multicanal completada. "
                        f"Se distribuyeron {len(rendered_files)} etiquetas en "
                        f"{len(pdf_source_files)} paginas ({self.config.channels_per_row} canales por fila).\n"
                        f"PDF guardado en:\n{pdf_path}"
                    )

            self.progress.emit(100, "Completado")
            self.finished.emit(message)
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    QUALITY_SCALES = {
        "Normal (1x)": 1,
        "Alta (2x recomendada)": 2,
        "Ultra (3x, mayor peso)": 3,
    }

    PRESET_SIZES = {
        "4 x 6 in (envios)": (4.0, 6.0),
        "4 x 3 in": (4.0, 3.0),
        "2 x 1 in": (2.0, 1.0),
        "1 x 1 in": (1.0, 1.0),
        "Personalizado": None,
    }

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ZPL to PDF/PNG Converter")
        self.setMinimumWidth(760)

        self.worker_thread = None
        self.worker = None

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setSpacing(14)

        file_group = QGroupBox("Archivo ZPL")
        file_form = QFormLayout(file_group)
        self.file_input = QLineEdit()
        browse_file_btn = QPushButton("Seleccionar .txt")
        browse_file_btn.clicked.connect(self.select_file)
        file_row = QHBoxLayout()
        file_row.addWidget(self.file_input)
        file_row.addWidget(browse_file_btn)
        file_form.addRow("Origen:", file_row)
        root_layout.addWidget(file_group)

        options_group = QGroupBox("Opciones")
        options_form = QFormLayout(options_group)

        self.size_preset = QComboBox()
        self.size_preset.addItems(self.PRESET_SIZES.keys())
        self.size_preset.currentTextChanged.connect(self.on_size_preset_changed)

        self.width_input = QDoubleSpinBox()
        self.width_input.setRange(0.5, 20.0)
        self.width_input.setDecimals(2)
        self.width_input.setSingleStep(0.1)
        self.width_input.setValue(4.0)

        self.height_input = QDoubleSpinBox()
        self.height_input.setRange(0.5, 20.0)
        self.height_input.setDecimals(2)
        self.height_input.setSingleStep(0.1)
        self.height_input.setValue(6.0)

        size_row = QHBoxLayout()
        size_row.addWidget(self.size_preset)
        size_row.addWidget(QLabel("Ancho (in):"))
        size_row.addWidget(self.width_input)
        size_row.addWidget(QLabel("Alto (in):"))
        size_row.addWidget(self.height_input)
        options_form.addRow("Etiqueta:", size_row)

        self.dpmm_input = QSpinBox()
        self.dpmm_input.setRange(6, 48)
        self.dpmm_input.setSingleStep(1)
        self.dpmm_input.setValue(12)
        options_form.addRow("Resolucion (dpmm):", self.dpmm_input)

        self.quality_input = QComboBox()
        self.quality_input.addItems(self.QUALITY_SCALES.keys())
        self.quality_input.setCurrentText("Alta (2x recomendada)")
        options_form.addRow("Calidad de render:", self.quality_input)

        self.channels_input = QSpinBox()
        self.channels_input.setRange(1, 6)
        self.channels_input.setSingleStep(1)
        self.channels_input.setValue(1)
        options_form.addRow("Canales por fila:", self.channels_input)

        self.format_input = QComboBox()
        self.format_input.addItems(["pdf", "png"])
        self.format_input.currentTextChanged.connect(self.on_format_changed)
        options_form.addRow("Formato de salida:", self.format_input)

        self.output_input = QLineEdit()
        browse_output_btn = QPushButton("Elegir destino")
        browse_output_btn.clicked.connect(self.select_output)
        output_row = QHBoxLayout()
        output_row.addWidget(self.output_input)
        output_row.addWidget(browse_output_btn)
        options_form.addRow("Destino:", output_row)

        self.png_prefix_input = QLineEdit("etiqueta")
        options_form.addRow("Prefijo PNG:", self.png_prefix_input)
        root_layout.addWidget(options_group)

        self.status_label = QLabel(
            "Motor local activado (sin API). Usa Canales por fila > 1 para etiquetas lado a lado."
        )
        root_layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        root_layout.addWidget(self.progress)

        self.convert_btn = QPushButton("Convertir")
        self.convert_btn.clicked.connect(self.start_conversion)
        root_layout.addWidget(self.convert_btn)

        self.setCentralWidget(root)
        self.on_size_preset_changed(self.size_preset.currentText())
        self.on_format_changed(self.format_input.currentText())

    def select_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo ZPL",
            "",
            "Text files (*.txt);;All files (*.*)",
        )
        if file_path:
            self.file_input.setText(file_path)

    def select_output(self) -> None:
        if self.format_input.currentText() == "png":
            output_dir = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta destino")
            if output_dir:
                self.output_input.setText(output_dir)
        else:
            output_file, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar PDF",
                "etiquetas.pdf",
                "PDF files (*.pdf)",
            )
            if output_file:
                self.output_input.setText(output_file)

    def on_size_preset_changed(self, selected: str) -> None:
        size = self.PRESET_SIZES[selected]
        is_custom = size is None
        self.width_input.setEnabled(is_custom)
        self.height_input.setEnabled(is_custom)
        if size is not None:
            width, height = size
            self.width_input.setValue(width)
            self.height_input.setValue(height)

    def on_format_changed(self, output_format: str) -> None:
        is_png = output_format == "png"
        self.png_prefix_input.setEnabled(is_png)
        self.png_prefix_input.setVisible(is_png)
        self.output_input.clear()

    def start_conversion(self) -> None:
        file_path = self.file_input.text().strip()
        output_path = self.output_input.text().strip()
        output_format = self.format_input.currentText()
        png_prefix = self.png_prefix_input.text().strip() or "etiqueta"
        quality_scale = self.QUALITY_SCALES[self.quality_input.currentText()]
        channels_per_row = self.channels_input.value()

        if not file_path or not os.path.isfile(file_path):
            QMessageBox.warning(self, "Falta archivo", "Selecciona un archivo .txt valido.")
            return

        if not output_path:
            if output_format == "png":
                QMessageBox.warning(self, "Falta destino", "Selecciona una carpeta destino para PNG.")
            else:
                QMessageBox.warning(self, "Falta destino", "Selecciona la ruta de salida del PDF.")
            return

        width_in = self.width_input.value()
        height_in = self.height_input.value()
        if width_in <= 0 or height_in <= 0:
            QMessageBox.warning(self, "Tamano invalido", "El ancho y el alto deben ser mayores a 0.")
            return

        config = ConversionConfig(
            file_path=file_path,
            width_in=width_in,
            height_in=height_in,
            dpmm=self.dpmm_input.value(),
            quality_scale=quality_scale,
            channels_per_row=channels_per_row,
            output_format=output_format,
            output_path=output_path,
            png_prefix=png_prefix,
        )
        self.run_worker(config)

    def run_worker(self, config: ConversionConfig) -> None:
        self.convert_btn.setEnabled(False)
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

    def on_finished(self, message: str) -> None:
        self.status_label.setText("Conversion finalizada.")
        QMessageBox.information(self, "Listo", message)

    def on_failed(self, error_message: str) -> None:
        self.status_label.setText("Error durante la conversion.")
        QMessageBox.critical(self, "Error", error_message)


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
