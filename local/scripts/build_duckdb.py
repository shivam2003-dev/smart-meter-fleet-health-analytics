from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_PATH = ROOT / "duckdb" / "smart_meter.duckdb"
PARQUET_PATH = DATA_DIR / "smart_meter_fleet_health.parquet"
CSV_PATH = DATA_DIR / "smart_meter_fleet_health.csv"
VIEWS_SQL = ROOT / "sql" / "00_create_duckdb_views.sql"


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not PARQUET_PATH.exists() and not CSV_PATH.exists():
        raise FileNotFoundError("Expected local data file under local/data/")

    con = duckdb.connect(str(DB_PATH))
    con.execute("INSTALL parquet")
    con.execute("LOAD parquet")

    if PARQUET_PATH.exists():
        source_sql = f"read_parquet('{PARQUET_PATH.as_posix()}')"
    else:
        source_sql = f"read_csv_auto('{CSV_PATH.as_posix()}', header = true)"

    con.execute(
        f"""
        CREATE OR REPLACE TABLE smart_meter_fleet_health AS
        SELECT
          meter_id::VARCHAR AS meter_id,
          CAST(timestamp AS TIMESTAMP) AS timestamp,
          CAST(timestamp AS DATE) AS event_date,
          voltage::DOUBLE AS voltage,
          current::DOUBLE AS current,
          power_factor::DOUBLE AS power_factor,
          CAST(last_communication_time AS TIMESTAMP) AS last_communication_time,
          date_diff('minute', CAST(last_communication_time AS TIMESTAMP), CAST(timestamp AS TIMESTAMP))::DOUBLE AS communication_lag_minutes,
          battery_status::VARCHAR AS battery_status,
          battery_pct::INTEGER AS battery_pct,
          rssi::DOUBLE AS rssi,
          firmware_version::VARCHAR AS firmware_version,
          state::VARCHAR AS state,
          district::VARCHAR AS district,
          discom::VARCHAR AS discom,
          feeder_id::VARCHAR AS feeder_id,
          consumption_kwh::DOUBLE AS consumption_kwh,
          voltage_issue::BOOLEAN AS voltage_issue,
          power_factor_issue::BOOLEAN AS power_factor_issue,
          comm_issue::BOOLEAN AS comm_issue,
          signal_issue::BOOLEAN AS signal_issue,
          battery_issue::BOOLEAN AS battery_issue,
          (
            CAST(voltage_issue AS INTEGER)
            + CAST(power_factor_issue AS INTEGER)
            + CAST(comm_issue AS INTEGER)
            + CAST(signal_issue AS INTEGER)
            + CAST(battery_issue AS INTEGER)
          ) AS issue_count,
          CASE
            WHEN (
              CAST(voltage_issue AS INTEGER)
              + CAST(power_factor_issue AS INTEGER)
              + CAST(comm_issue AS INTEGER)
              + CAST(signal_issue AS INTEGER)
              + CAST(battery_issue AS INTEGER)
            ) >= 3 THEN 'Critical'
            WHEN (
              CAST(voltage_issue AS INTEGER)
              + CAST(power_factor_issue AS INTEGER)
              + CAST(comm_issue AS INTEGER)
              + CAST(signal_issue AS INTEGER)
              + CAST(battery_issue AS INTEGER)
            ) >= 1 THEN 'Warning'
            ELSE 'Healthy'
          END AS health_status,
          strftime(CAST(timestamp AS TIMESTAMP), '%Y') AS year,
          strftime(CAST(timestamp AS TIMESTAMP), '%m') AS month,
          strftime(CAST(timestamp AS TIMESTAMP), '%d') AS day
        FROM {source_sql}
        QUALIFY row_number() OVER (
          PARTITION BY meter_id, CAST(timestamp AS TIMESTAMP)
          ORDER BY CAST(timestamp AS TIMESTAMP)
        ) = 1
        """
    )

    for statement in VIEWS_SQL.read_text().split(";"):
        statement = statement.strip()
        if statement:
            con.execute(statement)

    summary = con.execute(
        """
        SELECT
          COUNT(*) AS rows,
          COUNT(DISTINCT meter_id) AS meters,
          MIN(event_date) AS min_date,
          MAX(event_date) AS max_date
        FROM smart_meter_fleet_health
        """
    ).fetchdf()

    print(f"Created DuckDB database: {DB_PATH}")
    print(summary.to_string(index=False))
    con.close()


if __name__ == "__main__":
    main()
