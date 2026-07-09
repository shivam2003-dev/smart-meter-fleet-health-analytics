SELECT * FROM vw_fleet_summary;

SELECT health_status, COUNT(DISTINCT meter_id) AS meters
FROM smart_meter_fleet_health
GROUP BY health_status
ORDER BY meters DESC;
