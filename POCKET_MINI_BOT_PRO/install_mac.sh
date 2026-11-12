#!/usr/bin/env bash
set -e

echo "=================================================="
echo "  POCKET MINI BOT PRO — Instalador para macOS"
echo "  Compatible con Apple Silicon (M1/M2/M3) e Intel"
echo "=================================================="

# 1. Detect Python
PYTHON_BIN=""
for cmd in python3 python3.12 python3.11 python; do
    if command -v $cmd >/dev/null 2>&1; then
        PY_VER=$($cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        MAJOR=$(echo $PY_VER | cut -d. -f1)
        MINOR=$(echo $PY_VER | cut -d. -f2)
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 10 ]; then
            PYTHON_BIN=$cmd
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "❌ Error: Se requiere Python 3.10 o superior."
    echo "Instálalo vía Homebrew: brew install python"
    exit 1
fi

echo "✅ Python detectado: $($PYTHON_BIN --version) ($PYTHON_BIN)"

# 2. Virtual Environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creando entorno virtual en $VENV_DIR..."
    $PYTHON_BIN -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# 3. Upgrade pip and install requirements
echo "⬇️ Instalando dependencias necesarias (PySide6, OpenCV, MSS, NumPy)..."
pip install --upgrade pip
pip install -r "$SCRIPT_DIR/requirements.txt"

# 4. Permissions notice
echo ""
echo "🔐 Permisos de Grabación de Pantalla en macOS:"
echo "Para que el bot pueda capturar la ventana de Pocket Option, debes otorgar permiso:"
echo "  Ajustes del Sistema -> Privacidad y Seguridad -> Grabación de Pantalla"
echo "  Asegúrate de permitir Terminal / iTerm / Python."

chmod +x "$SCRIPT_DIR/run_mac.sh" 2>/dev/null || true
chmod +x "$SCRIPT_DIR/build_mac.sh" 2>/dev/null || true

echo ""
echo "🎉 ¡Instalación completada con éxito!"
echo "Para iniciar el bot ejecuta: ./run_mac.sh"
echo "=================================================="

