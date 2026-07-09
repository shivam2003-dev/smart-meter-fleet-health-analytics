#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
export SUPERSET_HOME="$PWD/superset_home"
export SUPERSET_CONFIG_PATH="$PWD/superset/superset_config.py"
export FLASK_APP=superset
export SUPERSET_SECRET_KEY="${SUPERSET_SECRET_KEY:-local-dev-smart-meter-secret-change-me}"

superset db upgrade

superset fab create-admin \
  --username admin \
  --firstname Smart \
  --lastname Meter \
  --email admin@example.com \
  --password admin || true

superset init
python scripts/register_superset_assets.py

echo "Superset initialized."
echo "Login: admin / admin"
echo "DuckDB URI:"
python - <<'PY'
from pathlib import Path
print("duckdb:///" + str(Path("duckdb/smart_meter.duckdb").resolve()))
PY
