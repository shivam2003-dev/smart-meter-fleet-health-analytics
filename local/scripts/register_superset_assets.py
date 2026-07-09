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
    ("vw_issue_mix", None),
    ("vw_state_health_summary", None),
    ("vw_feeder_risk", None),
    ("vw_battery_status_summary", None),
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


def dashboard_position_json(chart_ids_by_name: dict[str, int]) -> str:
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

    rows = [
        [
            ("Total Smart Meters", 3, 12),
            ("Healthy Meters", 3, 12),
            ("Warning Meters", 3, 12),
            ("Critical Meters", 3, 12),
        ],
        [
            ("Fleet Health Status", 4, 34),
            ("Daily Consumption Trend", 8, 34),
        ],
        [
            ("State Health Summary", 6, 34),
            ("Communication Hotspots", 6, 34),
        ],
        [
            ("Issue Mix", 4, 32),
            ("Battery Status", 4, 32),
            ("Firmware Health Mix", 4, 32),
        ],
        [
            ("Electrical Risk Areas", 6, 34),
            ("Top Feeder Risk", 6, 34),
        ],
    ]

    for row_index, row_specs in enumerate(rows, start=1):
        row_children = []
        for chart_name, width, height in row_specs:
            chart_id = chart_ids_by_name[chart_name]
            chart_key = f"CHART-{chart_id}"
            layout[chart_key] = {
                "type": "CHART",
                "id": chart_key,
                "children": [],
                "meta": {
                    "chartId": chart_id,
                    "height": height,
                    "width": width,
                    "uuid": "",
                },
            }
            row_children.append(chart_key)

        row_key = f"ROW-{row_index}"
        layout[row_key] = {
            "type": "ROW",
            "id": row_key,
            "children": row_children,
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
        }
        layout["GRID_ID"]["children"].append(row_key)

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
                "vw_fleet_summary",
                {
                    "metric": metric("Total", "SUM", "total_meters"),
                    "header_font_size": 0.38,
                    "subheader_font_size": 0.12,
                },
            ),
            (
                "Healthy Meters",
                "big_number_total",
                "vw_fleet_summary",
                {
                    "metric": metric("Healthy", "SUM", "healthy"),
                    "header_font_size": 0.38,
                    "subheader_font_size": 0.12,
                },
            ),
            (
                "Warning Meters",
                "big_number_total",
                "vw_fleet_summary",
                {
                    "metric": metric("Warning", "SUM", "warning"),
                    "header_font_size": 0.38,
                    "subheader_font_size": 0.12,
                },
            ),
            (
                "Critical Meters",
                "big_number_total",
                "vw_fleet_summary",
                {
                    "metric": metric("Critical", "SUM", "critical"),
                    "header_font_size": 0.45,
                    "subheader_font_size": 0.12,
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
                "Daily Consumption Trend",
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
                "State Health Summary",
                "table",
                "vw_state_health_summary",
                {
                    "query_mode": "aggregate",
                    "groupby": ["state"],
                    "metrics": [
                        metric("Total Meters", "SUM", "total_meters"),
                        metric("Healthy", "SUM", "healthy"),
                        metric("Warning", "SUM", "warning"),
                        metric("Critical", "SUM", "critical"),
                        metric("Warning %", "AVG", "warning_pct"),
                        metric("Critical %", "AVG", "critical_pct"),
                        metric("Avg RSSI", "AVG", "average_rssi"),
                    ],
                    "order_desc": True,
                    "page_length": 10,
                },
            ),
            (
                "Communication Hotspots",
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
                "Issue Mix",
                "pie",
                "vw_issue_mix",
                {
                    "groupby": ["issue_type"],
                    "metric": metric("Issues", "SUM", "issue_count"),
                    "donut": True,
                    "show_legend": True,
                    "legendType": "scroll",
                    "label_type": "key",
                },
            ),
            (
                "Battery Status",
                "pie",
                "vw_battery_status_summary",
                {
                    "groupby": ["battery_status"],
                    "metric": metric("Meters", "SUM", "meters"),
                    "donut": True,
                    "show_legend": True,
                    "legendType": "scroll",
                    "label_type": "key",
                },
            ),
            (
                "Firmware Health Mix",
                "pie",
                "vw_firmware_distribution",
                {
                    "groupby": ["firmware_version"],
                    "metric": metric("Meters", "SUM", "meters"),
                    "donut": True,
                    "show_legend": True,
                    "legendType": "scroll",
                    "label_type": "key",
                },
            ),
            (
                "Electrical Risk Areas",
                "table",
                "vw_electrical_health",
                {
                    "query_mode": "aggregate",
                    "groupby": ["state", "district", "discom"],
                    "metrics": [
                        metric("Voltage Violations", "SUM", "voltage_violations"),
                        metric("Low PF", "SUM", "low_power_factor"),
                        metric("Avg Voltage", "AVG", "average_voltage"),
                        metric("Avg Current", "AVG", "average_current"),
                        metric("Avg PF", "AVG", "average_power_factor"),
                    ],
                    "order_desc": True,
                    "page_length": 15,
                },
            ),
            (
                "Top Feeder Risk",
                "table",
                "vw_feeder_risk",
                {
                    "query_mode": "aggregate",
                    "groupby": ["feeder_id", "state", "district", "discom"],
                    "metrics": [
                        metric("Critical", "SUM", "critical_meters"),
                        metric("Warning", "SUM", "warning_meters"),
                        metric("Total Issues", "SUM", "total_issues"),
                        metric("Avg RSSI", "AVG", "average_rssi"),
                        metric("Total kWh", "SUM", "total_consumption_kwh"),
                    ],
                    "order_desc": True,
                    "page_length": 15,
                },
            ),
        ]

        charts: list[Slice] = []
        chart_ids_by_name: dict[str, int] = {}
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
            db.session.flush()
            chart_ids_by_name[name] = chart.id

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
        dashboard.position_json = dashboard_position_json(chart_ids_by_name)
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
