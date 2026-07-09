from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "duckdb" / "smart_meter.duckdb"


REQUIRED_VIEWS = [
    "vw_fleet_summary",
    "vw_health_by_status",
    "vw_communication_health",
    "vw_electrical_health",
    "vw_battery_health",
    "vw_daily_consumption",
    "vw_monthly_consumption",
    "vw_geographic_health",
    "vw_firmware_distribution",
    "vw_top_consumers",
    "vw_issue_mix",
    "vw_state_health_summary",
    "vw_feeder_risk",
    "vw_battery_status_summary",
]


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError("Run scripts/build_duckdb.py first.")

    con = duckdb.connect(str(DB_PATH), read_only=True)
    rows, meters = con.execute(
        "SELECT COUNT(*), COUNT(DISTINCT meter_id) FROM smart_meter_fleet_health"
    ).fetchone()
    if rows != 50_000:
        raise AssertionError(f"Expected 50,000 rows, got {rows}")
    if meters != 50_000:
        raise AssertionError(f"Expected 50,000 meters, got {meters}")

    existing = {
        row[0]
        for row in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
    }
    missing = [view for view in REQUIRED_VIEWS if view not in existing]
    if missing:
        raise AssertionError(f"Missing views: {missing}")

    print("Local DuckDB validation passed.")
    print(f"Rows: {rows:,}")
    print(f"Meters: {meters:,}")
    print(f"Views: {len(REQUIRED_VIEWS)}")
    print("Fleet summary:")
    print(con.execute("SELECT * FROM vw_fleet_summary").fetchdf().to_string(index=False))
    con.close()


if __name__ == "__main__":
    main()
