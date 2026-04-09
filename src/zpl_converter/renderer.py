from __future__ import annotations

import json
import subprocess

from .runtime import (
    build_renderer_environment,
    local_renderer_script_path,
    resolve_node_command,
    runtime_working_directory,
)


def parse_renderer_output(stdout_text: str) -> list[str]:
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
        raise RuntimeError(
            "No se encontro el renderer local. Falta el archivo renderer/render_zpl_local.mjs "
            "en la distribucion o en el proyecto."
        )

    width_mm = width_in * 25.4
    height_mm = height_in * 25.4
    node_command = resolve_node_command()

    command = [
        node_command,
        str(renderer_script),
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
            cwd=str(runtime_working_directory()),
            capture_output=True,
            text=True,
            check=False,
            env=build_renderer_environment(),
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "No se pudo ejecutar el runtime de Node. Verifica que el build incluya "
            "renderer/runtime/node y sus librerias o instala Node.js 20+."
        ) from exc

    if completed.returncode != 0:
        details = (completed.stderr or completed.stdout or "").strip()
        if len(details) > 500:
            details = details[:500] + "..."
        raise RuntimeError(
            "Fallo el renderer local.\n"
            "Asegurate de ejecutar 'npm ci' dentro de la carpeta 'renderer'.\n"
            f"Detalle: {details or 'sin detalle'}"
        )

    return parse_renderer_output(completed.stdout)
