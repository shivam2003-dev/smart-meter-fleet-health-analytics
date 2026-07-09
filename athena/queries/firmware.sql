SELECT firmware_version, COUNT(DISTINCT meter_id) AS meters
FROM smart_meter_fleet_health
GROUP BY firmware_version
ORDER BY meters DESC;

SELECT firmware_version, health_status, meters, communication_issues, signal_issues, voltage_issues
FROM vw_firmware_distribution
ORDER BY firmware_version, health_status;
