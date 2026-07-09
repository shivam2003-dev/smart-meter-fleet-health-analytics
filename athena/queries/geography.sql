SELECT state, health_status, COUNT(DISTINCT meter_id) AS meters
FROM smart_meter_fleet_health
GROUP BY state, health_status
ORDER BY state, health_status;

SELECT district, health_status, COUNT(DISTINCT meter_id) AS meters
FROM smart_meter_fleet_health
GROUP BY district, health_status
ORDER BY district, meters DESC;

SELECT discom, health_status, COUNT(DISTINCT meter_id) AS meters
FROM smart_meter_fleet_health
GROUP BY discom, health_status
ORDER BY discom, meters DESC;
