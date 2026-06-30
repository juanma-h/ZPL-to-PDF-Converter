from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse

from ...core.config import get_settings
from ...core.errors import ApplicationError, ConversionLimitError
from ...domain.models import ConversionConfig
from ...services.conversion import convert_zpl
from ...services.zpl_parser import analyze_zpl_text
from ..schemas import AnalyzeResponse

router = APIRouter(prefix="/zpl", tags=["zpl"])


def safe_stem(filename: str | None) -> str:
    stem = Path(filename or "etiquetas").stem
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", stem).strip("_")
    return cleaned[:80] or "etiquetas"


async def read_upload(upload: UploadFile) -> bytes:
    settings = get_settings()
    chunks: list[bytes] = []
    total = 0
    while chunk := await upload.read(1024 * 1024):
        total += len(chunk)
        if total > settings.max_upload_bytes:
            raise ConversionLimitError(
                f"El archivo supera el limite de {settings.max_upload_bytes // (1024 * 1024)} MB."
            )
        chunks.append(chunk)
    return b"".join(chunks)


def validate_quantity(total_quantity: int) -> None:
    limit = get_settings().max_rendered_labels
    if total_quantity > limit:
        raise ConversionLimitError(
            f"El archivo solicita {total_quantity} etiquetas; el limite del servidor es {limit}."
        )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(file: Annotated[UploadFile, File(...)]) -> AnalyzeResponse:
    try:
        content = (await read_upload(file)).decode("utf-8", errors="replace")
        stats = analyze_zpl_text(content)
        validate_quantity(stats.total_quantity)
    except ApplicationError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc

    return AnalyzeResponse(
        filename=file.filename or "etiquetas.txt",
        label_count=stats.label_count,
        total_quantity=stats.total_quantity,
        has_quantity_commands=stats.has_quantity_commands,
    )


@router.post("/convert", response_class=FileResponse)
async def convert(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(...)],
    output_format: Annotated[Literal["pdf", "png"], Form()] = "pdf",
    width_in: Annotated[float, Form(ge=0.5, le=20)] = 4.0,
    height_in: Annotated[float, Form(ge=0.5, le=20)] = 6.0,
    dpmm: Annotated[int, Form(ge=6, le=48)] = 12,
    quality_scale: Annotated[Literal[1, 2, 3], Form()] = 2,
    channels_per_row: Annotated[int, Form(ge=1, le=6)] = 1,
    die_cut_enabled: Annotated[bool, Form()] = False,
    die_cut_margin_mm: Annotated[float, Form(ge=0, le=25)] = 0,
    die_cut_columns: Annotated[int, Form(ge=1, le=6)] = 2,
    png_prefix: Annotated[str, Form(max_length=80)] = "etiqueta",
) -> FileResponse:
    workspace = Path(tempfile.mkdtemp(prefix="zpl-conversion-"))
    try:
        content = await read_upload(file)
        text = content.decode("utf-8", errors="replace")
        stats = analyze_zpl_text(text)
        validate_quantity(stats.total_quantity)

        stem = safe_stem(file.filename)
        input_path = workspace / f"{stem}.txt"
        input_path.write_bytes(content)
        output_path = workspace / ("png" if output_format == "png" else f"{stem}.pdf")
        prefix = safe_stem(png_prefix)

        config = ConversionConfig(
            file_path=str(input_path),
            width_in=width_in,
            height_in=height_in,
            dpmm=dpmm,
            quality_scale=quality_scale,
            channels_per_row=channels_per_row,
            output_format=output_format,
            output_path=str(output_path),
            png_prefix=prefix,
            die_cut_enabled=die_cut_enabled,
            die_cut_margin_mm=die_cut_margin_mm,
            die_cut_columns=die_cut_columns,
        )
        result = await run_in_threadpool(convert_zpl, config)

        if output_format == "png":
            archive_base = workspace / f"{stem}_png"
            archive_path = Path(shutil.make_archive(str(archive_base), "zip", result.output_path))
            download_name = f"{stem}_png.zip"
            media_type = "application/zip"
            response_path = archive_path
        else:
            download_name = f"{stem}.pdf"
            media_type = "application/pdf"
            response_path = Path(result.output_path)

        background_tasks.add_task(shutil.rmtree, workspace, ignore_errors=True)
        return FileResponse(
            response_path,
            filename=download_name,
            media_type=media_type,
            background=background_tasks,
            headers={
                "X-Generated-Files": str(result.generated_count),
                "X-Rendered-Labels": str(result.total_rendered_labels),
            },
        )
    except ConversionLimitError as exc:
        shutil.rmtree(workspace, ignore_errors=True)
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except (ApplicationError, OSError, ValueError) as exc:
        shutil.rmtree(workspace, ignore_errors=True)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception:
        shutil.rmtree(workspace, ignore_errors=True)
        raise
