import io
import os
import re
import sys
from dataclasses import dataclass
from typing import List

import requests
from PIL import Image
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QComboBox,
    QProgressBar,
    QSpinBox,
    QDoubleSpinBox,
    QVBoxLayout,
    QWidget,
)


LABELARY_URL_TEMPLATE = "https://api.labelary.com/v1/printers/{dpmm}dpmm/labels/{width}x{height}/0/"


@dataclass
class ConversionConfig:
    file_path: str
    width_in: float
    height_in: float
    dpmm: int
    output_format: str
    output_path: str
    png_prefix: str


def parse_zpl_labels(zpl_text: str) -> List[str]:
    pattern = re.compile(r"\^XA.*?\^XZ", re.IGNORECASE | re.DOTALL)
    labels = [match.strip() for match in pattern.findall(zpl_text)]
    if labels:
        return labels

    text = zpl_text.strip()
    if not text:
        return []

    if "^XZ" in text.upper():
        chunks = re.split(r"(?i)\^XZ", text)
        normalized = []
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            if "^XA" not in chunk.upper():
                chunk = "^XA\n" + chunk
            normalized.append(chunk + "\n^XZ")
        return normalized

    if "^XA" not in text.upper():
        text = "^XA\n" + text
    if "^XZ" not in text.upper():
        text = text + "\n^XZ"
    return [text]


def render_label_png(zpl: str, width_in: float, height_in: float, dpmm: int) -> bytes:
    url = LABELARY_URL_TEMPLATE.format(
        dpmm=dpmm,
        width=f"{width_in:.2f}",
        height=f"{height_in:.2f}",
    )
    response = requests.post(
        url,
        data=zpl.encode("utf-8"),
        headers={"Accept": "image/png"},
        timeout=30,
    )

    if response.status_code != 200:
        details = response.text.strip().replace("\n", " ")
        if len(details) > 180:
            details = details[:180] + "..."
        raise RuntimeError(f"Labelary devolvio {response.status_code}. {details}")

    return response.content


def save_png_files(images: List[bytes], output_dir: str, prefix: str) -> List[str]:
    os.makedirs(output_dir, exist_ok=True)
    saved_paths = []
    for idx, image_bytes in enumerate(images, start=1):
        output_file = os.path.join(output_dir, f"{prefix}_{idx:03d}.png")
        with open(output_file, "wb") as f:
            f.write(image_bytes)
        saved_paths.append(output_file)
    return saved_paths


def save_pdf_file(images: List[bytes], output_file: str) -> str:
    if not output_file.lower().endswith(".pdf"):
        output_file += ".pdf"

    pil_images = []
    for image_bytes in images:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        pil_images.append(image)

    first, *rest = pil_images
    first.save(output_file, save_all=True, append_images=rest, resolution=300.0)

    for image in pil_images:
        image.close()

    return output_file


class ConversionWorker(QObject):
    progress = Signal(int, str)
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, config: ConversionConfig):
        super().__init__()
        self.config = config

    def run(self) -> None:
        try:
            with open(self.config.file_path, "r", encoding="utf-8", errors="replace") as f:
                zpl_text = f.read()

            labels = parse_zpl_labels(zpl_text)
            if not labels:
                raise ValueError("El archivo no contiene datos ZPL validos.")

            images = []
            total = len(labels)
            for idx, label in enumerate(labels, start=1):
                progress = int((idx / total) * 80)
                self.progress.emit(progress, f"Renderizando etiqueta {idx}/{total}")
                image = render_label_png(
                    zpl=label,
                    width_in=self.config.width_in,
                    height_in=self.config.height_in,
                    dpmm=self.config.dpmm,
                )
                images.append(image)

            self.progress.emit(90, "Generando salida")
            if self.config.output_format == "png":
                saved = save_png_files(images, self.config.output_path, self.config.png_prefix)
                message = f"Exportacion completada. Se generaron {len(saved)} PNG en:\n{self.config.output_path}"
            else:
                pdf_path = save_pdf_file(images, self.config.output_path)
                message = f"Exportacion completada. PDF guardado en:\n{pdf_path}"

            self.progress.emit(100, "Completado")
            self.finished.emit(message)
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
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
        self.dpmm_input.setRange(6, 24)
        self.dpmm_input.setSingleStep(1)
        self.dpmm_input.setValue(8)
        options_form.addRow("Resolucion (dpmm):", self.dpmm_input)

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
            "Nota: el renderizado usa la API de Labelary, por lo que necesitas internet para convertir."
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
