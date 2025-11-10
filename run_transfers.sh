#!/usr/bin/env bash
set -Eeuo pipefail

# Base paths (defaults can be overridden by env)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="${BASE_DIR:-$SCRIPT_DIR}"
ENV_FILE="${ENV_FILE:-$BASE_DIR/.env}"
PY_BIN="${PY_BIN:-python3}"
SCRIPT="${SCRIPT:-$BASE_DIR/shopify_transfers_pretty_export.py}"
LOG_DIR="${LOG_DIR:-$BASE_DIR/logs}"
LOCK_DIR="${LOCK_DIR:-$BASE_DIR/.run.lock}"

mkdir -p "$LOG_DIR"

# Prevent overlapping runs (portable lock using mkdir)
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "Another run is already in progress. Exiting."
  exit 0
fi
trap 'rmdir "$LOCK_DIR"' EXIT

# Load .env (export all keys)
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
else
  echo "WARN: .env not found at $ENV_FILE" >&2
fi

ts="$(date '+%Y-%m-%d_%H-%M-%S')"
LOG_OUT="$LOG_DIR/run_$ts.out.log"
LOG_ERR="$LOG_DIR/run_$ts.err.log"

{
  echo "[$(date)] Starting Shopify transfers export…"
  "$PY_BIN" "$SCRIPT"
  rc=$?
  echo "[$(date)] Finished with exit code $rc"
  exit $rc
} >>"$LOG_OUT" 2>>"$LOG_ERR"
