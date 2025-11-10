#!/usr/bin/env bash
set -Eeuo pipefail

# repo root (directory of this script)
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$BASE_DIR/.." && pwd)"

ENV_FILE="$REPO_ROOT/.env"
SCRIPT="$REPO_ROOT/shopify_transfers_pretty_export.py"
PY_BIN="$REPO_ROOT/.venv/bin/python3"
LOG_DIR="$REPO_ROOT/logs"
mkdir -p "$LOG_DIR"

# bootstrap venv if missing
if [[ ! -x "$PY_BIN" ]]; then
  python3 -m venv "$REPO_ROOT/.venv"
  "$REPO_ROOT/.venv/bin/pip" install -U pip
  "$REPO_ROOT/.venv/bin/pip" install -r "$REPO_ROOT/requirements.txt"
fi

# Load .env safely
if [[ -f "$ENV_FILE" ]]; then
  while IFS= read -r line; do
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    if [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]]; then
      export "$line"
    fi
  done < "$ENV_FILE"
fi

ts="$(date '+%Y-%m-%d_%H-%M-%S')"
LOG_OUT="$LOG_DIR/run_$ts.out.log"
LOG_ERR="$LOG_DIR/run_$ts.err.log"

echo "[$(date)] Starting Shopify transfers export..." | tee -a "$LOG_OUT"
"$PY_BIN" "$SCRIPT" >>"$LOG_OUT" 2>>"$LOG_ERR"
echo "[$(date)] Done." | tee -a "$LOG_OUT"
