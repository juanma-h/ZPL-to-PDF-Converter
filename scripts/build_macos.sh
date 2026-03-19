#!/usr/bin/env bash
set -euo pipefail

ARCH="${1:-native}"
DIST_DIR="${2:-dist/macos-${ARCH}}"
CREATE_DMG="${CREATE_DMG:-1}"
EMBED_NODE_RUNTIME="${EMBED_NODE_RUNTIME:-1}"
APP_NAME="ZPLConverter"
DMG_NAME="${APP_NAME}-${ARCH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

export PIP_CACHE_DIR="${REPO_ROOT}/build/.pip-cache"
export PYINSTALLER_CONFIG_DIR="${REPO_ROOT}/build/.pyinstaller"

RUNTIME_DIR="renderer/runtime"
RUNTIME_BIN="${RUNTIME_DIR}/node"
RUNTIME_LIB_DIR="${RUNTIME_DIR}/lib"

mkdir -p "${PIP_CACHE_DIR}" "${PYINSTALLER_CONFIG_DIR}" "${RUNTIME_LIB_DIR}"

if ! command -v node >/dev/null 2>&1; then
  echo "[ERROR] Node.js no esta instalado o no esta en PATH."
  echo "Instalalo y vuelve a intentar."
  echo "- Intel macOS (Homebrew):         brew install node@20"
  echo "- Apple Silicon macOS (Homebrew): brew install node@20"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "[ERROR] npm no esta disponible en PATH."
  echo "Reinstala Node.js 20+ o corrige tu PATH (npm viene con Node)."
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] python3 no esta disponible en PATH."
  exit 1
fi

NODE_BIN="$(command -v node)"
NODE_REALPATH="$(python3 - <<'PY' "$NODE_BIN"
import os, sys
print(os.path.realpath(sys.argv[1]))
PY
)"

