#!/bin/bash
set -e

mkdir -p /data

# Seed a fresh SQLite DB with the Prisma schema already applied, if this
# container's /data is empty (e.g. first boot, or ephemeral storage on a
# free HF Spaces tier that doesn't persist a volume across restarts).
if [ ! -f /data/app.db ]; then
  cp /app/frontend/prisma/seed.db /data/app.db
fi

export DATABASE_URL="file:/data/app.db"
export CHECKPOINT_DB_PATH="/data/checkpoints.db"

cd /app/backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

cd /app/frontend
PORT="${PORT:-7860}" HOSTNAME="0.0.0.0" node server.js &
FRONTEND_PID=$!

trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null' TERM INT

wait -n "$BACKEND_PID" "$FRONTEND_PID"
kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
wait
