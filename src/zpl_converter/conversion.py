from __future__ import annotations

import os
import shutil
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from .image_ops import apply_png_dpi_metadata, compose_labels_side_by_side, save_pdf_file
from .models import ConversionConfig, ConversionResult
from .renderer import run_local_renderer
from .zpl_parser import analyze_zpl_text


ProgressCallback = Callable[[int, str], None] | None


def emit_progress(callback: ProgressCallback, value: int, text: str) -> None:
    if callback:
        callback(value, text)


@contextmanager
def managed_temporary_directory(
    prefix: str,
    preferred_parent: str | None = None,
):
    if preferred_parent:
        preferred_path = Path(preferred_parent)
        temp_root = preferred_path if preferred_path.is_dir() else preferred_path.parent
    else:
        temp_root_env = os.environ.get("ZPL_CONVERTER_TEMP_DIR", "").strip()
        temp_root = Path(temp_root_env) if temp_root_env else Path.cwd() / "build" / "tmp"

    temp_root.mkdir(parents=True, exist_ok=True)
    temp_dir = temp_root / f"{prefix}{uuid4().hex[:8]}"
    temp_dir.mkdir(parents=True, exist_ok=False)
    try:
        yield str(temp_dir)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def convert_zpl(config: ConversionConfig, progress: ProgressCallback = None) -> ConversionResult:
    emit_progress(progress, 10, "Validando archivo ZPL")
    with open(config.file_path, "r", encoding="utf-8", errors="replace") as file_handle:
        zpl_text = file_handle.read().strip()

    if not zpl_text:
        raise ValueError("El archivo esta vacio.")

    stats = analyze_zpl_text(zpl_text)
    if stats.is_empty:
        raise ValueError("No se encontraron etiquetas ZPL validas en el archivo.")

    emit_progress(progress, 20, "Renderizando etiquetas en motor local")

    if config.output_format == "png":
        output_dir = config.output_path
        os.makedirs(output_dir, exist_ok=True)

        if config.channels_per_row <= 1:
            rendered_files = run_local_renderer(
                input_file=config.file_path,
                width_in=config.width_in,
                height_in=config.height_in,
                dpmm=config.effective_dpmm,
                output_dir=output_dir,
                prefix=config.png_prefix,
            )
            final_files = rendered_files
        else:
            with managed_temporary_directory(
                prefix="zpl_local_render_channels_",
                preferred_parent=output_dir,
            ) as temp_dir:
                rendered_files = run_local_renderer(
                    input_file=config.file_path,
                    width_in=config.width_in,
                    height_in=config.height_in,
                    dpmm=config.effective_dpmm,
                    output_dir=temp_dir,
                    prefix="label",
                )
                emit_progress(progress, 70, "Armando etiquetas multicanal")
                final_files = compose_labels_side_by_side(
                    image_paths=rendered_files,
                    output_dir=output_dir,
                    output_prefix=config.png_prefix,
                    channels_per_row=config.channels_per_row,
                )

        emit_progress(progress, 85, "Ajustando metadatos de imagen")
        apply_png_dpi_metadata(final_files, dpi=config.effective_dpi)

        if config.channels_per_row <= 1:
            message = (
                f"Exportacion completada. Se generaron {len(final_files)} PNG en:\n"
                f"{output_dir}"
            )
        else:
            message = (
                "Exportacion multicanal completada. "
                f"Se distribuyeron {len(rendered_files)} etiquetas en {len(final_files)} PNG "
                f"({config.channels_per_row} canales por fila) en:\n{output_dir}"
            )

        result = ConversionResult(
            message=message,
            output_path=output_dir,
            output_format="png",
            generated_count=len(final_files),
            source_label_count=stats.label_count,
            total_rendered_labels=len(rendered_files),
        )
    else:
        with managed_temporary_directory(
            prefix="zpl_local_render_",
            preferred_parent=config.output_path,
        ) as temp_dir:
            rendered_files = run_local_renderer(
                input_file=config.file_path,
                width_in=config.width_in,
                height_in=config.height_in,
                dpmm=config.effective_dpmm,
                output_dir=temp_dir,
                prefix="label",
            )
            if config.channels_per_row > 1:
                emit_progress(progress, 70, "Armando etiquetas multicanal")
                pdf_source_files = compose_labels_side_by_side(
                    image_paths=rendered_files,
                    output_dir=temp_dir,
                    output_prefix="canales",
                    channels_per_row=config.channels_per_row,
                )
            else:
                pdf_source_files = rendered_files

            emit_progress(progress, 85, "Generando PDF")
            pdf_path = save_pdf_file(
                pdf_source_files,
                config.output_path,
                dpi=config.effective_dpi,
            )

        if config.channels_per_row <= 1:
            message = f"Exportacion completada. PDF guardado en:\n{pdf_path}"
        else:
            message = (
                "Exportacion multicanal completada. "
                f"Se distribuyeron {len(rendered_files)} etiquetas en "
                f"{len(pdf_source_files)} paginas ({config.channels_per_row} canales por fila).\n"
                f"PDF guardado en:\n{pdf_path}"
            )

        result = ConversionResult(
            message=message,
            output_path=pdf_path,
            output_format="pdf",
            generated_count=len(pdf_source_files),
            source_label_count=stats.label_count,
            total_rendered_labels=len(rendered_files),
        )

    emit_progress(progress, 100, "Completado")
    return result
