SELECT event_date, SUM(consumption_kwh) AS daily_consumption_kwh
FROM smart_meter_fleet_health
GROUP BY event_date
ORDER BY event_date;

SELECT year, month, SUM(consumption_kwh) AS monthly_consumption_kwh
FROM smart_meter_fleet_health
GROUP BY year, month
ORDER BY year, month;

SELECT meter_id, state, district, discom, feeder_id, total_consumption_kwh
FROM vw_top_consumers
ORDER BY total_consumption_kwh DESC
LIMIT 100;

SELECT discom, SUM(consumption_kwh) AS consumption_kwh
FROM smart_meter_fleet_health
GROUP BY discom
ORDER BY consumption_kwh DESC;
