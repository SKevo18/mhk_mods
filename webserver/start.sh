#!/usr/bin/bash
cd "$(dirname "$0")"

set -a; source .envrc; set +a


handle_sigint() {
  echo "Killing both processes"
  kill $pid1 $pid2
}

trap handle_sigint SIGINT

# So cli.py can be imported:
export PYTHONPATH=../

../.venv/bin/gunicorn flask_app:MHKM_FLASK_APP --bind=unix:./mhk_mods_flask.sock -k sync -m 007 -w 4 --timeout=300 &
pid1=$!

../.venv/bin/gunicorn fastapi_app:MHKM_FASTAPI_APP --bind=unix:./mhk_mods_fastapi.sock -k uvicorn.workers.UvicornWorker -m 007 -w 4 --timeout=300 &
pid2=$!


wait $pid1 $pid2
