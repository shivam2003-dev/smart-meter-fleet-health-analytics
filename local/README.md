# Local Smart Meter Analytics Stack

This folder runs the smart meter analytics workflow on your laptop.

It uses:

- DuckDB for local SQL over CSV/Parquet.
- Jupyter Notebook for exploration and explanation.
- Apache Superset for local BI dashboards.

No AWS resources are required for this local path. Superset and Jupyter are local web apps, so they run on your laptop ports, not in the cloud.

## Folder Layout

```text
local/
  data/
    smart_meter_fleet_health.csv
    smart_meter_fleet_health.parquet
  duckdb/
    smart_meter.duckdb
  notebooks/
    smart_meter_fleet_health_local.ipynb
  scripts/
    build_duckdb.py
    validate_local_stack.py
    register_superset_assets.py
    init_superset.sh
    run_jupyter.sh
    run_superset.sh
  sql/
    00_create_duckdb_views.sql
  superset/
    superset_config.py
  superset_home/
```

## Quick Start

From the repo root:

```bash
cd local
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -r requirements.txt

python scripts/build_duckdb.py
python scripts/validate_local_stack.py
```

## Open Jupyter

```bash
cd local
source .venv/bin/activate
./scripts/run_jupyter.sh
```

Open the notebook:

```text
notebooks/smart_meter_fleet_health_local.ipynb
```

## Open Superset

```bash
cd local
source .venv/bin/activate
./scripts/init_superset.sh
./scripts/run_superset.sh
```

Open:

```text
http://localhost:8088
```

Default local login:

```text
username: admin
password: admin
```

The init script registers:

- Superset database: `Smart Meter DuckDB`
- Datasets: base table plus all analytics views
- Dashboard: `Smart Meter Fleet Health Local Dashboard`

The dashboard is arranged as:

- Row 1: Total, Healthy, Warning, and Critical meter KPI cards.
- Row 2: Fleet health donut and daily consumption trend.
- Row 3: State health summary and communication hotspots.
- Row 4: Issue mix, battery status, and firmware health mix.
- Row 5: Electrical risk areas and top feeder risk.

DuckDB SQLAlchemy URI for manual Superset setup:

```text
duckdb:///local/duckdb/smart_meter.duckdb
```

If Superset asks for an absolute path, use:

```bash
python - <<'PY'
from pathlib import Path
print("duckdb:///" + str(Path("duckdb/smart_meter.duckdb").resolve()))
PY
```

## What DuckDB Creates

The builder creates:

- Table: `smart_meter_fleet_health`
- Views:
  - `vw_fleet_summary`
  - `vw_health_by_status`
  - `vw_communication_health`
  - `vw_electrical_health`
  - `vw_battery_health`
  - `vw_daily_consumption`
  - `vw_monthly_consumption`
  - `vw_geographic_health`
  - `vw_firmware_distribution`
  - `vw_top_consumers`
  - `vw_issue_mix`
  - `vw_state_health_summary`
  - `vw_feeder_risk`
  - `vw_battery_status_summary`

## Reset

```bash
rm -f duckdb/smart_meter.duckdb
python scripts/build_duckdb.py
```
