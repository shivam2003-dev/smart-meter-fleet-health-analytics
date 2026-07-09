#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
export JUPYTER_PLATFORM_DIRS=1
jupyter lab --no-browser --notebook-dir notebooks --port 8888
