#!/usr/bin/env bash
set -euo pipefail

ARCH="${1:-native}"
DIST_DIR="${2:-dist/macos-${ARCH}}"
CREATE_DMG="${CREATE_DMG:-1}"
APP_NAME="ZPLConverter"
DMG_NAME="${APP_NAME}-${ARCH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

export PIP_CACHE_DIR="${REPO_ROOT}/build/.pip-cache"
export PYINSTALLER_CONFIG_DIR="${REPO_ROOT}/build/.pyinstaller"

mkdir -p "${PIP_CACHE_DIR}" "${PYINSTALLER_CONFIG_DIR}" "renderer/bin"

if ! command -v node >/dev/null 2>&1; then
  echo "[ERROR] Node.js no esta instalado o no esta en PATH."
  echo "Instalalo y vuelve a intentar."
  echo "- Intel macOS (Homebrew):        brew install node@20"
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

copy_node_runtime() {
  local source_bin="$1"
  local target_bin="renderer/bin/node"

  echo "[preflight] Embedding Node runtime from ${source_bin}"
  cp "${source_bin}" "${target_bin}"
  chmod +x "${target_bin}"
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

copy_node_runtime "${NODE_REALPATH}"

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
