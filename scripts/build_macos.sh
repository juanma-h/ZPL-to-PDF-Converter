#!/usr/bin/env bash
set -euo pipefail

ARCH="${1:-native}"
DIST_DIR="${2:-dist/macos-${ARCH}}"
CREATE_DMG="${CREATE_DMG:-1}"
EMBED_NODE_RUNTIME="${EMBED_NODE_RUNTIME:-1}"
STRICT_EMBED_NODE_RUNTIME="${STRICT_EMBED_NODE_RUNTIME:-0}"
SKIP_PYTHON_DEPS_INSTALL="${SKIP_PYTHON_DEPS_INSTALL:-0}"
SKIP_NPM_INSTALL="${SKIP_NPM_INSTALL:-0}"
APP_NAME="ZPLConverter"
SCRIPT_REVISION="2026-03-19-runtime-fallback"
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
NODE_REALPATH="$(python3 -c "import os,sys; print(os.path.realpath(sys.argv[1]))" "$NODE_BIN")"

collect_node_dependencies() {
  local source_bin="$1"
  local output_file="$2"
  local helper_script="scripts/collect_macos_node_deps.py"

  if [[ ! -f "${helper_script}" ]]; then
    echo "[ERROR] No se encontro ${helper_script}"
    return 1
  fi

  python3 "${helper_script}" "$source_bin" "$output_file"
}

embed_node_runtime() {
  local source_bin="$1"
  local tmp_list="build/node-runtime-libs.txt"

  mkdir -p "${RUNTIME_DIR}"
  chmod -R u+w "${RUNTIME_DIR}" 2>/dev/null || true
  rm -f "${RUNTIME_BIN}"
  rm -rf "${RUNTIME_LIB_DIR}"
  mkdir -p "${RUNTIME_LIB_DIR}"

  echo "[preflight] Embedding Node runtime from ${source_bin}"
  install -m 0755 "${source_bin}" "${RUNTIME_BIN}"

  if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "[preflight] Non-macOS host detected; only the Node binary will be embedded"
    return
  fi

  if ! command -v otool >/dev/null 2>&1; then
    echo "[preflight] otool no disponible; se empaqueta solo el binario de Node"
    return
  fi

  if ! collect_node_dependencies "${source_bin}" "${tmp_list}"; then
    echo "[WARN] No se pudieron recolectar las dependencias dylib de Node"
    return 1
  fi

  if [[ ! -s "${tmp_list}" ]]; then
    echo "[preflight] No external dylibs were detected for Node"
    return
  fi

  while IFS= read -r dylib_path; do
    [[ -n "${dylib_path}" ]] || continue
    target_path="${RUNTIME_LIB_DIR}/$(basename "${dylib_path}")"
    rm -f "${target_path}"
    install -m 0644 "${dylib_path}" "${target_path}"
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
    echo "[ERROR] El build de PyInstaller no produjo un bundle .app. Revisa pyinstaller/main.spec."
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

echo "[preflight] script revision: ${SCRIPT_REVISION}"
echo "[preflight] node: $(node -v)"
echo "[preflight] npm:  $(npm -v)"
echo "[preflight] architecture request: ${ARCH}"
echo "[preflight] resolved node: ${NODE_REALPATH}"

if [[ "${EMBED_NODE_RUNTIME}" == "1" ]]; then
  if ! embed_node_runtime "${NODE_REALPATH}"; then
    if [[ "${STRICT_EMBED_NODE_RUNTIME}" == "1" ]]; then
      echo "[ERROR] Fallo el embedding del runtime de Node y STRICT_EMBED_NODE_RUNTIME=1"
      exit 1
    fi

    echo "[WARN] Fallo el embedding del runtime de Node; se continuara usando Node externo desde PATH"
    rm -rf "${RUNTIME_DIR}"
  fi
else
  echo "[preflight] Skipping embedded Node runtime (EMBED_NODE_RUNTIME=${EMBED_NODE_RUNTIME})"
fi

if [[ "${SKIP_PYTHON_DEPS_INSTALL}" == "1" ]]; then
  echo "[1/5] Skipping Python dependency installation"
else
  echo "[1/5] Installing Python dependencies"
  python3 -m pip install --upgrade pip
  python3 -m pip install -r requirements.txt pyinstaller
fi

if [[ "${SKIP_NPM_INSTALL}" == "1" ]]; then
  echo "[2/5] Skipping renderer dependency installation"
else
  echo "[2/5] Installing renderer dependencies"
  (
    cd renderer
    npm ci
  )
fi

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
