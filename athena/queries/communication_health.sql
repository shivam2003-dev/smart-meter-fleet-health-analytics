SELECT
  COUNT_IF(communication_lag_minutes > 180) AS offline_meters,
  COUNT_IF(comm_issue) AS communication_issues,
  ROUND(AVG(rssi), 2) AS average_rssi
FROM smart_meter_fleet_health;

SELECT state, MIN(rssi) AS worst_rssi, ROUND(AVG(rssi), 2) AS average_rssi
FROM smart_meter_fleet_health
GROUP BY state
ORDER BY worst_rssi ASC;
