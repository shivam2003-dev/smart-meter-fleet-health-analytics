import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "duckdb" / "smart_meter.duckdb"
SUPERSET_HOME = ROOT / "superset_home"
SUPERSET_CONFIG = ROOT / "superset" / "superset_config.py"
DATABASE_NAME = "Smart Meter DuckDB"
DASHBOARD_TITLE = "Smart Meter Fleet Health Local Dashboard"

DATASETS = [
    ("smart_meter_fleet_health", "event_date"),
    ("vw_fleet_summary", None),
    ("vw_health_by_status", None),
    ("vw_communication_health", None),
    ("vw_electrical_health", None),
    ("vw_battery_health", None),
    ("vw_daily_consumption", "event_date"),
    ("vw_monthly_consumption", None),
    ("vw_geographic_health", None),
    ("vw_firmware_distribution", None),
    ("vw_top_consumers", "last_seen_at"),
]


def chart_params(dataset_id: int, viz_type: str, extra: dict) -> str:
    base = {
        "datasource": f"{dataset_id}__table",
        "viz_type": viz_type,
        "adhoc_filters": [],
        "row_limit": 1000,
        "time_range": "No filter",
    }
    base.update(extra)
    return json.dumps(base)


def metric(label: str, aggregate: str, column_name: str | None = None) -> dict:
    result = {
        "aggregate": aggregate,
        "expressionType": "SIMPLE",
        "label": label,
    }
    if column_name:
        result["column"] = {"column_name": column_name}
    return result


