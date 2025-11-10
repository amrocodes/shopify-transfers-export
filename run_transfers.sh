#!/usr/bin/env bash
set -Eeuo pipefail

BASE_DIR="//Users/amro/Library/Application Support/shopify-transfers"
ENV_FILE="$BASE_DIR/.env"
PY_BIN="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"
SCRIPT="$BASE_DIR/shopify_transfers_pretty_export.py"
LOG_DIR="$BASE_DIR/logs"
mkdir -p "$LOG_DIR"

# Load .env safely: only KEY=VALUE lines; ignore comments/blank/bad lines
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
