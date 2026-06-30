from __future__ import annotations

import os
import shutil
from pathlib import Path

from ..core.config import get_settings
from ..domain.models import RuntimeStatus


def local_renderer_script_path() -> Path:
    return get_settings().renderer_dir / "render_zpl_local.mjs"


def runtime_working_directory() -> Path:
    return get_settings().project_root


def resolve_node_command() -> str:
    configured_node = os.getenv("NODE_BINARY", "").strip()
    if configured_node and Path(configured_node).is_file():
        return configured_node

    system_node = shutil.which("node")
    if system_node:
        return system_node

    raise RuntimeError("No se encontro Node.js 20+ en el servidor.")


def get_runtime_status() -> RuntimeStatus:
    renderer_script = local_renderer_script_path()
    if not renderer_script.is_file():
        return RuntimeStatus(
            available=False,
            node_command=None,
            description="Renderer no disponible",
            detail="Falta renderer/render_zpl_local.mjs.",
        )

    try:
        node_command = resolve_node_command()
    except RuntimeError as exc:
        return RuntimeStatus(
            available=False,
            node_command=None,
            description="Node.js no disponible",
            detail=str(exc),
        )

    return RuntimeStatus(
        available=True,
        node_command=node_command,
        description="Renderer local listo",
        detail=f"Node.js: {node_command}",
    )
