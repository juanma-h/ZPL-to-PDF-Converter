from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Sequence

from PIL import Image


def ensure_pdf_extension(output_file: str) -> str:
    if output_file.lower().endswith(".pdf"):
        return output_file
    return output_file + ".pdf"


def save_pdf_file(image_paths: Sequence[str], output_file: str, dpi: float) -> str:
    output_file = ensure_pdf_extension(output_file)

    pil_images = []
    for image_path in image_paths:
        with open(image_path, "rb") as file_handle:
            image_bytes = file_handle.read()
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
) -> list[str]:
    if channels_per_row <= 1:
        return [str(Path(path)) for path in image_paths]

    arranged_files: list[str] = []
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
                rgb_image = image.convert("RGB")
                row_images.append(rgb_image)
                max_width = max(max_width, rgb_image.width)
                max_height = max(max_height, rgb_image.height)

        canvas_width = max_width * channels_per_row
        canvas = Image.new("RGB", (canvas_width, max_height), "white")

        for column, image in enumerate(row_images):
            position_x = column * max_width + (max_width - image.width) // 2
            position_y = (max_height - image.height) // 2
            canvas.paste(image, (position_x, position_y))
            image.close()

        file_name = f"{output_prefix}_fila_{row_index:04d}.png"
        output_path = str(Path(output_dir) / file_name)
        canvas.save(output_path, format="PNG")
        canvas.close()
        arranged_files.append(output_path)

    return arranged_files
