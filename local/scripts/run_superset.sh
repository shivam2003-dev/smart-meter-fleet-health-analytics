#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
export SUPERSET_HOME="$PWD/superset_home"
export SUPERSET_CONFIG_PATH="$PWD/superset/superset_config.py"
export FLASK_APP=superset
export SUPERSET_SECRET_KEY="${SUPERSET_SECRET_KEY:-local-dev-smart-meter-secret-change-me}"

superset run -h 127.0.0.1 -p 8088 --with-threads
