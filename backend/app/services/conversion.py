from __future__ import annotations

import os
import shutil
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from ..domain.models import ConversionConfig, ConversionResult
from .image_ops import apply_png_dpi_metadata, compose_labels_side_by_side, save_pdf_file
from .renderer import run_local_renderer
from .zpl_parser import analyze_zpl_text

ProgressCallback = Callable[[int, str], None] | None


def emit_progress(callback: ProgressCallback, value: int, text: str) -> None:
    if callback:
        callback(value, text)


@contextmanager
def managed_temporary_directory(prefix: str, preferred_parent: str | None = None):
    if preferred_parent:
        preferred_path = Path(preferred_parent)
        temp_root = preferred_path if preferred_path.is_dir() else preferred_path.parent
    else:
        temp_root = Path.cwd() / "build" / "tmp"

    temp_root.mkdir(parents=True, exist_ok=True)
    temp_dir = temp_root / f"{prefix}{uuid4().hex[:8]}"
    temp_dir.mkdir(parents=True, exist_ok=False)
    try:
        yield str(temp_dir)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def convert_zpl(config: ConversionConfig, progress: ProgressCallback = None) -> ConversionResult:
    emit_progress(progress, 10, "Validando archivo ZPL")
    with open(config.file_path, encoding="utf-8", errors="replace") as file_handle:
        zpl_text = file_handle.read().strip()

    if not zpl_text:
        raise ValueError("El archivo esta vacio.")

    stats = analyze_zpl_text(zpl_text)
    if stats.is_empty:
        raise ValueError("No se encontraron etiquetas ZPL validas en el archivo.")

    emit_progress(progress, 20, "Renderizando etiquetas en motor local")
    layout_columns = config.layout_columns
    label_margin_px = config.die_cut_margin_px

    if config.output_format == "png":
        output_dir = config.output_path
        os.makedirs(output_dir, exist_ok=True)
        if layout_columns <= 1 and label_margin_px <= 0:
            rendered_files = run_local_renderer(
                config.file_path,
                config.width_in,
                config.height_in,
                config.effective_dpmm,
                output_dir,
                config.png_prefix,
            )
            final_files = rendered_files
        else:
            with managed_temporary_directory("zpl_render_", output_dir) as temp_dir:
                rendered_files = run_local_renderer(
                    config.file_path,
                    config.width_in,
                    config.height_in,
                    config.effective_dpmm,
                    temp_dir,
                    "label",
                )
                emit_progress(progress, 70, "Armando etiquetas multicanal")
                final_files = compose_labels_side_by_side(
                    rendered_files,
                    output_dir,
                    config.png_prefix,
                    layout_columns,
                    label_margin_px,
                )

        emit_progress(progress, 85, "Ajustando metadatos de imagen")
        apply_png_dpi_metadata(final_files, config.effective_dpi)
        result = ConversionResult(
            message="Exportacion PNG completada.",
            output_path=output_dir,
            output_format="png",
            generated_count=len(final_files),
            source_label_count=stats.label_count,
            total_rendered_labels=len(rendered_files),
        )
    else:
        with managed_temporary_directory("zpl_render_", config.output_path) as temp_dir:
            rendered_files = run_local_renderer(
                config.file_path,
                config.width_in,
                config.height_in,
                config.effective_dpmm,
                temp_dir,
                "label",
            )
            if layout_columns > 1 or label_margin_px > 0:
                emit_progress(progress, 70, "Armando composicion final")
                pdf_source_files = compose_labels_side_by_side(
                    rendered_files,
                    temp_dir,
                    "canales",
                    layout_columns,
                    label_margin_px,
                )
            else:
                pdf_source_files = rendered_files

            emit_progress(progress, 85, "Generando PDF")
            pdf_path = save_pdf_file(pdf_source_files, config.output_path, config.effective_dpi)

        result = ConversionResult(
            message="Exportacion PDF completada.",
            output_path=pdf_path,
            output_format="pdf",
            generated_count=len(pdf_source_files),
            source_label_count=stats.label_count,
            total_rendered_labels=len(rendered_files),
        )

    emit_progress(progress, 100, "Completado")
    return result
