#!/bin/bash
set -e
cd "$(dirname "$0")"
source .venv/bin/activate
export PYTHONPATH="POCKET_MINI_BOT_PRO:$PYTHONPATH"
exec python POCKET_MINI_BOT_PRO/main.py "$@"
