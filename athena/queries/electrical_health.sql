SELECT
  COUNT_IF(voltage_issue) AS voltage_violations,
  COUNT_IF(power_factor_issue) AS low_power_factor,
  ROUND(AVG(voltage), 2) AS average_voltage,
  ROUND(AVG(current), 2) AS average_current
FROM smart_meter_fleet_health;

SELECT state, district, discom, voltage_violations, low_power_factor, average_voltage, average_current
FROM vw_electrical_health
ORDER BY voltage_violations DESC;
