SELECT battery_status, COUNT(DISTINCT meter_id) AS meters, ROUND(AVG(battery_pct), 2) AS average_battery_pct
FROM smart_meter_fleet_health
GROUP BY battery_status
ORDER BY meters DESC;

SELECT meter_id, state, district, discom, battery_pct, battery_status, timestamp
FROM smart_meter_fleet_health
WHERE battery_issue = true
ORDER BY battery_pct ASC, timestamp DESC;
