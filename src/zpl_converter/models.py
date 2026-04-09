from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


APP_NAME = "ZPLConverter"
APP_DISPLAY_NAME = "ZPL to PDF/PNG Converter"
APP_ORGANIZATION = "JuanM"

QUALITY_SCALES: dict[str, int] = {
    "Normal (1x)": 1,
    "Alta (2x recomendada)": 2,
    "Ultra (3x, mayor peso)": 3,
}

PRESET_SIZES: dict[str, tuple[float, float] | None] = {
    "4 x 6 in (envios)": (4.0, 6.0),
    "4 x 3 in": (4.0, 3.0),
    "2 x 1 in": (2.0, 1.0),
    "1 x 1 in": (1.0, 1.0),
    "Personalizado": None,
}


@dataclass(slots=True)
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
    open_output_on_complete: bool = False

    @property
    def width_mm(self) -> float:
        return self.width_in * 25.4

    @property
    def height_mm(self) -> float:
        return self.height_in * 25.4

    @property
    def effective_dpmm(self) -> int:
        return self.dpmm * self.quality_scale

    @property
    def effective_dpi(self) -> float:
        return self.effective_dpmm * 25.4


@dataclass(slots=True)
class ConversionResult:
    message: str
    output_path: str
    output_format: str
    generated_count: int
    source_label_count: int
    total_rendered_labels: int

    @property
    def output_path_obj(self) -> Path:
        return Path(self.output_path)


@dataclass(slots=True)
class RuntimeStatus:
    available: bool
    using_embedded_runtime: bool
    node_command: str | None
    description: str
    detail: str


@dataclass(slots=True)
class ZplDocumentStats:
    label_count: int
    total_quantity: int
    has_quantity_commands: bool

    @property
    def is_empty(self) -> bool:
        return self.label_count == 0
