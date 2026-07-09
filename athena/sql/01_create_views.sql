USE smart_meter_analytics;

CREATE OR REPLACE VIEW vw_fleet_summary AS
SELECT
  COUNT(DISTINCT meter_id) AS total_meters,
  COUNT_IF(health_status = 'Healthy') AS healthy,
  COUNT_IF(health_status = 'Warning') AS warning,
  COUNT_IF(health_status = 'Critical') AS critical,
  ROUND(AVG(voltage), 2) AS average_voltage,
  ROUND(AVG(rssi), 2) AS average_rssi,
  ROUND(AVG(battery_pct), 2) AS average_battery_pct,
  ROUND(AVG(consumption_kwh), 3) AS average_consumption_kwh
FROM smart_meter_fleet_health;

CREATE OR REPLACE VIEW vw_communication_health AS
SELECT
  state,
  district,
  discom,
  COUNT(*) AS readings,
  COUNT_IF(comm_issue) AS communication_issues,
  COUNT_IF(communication_lag_minutes > 180) AS offline_meters,
  ROUND(AVG(rssi), 2) AS average_rssi,
  MIN(rssi) AS worst_rssi
FROM smart_meter_fleet_health
GROUP BY state, district, discom;

CREATE OR REPLACE VIEW vw_electrical_health AS
SELECT
  state,
  district,
  discom,
  COUNT(*) AS readings,
  COUNT_IF(voltage_issue) AS voltage_violations,
  COUNT_IF(power_factor_issue) AS low_power_factor,
  ROUND(AVG(voltage), 2) AS average_voltage,
  ROUND(AVG(current), 2) AS average_current,
  ROUND(AVG(power_factor), 3) AS average_power_factor
FROM smart_meter_fleet_health
GROUP BY state, district, discom;

CREATE OR REPLACE VIEW vw_battery_health AS
SELECT
  state,
  district,
  discom,
  battery_status,
  COUNT(*) AS devices,
  ROUND(AVG(battery_pct), 2) AS average_battery_pct,
  COUNT_IF(battery_issue) AS low_battery_devices
FROM smart_meter_fleet_health
GROUP BY state, district, discom, battery_status;

CREATE OR REPLACE VIEW vw_daily_consumption AS
SELECT
  event_date,
  state,
  district,
  discom,
  SUM(consumption_kwh) AS total_consumption_kwh,
  AVG(consumption_kwh) AS average_consumption_kwh,
  COUNT(DISTINCT meter_id) AS meters
FROM smart_meter_fleet_health
GROUP BY event_date, state, district, discom;

CREATE OR REPLACE VIEW vw_monthly_consumption AS
SELECT
  year,
  month,
  state,
  discom,
  SUM(consumption_kwh) AS total_consumption_kwh,
  AVG(consumption_kwh) AS average_consumption_kwh,
  COUNT(DISTINCT meter_id) AS meters
FROM smart_meter_fleet_health
GROUP BY year, month, state, discom;

CREATE OR REPLACE VIEW vw_geographic_health AS
SELECT
  state,
  district,
  discom,
  health_status,
  COUNT(*) AS meter_readings,
  COUNT(DISTINCT meter_id) AS meters,
  ROUND(AVG(voltage), 2) AS average_voltage,
  ROUND(AVG(rssi), 2) AS average_rssi,
  ROUND(AVG(battery_pct), 2) AS average_battery_pct
FROM smart_meter_fleet_health
GROUP BY state, district, discom, health_status;

CREATE OR REPLACE VIEW vw_firmware_distribution AS
SELECT
  firmware_version,
  health_status,
  COUNT(DISTINCT meter_id) AS meters,
  COUNT_IF(comm_issue) AS communication_issues,
  COUNT_IF(signal_issue) AS signal_issues,
  COUNT_IF(voltage_issue) AS voltage_issues
FROM smart_meter_fleet_health
GROUP BY firmware_version, health_status;

CREATE OR REPLACE VIEW vw_top_consumers AS
SELECT
  meter_id,
  state,
  district,
  discom,
  feeder_id,
  SUM(consumption_kwh) AS total_consumption_kwh,
  AVG(voltage) AS average_voltage,
  AVG(current) AS average_current,
  MAX(timestamp) AS last_seen_at
FROM smart_meter_fleet_health
GROUP BY meter_id, state, district, discom, feeder_id;
