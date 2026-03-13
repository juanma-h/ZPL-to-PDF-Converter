#!/usr/bin/env bash
set -euo pipefail

ARCH="${1:-native}"
DIST_DIR="${2:-dist/macos-${ARCH}}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

export PIP_CACHE_DIR="${REPO_ROOT}/build/.pip-cache"
export PYINSTALLER_CONFIG_DIR="${REPO_ROOT}/build/.pyinstaller"

mkdir -p "${PIP_CACHE_DIR}" "${PYINSTALLER_CONFIG_DIR}"

if ! command -v node >/dev/null 2>&1; then
  echo "[ERROR] Node.js no esta instalado o no esta en PATH."
  echo "Instalalo y vuelve a intentar. Ejemplo en macOS con Homebrew:"
  echo "  brew install node@20"
  echo "  echo 'export PATH=\"/opt/homebrew/opt/node@20/bin:$PATH\"' >> ~/.zshrc"
  echo "  source ~/.zshrc"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "[ERROR] npm no esta disponible en PATH."
  echo "Reinstala Node.js 20+ o corrige tu PATH (npm viene con Node)."
  exit 1
fi

echo "[preflight] node: $(node -v)"
echo "[preflight] npm:  $(npm -v)"

echo "[1/4] Installing Python dependencies"
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt pyinstaller

echo "[2/4] Installing renderer dependencies"
(
  cd renderer
  npm ci
)

echo "[3/4] Building app with PyInstaller"
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

echo "[4/4] Build ready at ${DIST_DIR}"
