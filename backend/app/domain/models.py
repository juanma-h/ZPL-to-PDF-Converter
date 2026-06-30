from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


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
    die_cut_enabled: bool = False
    die_cut_margin_mm: float = 0.0
    die_cut_columns: int = 1

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

    @property
    def layout_columns(self) -> int:
        if self.die_cut_enabled:
            return max(1, self.die_cut_columns)
        return max(1, self.channels_per_row)

    @property
    def die_cut_margin_px(self) -> int:
        if not self.die_cut_enabled:
            return 0
        return max(0, round(self.die_cut_margin_mm * self.effective_dpmm))


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
