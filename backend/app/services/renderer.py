from __future__ import annotations

import json
import subprocess

from ..core.config import get_settings
from ..core.errors import RenderError
from .runtime import local_renderer_script_path, resolve_node_command, runtime_working_directory


def parse_renderer_output(stdout_text: str) -> list[str]:
    if not stdout_text.strip():
        raise RenderError("El renderer local no devolvio salida.")

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
        raise RenderError("No se pudo interpretar la salida del renderer local.")

    files = payload.get("files")
    if not isinstance(files, list) or not files:
        raise RenderError("El renderer local no genero imagenes.")

    return [str(file_path) for file_path in files]


def run_local_renderer(
    input_file: str,
    width_in: float,
    height_in: float,
    dpmm: int,
    output_dir: str,
    prefix: str,
) -> list[str]:
    renderer_script = local_renderer_script_path()
    if not renderer_script.is_file():
        raise RenderError("No se encontro renderer/render_zpl_local.mjs.")

    command = [
        resolve_node_command(),
        str(renderer_script),
        "--input",
        input_file,
        "--output-dir",
        output_dir,
        "--prefix",
        prefix,
        "--width-mm",
        f"{width_in * 25.4:.2f}",
        "--height-mm",
        f"{height_in * 25.4:.2f}",
        "--dpmm",
        str(dpmm),
    ]

    try:
        completed = subprocess.run(
            command,
            cwd=str(runtime_working_directory()),
            capture_output=True,
            text=True,
            check=False,
            timeout=get_settings().renderer_timeout_seconds,
        )
    except FileNotFoundError as exc:
        raise RenderError("No se pudo ejecutar Node.js en el servidor.") from exc
    except subprocess.TimeoutExpired as exc:
        raise RenderError("El renderer excedio el tiempo maximo permitido.") from exc

    if completed.returncode != 0:
        details = (completed.stderr or completed.stdout or "").strip()
        if len(details) > 500:
            details = details[:500] + "..."
        raise RenderError(f"Fallo el renderer local. Detalle: {details or 'sin detalle'}")

    return parse_renderer_output(completed.stdout)
