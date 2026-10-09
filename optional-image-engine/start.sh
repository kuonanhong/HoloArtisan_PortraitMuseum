#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ -x .venv/bin/python ]; then
  exec .venv/bin/python server.py --preload "$@"
fi
exec python3 server.py --preload "$@"