collect_node_dependencies() {
  local source_bin="$1"
  local output_file="$2"

  python3 - <<'PY' "$source_bin" "$output_file"
from __future__ import annotations
import pathlib
import subprocess
import sys

source = pathlib.Path(sys.argv[1]).resolve()
output = pathlib.Path(sys.argv[2])
visited: set[pathlib.Path] = set()
results: list[pathlib.Path] = []
stack = [source]


def is_system_library(path: str) -> bool:
    return path.startswith('/usr/lib/') or path.startswith('/System/Library/')

while stack:
    current = stack.pop()
    if current in visited or not current.exists():
        continue
    visited.add(current)

    proc = subprocess.run(
        ['otool', '-L', str(current)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        continue

    for raw_line in proc.stdout.splitlines()[1:]:
        line = raw_line.strip()
        if not line:
            continue
        dep_text = line.split(' (compatibility version', 1)[0].strip()
        if not dep_text.startswith('/'):
            continue
        if is_system_library(dep_text):
            continue

        dep = pathlib.Path(dep_text)
        if not dep.exists() or dep in visited:
            continue

        results.append(dep)
        stack.append(dep)

output.write_text('\n'.join(str(path) for path in results) + ('\n' if results else ''))
PY
}

embed_node_runtime() {
  local source_bin="$1"
  local tmp_list="build/node-runtime-libs.txt"

  rm -f "${RUNTIME_BIN}"
  rm -rf "${RUNTIME_LIB_DIR}"
  mkdir -p "${RUNTIME_LIB_DIR}"

  echo "[preflight] Embedding Node runtime from ${source_bin}"
  cp "${source_bin}" "${RUNTIME_BIN}"
  chmod +x "${RUNTIME_BIN}"

  if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "[preflight] Non-macOS host detected; only the Node binary will be embedded"
    return
  fi

  if ! command -v otool >/dev/null 2>&1; then
    echo "[preflight] otool no disponible; se empaqueta solo el binario de Node"
    return
  fi

  collect_node_dependencies "${source_bin}" "${tmp_list}"
  if [[ ! -s "${tmp_list}" ]]; then
    echo "[preflight] No external dylibs were detected for Node"
    return
  fi

  while IFS= read -r dylib_path; do
    [[ -n "${dylib_path}" ]] || continue
    cp "${dylib_path}" "${RUNTIME_LIB_DIR}/$(basename "${dylib_path}")"
  done < "${tmp_list}"

  echo "[preflight] Embedded dylibs:"
  sed 's/^/  - /' "${tmp_list}"
}

create_dmg() {
  local app_bundle="${DIST_DIR}/${APP_NAME}.app"
  local dmg_dir="${DIST_DIR}/dmg"
  local dmg_path="${DIST_DIR}/${DMG_NAME}.dmg"

  if [[ "${CREATE_DMG}" != "1" ]]; then
    echo "[4/5] Skipping DMG creation (CREATE_DMG=${CREATE_DMG})"
    return
  fi

  if ! command -v hdiutil >/dev/null 2>&1; then
    echo "[4/5] hdiutil no disponible; se omite la creacion del DMG"
    return
  fi

  if [[ ! -d "${app_bundle}" ]]; then
    echo "[ERROR] No se encontro ${app_bundle} para crear el DMG"
    exit 1
  fi

  rm -rf "${dmg_dir}" "${dmg_path}"
  mkdir -p "${dmg_dir}"
  cp -R "${app_bundle}" "${dmg_dir}/"
  ln -s /Applications "${dmg_dir}/Applications"

  echo "[4/5] Creating DMG at ${dmg_path}"
  hdiutil create \
    -volname "${APP_NAME}" \
    -srcfolder "${dmg_dir}" \
    -ov \
    -format UDZO \
    "${dmg_path}"
}

echo "[preflight] node: $(node -v)"
echo "[preflight] npm:  $(npm -v)"
echo "[preflight] architecture request: ${ARCH}"
echo "[preflight] resolved node: ${NODE_REALPATH}"

if [[ "${EMBED_NODE_RUNTIME}" == "1" ]]; then
  embed_node_runtime "${NODE_REALPATH}"
else
  echo "[preflight] Skipping embedded Node runtime (EMBED_NODE_RUNTIME=${EMBED_NODE_RUNTIME})"
fi

echo "[1/5] Installing Python dependencies"
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt pyinstaller

echo "[2/5] Installing renderer dependencies"
(
  cd renderer
  npm ci
)

echo "[3/5] Building app with PyInstaller"
TARGET_ARCH_ENV=""
if [[ "${ARCH}" == "native" ]]; then
  TARGET_ARCH_ENV=""
elif [[ "${ARCH}" == "x86_64" || "${ARCH}" == "arm64" || "${ARCH}" == "universal2" ]]; then
  TARGET_ARCH_ENV="${ARCH}"
else
  echo "[ERROR] Arquitectura no soportada: ${ARCH}"
  echo "Usa una de: native, x86_64, arm64, universal2"
  exit 1
fi

if [[ -n "${TARGET_ARCH_ENV}" ]]; then
  export PYINSTALLER_TARGET_ARCH="${TARGET_ARCH_ENV}"
  echo "[preflight] PyInstaller target arch via spec: ${PYINSTALLER_TARGET_ARCH}"
else
  unset PYINSTALLER_TARGET_ARCH || true
  echo "[preflight] PyInstaller target arch: native"
fi

python3 -m PyInstaller \
  --noconfirm \
  --clean \
  --distpath "${DIST_DIR}" \
  --workpath "build/tmp/macos-${ARCH}" \
  pyinstaller/main.spec

create_dmg

echo "[5/5] Build ready at ${DIST_DIR}"
if [[ -f "${DIST_DIR}/${DMG_NAME}.dmg" ]]; then
  echo "[5/5] DMG ready at ${DIST_DIR}/${DMG_NAME}.dmg"
fi
