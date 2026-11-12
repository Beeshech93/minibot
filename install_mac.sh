#!/bin/bash
set -e
cd "$(dirname "$0")"
echo "POCKET MINI BOT - instalación"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 no está instalado. Instálalo desde https://www.python.org/downloads/macos/"
  exit 1
fi
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt
pip cache purge >/dev/null 2>&1 || true
echo ""
echo "Instalación completada."
echo "Ejecuta: ./run_mac.sh"