def dashboard_position_json(chart_ids: list[int]) -> str:
    layout: dict[str, dict] = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {
            "type": "ROOT",
            "id": "ROOT_ID",
            "children": ["GRID_ID"],
        },
        "GRID_ID": {
            "type": "GRID",
            "id": "GRID_ID",
            "children": [],
        },
    }

    row: list[str] = []
    for index, chart_id in enumerate(chart_ids, start=1):
        chart_key = f"CHART-{chart_id}"
        layout[chart_key] = {
            "type": "CHART",
            "id": chart_key,
            "children": [],
            "meta": {
                "chartId": chart_id,
                "height": 22 if index == 1 else 36,
                "width": 4 if index == 1 else 6,
                "uuid": "",
            },
        }
        row.append(chart_key)

        if len(row) == 3 or index == len(chart_ids):
            row_key = f"ROW-{index}"
            layout[row_key] = {
                "type": "ROW",
                "id": row_key,
                "children": row,
                "meta": {"background": "BACKGROUND_TRANSPARENT"},
            }
            layout["GRID_ID"]["children"].append(row_key)
            row = []

    return json.dumps(layout)


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"{DB_PATH} does not exist. Run scripts/build_duckdb.py first."
        )

    os.environ.setdefault("SUPERSET_HOME", str(SUPERSET_HOME))
    os.environ.setdefault("SUPERSET_CONFIG_PATH", str(SUPERSET_CONFIG))
    os.environ.setdefault(
        "SUPERSET_SECRET_KEY", "local-dev-smart-meter-secret-change-me"
    )

    from superset.app import create_app
    app = create_app()
    duckdb_uri = "duckdb:///" + str(DB_PATH.resolve())

    with app.app_context():
        from superset.connectors.sqla.models import SqlaTable
        from superset.extensions import db
        from superset.models.core import Database

        database = (
            db.session.query(Database)
            .filter(Database.database_name == DATABASE_NAME)
            .one_or_none()
        )
        if database is None:
            database = Database(database_name=DATABASE_NAME)

        database.set_sqlalchemy_uri(duckdb_uri)
        database.expose_in_sqllab = True
        database.allow_ctas = False
        database.allow_cvas = False
        database.allow_dml = False
        database.allow_file_upload = False
        database.extra = json.dumps(
            {
                "metadata_params": {},
                "engine_params": {},
                "metadata_cache_timeout": {},
                "schemas_allowed_for_file_upload": [],
            }
        )
        db.session.add(database)
        db.session.commit()

        created = 0
        updated = 0
        datasets: dict[str, SqlaTable] = {}
        for table_name, main_dttm_col in DATASETS:
            dataset = (
                db.session.query(SqlaTable)
                .filter(
                    SqlaTable.database_id == database.id,
                    SqlaTable.table_name == table_name,
                    SqlaTable.schema.is_(None),
                )
                .one_or_none()
            )
            if dataset is None:
                dataset = SqlaTable(table_name=table_name, database=database)
                created += 1
            else:
                updated += 1

            dataset.database = database
            dataset.main_dttm_col = main_dttm_col
            dataset.normalize_columns = True
            dataset.is_sqllab_view = table_name.startswith("vw_")
            db.session.add(dataset)
            db.session.flush()
            dataset.fetch_metadata()
            db.session.add(dataset)
            datasets[table_name] = dataset

        db.session.commit()

        from superset.models.dashboard import Dashboard
        from superset.models.slice import Slice

        chart_specs = [
            (
                "Total Smart Meters",
                "big_number_total",
                "smart_meter_fleet_health",
                {
                    "metric": metric("Total Smart Meters", "COUNT_DISTINCT", "meter_id"),
                    "header_font_size": 0.45,
                    "subheader_font_size": 0.15,
                },
            ),
            (
                "Fleet Health Status",
                "pie",
                "vw_health_by_status",
                {
                    "groupby": ["health_status"],
                    "metric": metric("Readings", "SUM", "readings"),
                    "donut": True,
                    "show_legend": True,
                    "legendType": "scroll",
                    "label_type": "key",
                },
            ),
            (
                "Daily Consumption",
                "echarts_timeseries_line",
                "vw_daily_consumption",
                {
                    "granularity_sqla": "event_date",
                    "time_grain_sqla": "P1D",
                    "metrics": [metric("Total kWh", "SUM", "total_consumption_kwh")],
                    "groupby": ["state"],
                    "show_legend": True,
                },
            ),
            (
                "State-wise Health",
                "echarts_timeseries_bar",
                "vw_geographic_health",
                {
                    "groupby": ["state", "health_status"],
                    "metrics": [metric("Meters", "SUM", "meters")],
                    "show_legend": True,
                    "orientation": "vertical",
                },
            ),
            (
                "Communication Health",
                "table",
                "vw_communication_health",
                {
                    "query_mode": "aggregate",
                    "groupby": ["state", "district", "discom"],
                    "metrics": [
                        metric("Communication Issues", "SUM", "communication_issues"),
                        metric("Average RSSI", "AVG", "average_rssi"),
                        metric("Worst RSSI", "MIN", "worst_rssi"),
                    ],
                    "order_desc": True,
                    "page_length": 20,
                },
            ),
            (
                "Firmware Distribution",
                "echarts_timeseries_bar",
                "vw_firmware_distribution",
                {
                    "groupby": ["firmware_version", "health_status"],
                    "metrics": [metric("Meters", "SUM", "meters")],
                    "show_legend": True,
                    "orientation": "vertical",
                },
            ),
        ]

        charts: list[Slice] = []
        charts_created = 0
        charts_updated = 0
        for name, viz_type, dataset_name, params_extra in chart_specs:
            dataset = datasets[dataset_name]
            chart = (
                db.session.query(Slice).filter(Slice.slice_name == name).one_or_none()
            )
            if chart is None:
                chart = Slice(slice_name=name)
                charts_created += 1
            else:
                charts_updated += 1

            chart.viz_type = viz_type
            chart.datasource_id = dataset.id
            chart.datasource_type = "table"
            chart.datasource_name = dataset.table_name
            chart.table = dataset
            chart.params = chart_params(dataset.id, viz_type, params_extra)
            chart.query_context = None
            db.session.add(chart)
            charts.append(chart)

        db.session.commit()

        dashboard = (
            db.session.query(Dashboard)
            .filter(Dashboard.dashboard_title == DASHBOARD_TITLE)
            .one_or_none()
        )
        if dashboard is None:
            dashboard = Dashboard(dashboard_title=DASHBOARD_TITLE)

        dashboard.published = True
        dashboard.slices = charts
        dashboard.position_json = dashboard_position_json([chart.id for chart in charts])
        dashboard.json_metadata = json.dumps(
            {
                "timed_refresh_immune_slices": [],
                "expanded_slices": {},
                "color_namespace": "smart_meter_local",
                "label_colors": {
                    "Healthy": "#84d8ef",
                    "Warning": "#2f5d78",
                    "Critical": "#f2ad57",
                },
            }
        )
        db.session.add(dashboard)
        db.session.commit()

    print(f"Registered Superset database: {DATABASE_NAME}")
    print(f"DuckDB URI: {duckdb_uri}")
    print(f"Datasets created: {created}")
    print(f"Datasets updated: {updated}")
    print(f"Charts created: {charts_created}")
    print(f"Charts updated: {charts_updated}")
    print(f"Dashboard: {DASHBOARD_TITLE}")


if __name__ == "__main__":
    main()
