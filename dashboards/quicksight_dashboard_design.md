# QuickSight Dashboard Design

Dashboard name: `Smart Meter Fleet Health Executive Dashboard`

Primary dataset: Athena table `smart_meter_analytics.smart_meter_fleet_health`

Recommended import mode: SPICE for dashboard performance. Use direct query only while testing schema changes.

## Filters

- Date range: `event_date`
- State: `state`
- District: `district`
- DISCOM: `discom`
- Firmware version: `firmware_version`
- Health status: `health_status`

## Calculated Fields

Create these calculated fields in QuickSight if they are not imported from Athena views:

- `Unhealthy Flag`: `ifelse({health_status} = 'Healthy', 0, 1)`
- `Offline Flag`: `ifelse({communication_lag_minutes} > 180, 1, 0)`
- `Low Battery Flag`: `ifelse({battery_status} = 'Low', 1, 0)`
- `Signal Quality`: `ifelse({rssi} < -90, 'Poor', {rssi} < -80, 'Weak', 'Good')`

## Sheet 1: Executive Overview

KPI cards:

- Total Smart Meters: distinct count of `meter_id`
- Healthy: distinct count where `health_status = Healthy`
- Warning: distinct count where `health_status = Warning`
- Critical: distinct count where `health_status = Critical`
- Average Voltage: average `voltage`
- Average RSSI: average `rssi`
- Average Battery %: average `battery_pct`
- Average Consumption: average `consumption_kwh`

Visuals:

- Health Status Donut: `health_status` by distinct count `meter_id`
- Meter Health Trend: `event_date` by distinct count `meter_id`, grouped by `health_status`
- Fleet Summary Table: `state`, `district`, `discom`, distinct meters, average voltage, average RSSI, average battery, warning count, critical count

## Sheet 2: Geography

Visuals:

- State-wise Health: stacked bar, `state` by distinct meters grouped by `health_status`
- District-wise Heatmap: `district` by `health_status`, color by distinct meters
- DISCOM Comparison: clustered bar, `discom` by healthy/warning/critical meters
- Map visual: state or district if geocoding is enabled in the account

## Sheet 3: Communication

Visuals:

- RSSI Distribution: histogram of `rssi`
- Communication Issues: bar by `state` or `discom`, measure count where `comm_issue = true`
- Signal Quality Histogram: calculated `Signal Quality`
- Worst RSSI Table: `meter_id`, `state`, `district`, `discom`, `rssi`, `last_communication_time`, `health_status`

## Sheet 4: Electrical

Visuals:

- Voltage Distribution: histogram of `voltage`
- Power Factor Distribution: histogram of `power_factor`
- Voltage Violations: bar by `state`, measure count where `voltage_issue = true`
- Current Distribution: histogram of `current`
- Electrical Health Table: `meter_id`, `voltage`, `current`, `power_factor`, issue flags

## Sheet 5: Battery

Visuals:

- Battery % Distribution: histogram of `battery_pct`
- Battery Status: donut by `battery_status`
- Low Battery Devices: table filtered to `battery_issue = true`
- Battery by Firmware: `firmware_version` by average `battery_pct`

## Sheet 6: Consumption

Visuals:

- Daily Consumption: line chart `event_date` by sum `consumption_kwh`
- State-wise Consumption: bar `state` by sum `consumption_kwh`
- Top Feeders: bar `feeder_id` by sum `consumption_kwh`, top 20
- Top Districts: bar `district` by sum `consumption_kwh`

## Sheet 7: Firmware

Visuals:

- Firmware Version Distribution: bar `firmware_version` by distinct meters
- Firmware Health: stacked bar `firmware_version` grouped by `health_status`
- Firmware Issues Table: `firmware_version`, communication issues, signal issues, voltage issues, critical count

## Publishing Notes

1. In QuickSight, create a new dataset from Athena.
2. Select workgroup created by Terraform.
3. Select database `smart_meter_analytics`.
4. Select table `smart_meter_fleet_health` or the curated Athena views.
5. Import to SPICE.
6. Set row-level security later if state or DISCOM-level access separation is required.
7. Schedule SPICE refresh after the Glue ETL completes.
