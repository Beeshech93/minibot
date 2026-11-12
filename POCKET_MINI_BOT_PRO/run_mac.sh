#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Prioritize local venv if exists, otherwise parent venv
if [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    PY_EXEC="$SCRIPT_DIR/.venv/bin/python"
elif [ -f "$SCRIPT_DIR/../.venv/bin/python" ]; then
    PY_EXEC="$SCRIPT_DIR/../.venv/bin/python"
else
    PY_EXEC="python3"
fi

export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
exec "$PY_EXEC" "$SCRIPT_DIR/main.py" "$@"
