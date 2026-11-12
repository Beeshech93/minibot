#!/bin/bash
set -e
cd "$(dirname "$0")"
source .venv/bin/activate
python pocket_mini_bot/main.py
