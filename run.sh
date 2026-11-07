#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo 'Missing virtual environment: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt' >&2
  exit 1
fi
exec .venv/bin/python main.py
