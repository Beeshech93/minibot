#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "  POCKET MINI BOT PRO — Compilador de macOS .app"
echo "=================================================="

# Select Python
if [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    PY_EXEC="$SCRIPT_DIR/.venv/bin/python"
elif [ -f "$SCRIPT_DIR/../.venv/bin/python" ]; then
    PY_EXEC="$SCRIPT_DIR/../.venv/bin/python"
else
    PY_EXEC="python3"
fi

echo "📦 Verificando PyInstaller..."
"$PY_EXEC" -m pip install pyinstaller

echo "🔨 Compilando aplicación nativa de macOS (dist/PocketMiniBotPro.app)..."
"$PY_EXEC" -m PyInstaller \
    --name="PocketMiniBotPro" \
    --windowed \
    --noconfirm \
    --clean \
    --add-data="app:app" \
    --add-data="ui:ui" \
    --add-data="assets:assets" \
    --osx-bundle-identifier="com.pocketminibot.pro" \
    main.py

echo ""
echo "🎉 Compilación completada con éxito."
echo "La aplicación se encuentra en: $SCRIPT_DIR/dist/PocketMiniBotPro.app"
echo "Puedes moverla a tu carpeta /Applications para abrirla desde Spotlight o Finder."
echo "=================================================="
