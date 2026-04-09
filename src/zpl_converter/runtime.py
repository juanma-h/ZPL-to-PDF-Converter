from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from .models import RuntimeStatus


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def runtime_base_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return PROJECT_ROOT


def local_renderer_script_path() -> Path:
    return runtime_base_path() / "renderer" / "render_zpl_local.mjs"


def bundled_node_runtime_dir() -> Path:
    return runtime_base_path() / "renderer" / "runtime"


def bundled_node_binary_path() -> Path:
    suffix = ".exe" if os.name == "nt" else ""
    return bundled_node_runtime_dir() / f"node{suffix}"


def bundled_node_lib_dir() -> Path:
    return bundled_node_runtime_dir() / "lib"


def runtime_working_directory() -> Path:
    return runtime_base_path()


def runtime_library_env_var() -> str | None:
    if sys.platform == "darwin":
        return "DYLD_LIBRARY_PATH"
    if sys.platform.startswith("linux"):
        return "LD_LIBRARY_PATH"
    return None


def resolve_node_command() -> str:
    bundled_node = bundled_node_binary_path()
    if bundled_node.is_file():
        return str(bundled_node)

    system_node = shutil.which("node")
    if system_node:
        return system_node

    raise RuntimeError(
        "No se encontro Node.js. La app requiere un runtime de Node embebido "
        "o una instalacion de Node.js 20+ disponible en PATH."
    )


def build_renderer_environment() -> dict[str, str]:
    env = os.environ.copy()
    bundled_node = bundled_node_binary_path()
    bundled_lib_dir = bundled_node_lib_dir()
    library_env_var = runtime_library_env_var()

    if bundled_node.is_file() and bundled_lib_dir.is_dir() and library_env_var:
        current_value = env.get(library_env_var, "")
        lib_entries = [str(bundled_lib_dir)]
        if current_value:
            lib_entries.append(current_value)
        env[library_env_var] = os.pathsep.join(lib_entries)

    return env


def get_runtime_status() -> RuntimeStatus:
    renderer_script = local_renderer_script_path()
    if not renderer_script.is_file():
        return RuntimeStatus(
            available=False,
            using_embedded_runtime=False,
            node_command=None,
            description="Renderer local no disponible",
            detail="Falta renderer/render_zpl_local.mjs en el proyecto o bundle.",
        )

    bundled_node = bundled_node_binary_path()
    if bundled_node.is_file():
        return RuntimeStatus(
            available=True,
            using_embedded_runtime=True,
            node_command=str(bundled_node),
            description="Node embebido listo",
            detail=f"Runtime incluido en {bundled_node.parent}",
        )

    system_node = shutil.which("node")
    if system_node:
        return RuntimeStatus(
            available=True,
            using_embedded_runtime=False,
            node_command=system_node,
            description="Node externo detectado",
            detail=f"Usando Node desde PATH: {system_node}",
        )

    return RuntimeStatus(
        available=False,
        using_embedded_runtime=False,
        node_command=None,
        description="Node no disponible",
        detail="Instala Node.js 20+ o genera un build con runtime embebido.",
    )
