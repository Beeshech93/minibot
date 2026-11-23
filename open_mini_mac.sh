#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 Iniciando Pocket Mini Bot en modo flotante..."
if [ -d "/Applications/Google Chrome.app" ]; then
  open -na "Google Chrome" --args --app="file://$DIR/index.html" --window-size=360,670 --window-position=50,50
elif [ -d "/Applications/Brave Browser.app" ]; then
  open -na "Brave Browser" --args --app="file://$DIR/index.html" --window-size=360,670 --window-position=50,50
else
  open "file://$DIR/index.html"
fi
