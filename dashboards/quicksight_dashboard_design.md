# QuickSight Dashboard Design

Dashboard name: `Smart Meter Fleet Health Executive Dashboard`

Live dashboard ID: `smart-meter-fleet-health-executive-dashboard`

Published dashboard version: `2`

Primary dataset: Athena table `smart_meter_analytics.smart_meter_fleet_health`

Live QuickSight data source: `smart-meter-athena`

Live QuickSight dataset: `smart-meter-fleet-health-dataset`

Current import mode: `DIRECT_QUERY`

Recommended production import mode: SPICE for dashboard performance after the schema stabilizes.

Note: AWS Glue will show this as a PySpark script job, not as a visual ETL canvas. Build the visual charts in QuickSight using the dataset above.

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

## Deployed Sheet 1: Executive Overview

Created initial dashboard visuals:

- Total Smart Meters KPI
- Average Voltage KPI
- Average RSSI KPI
- Average Battery % KPI
- Average kWh KPI
- Fleet Health Status donut
- State-wise Health stacked bar
- Consumption by DISCOM bar
- Battery Status bar
- Fleet Summary table

## Deployed Sheet 2: Operations Detail

Created operations visuals:

- Firmware Distribution
- District Health
- Average Voltage by State
- Average RSSI by DISCOM
- Consumption by Feeder
- Device Detail table

## Future Expansion Ideas

Additional KPI cards:

- Total Smart Meters: distinct count of `meter_id`
- Healthy: distinct count where `health_status = Healthy`
- Warning: distinct count where `health_status = Warning`
- Critical: distinct count where `health_status = Critical`
- Average Voltage: average `voltage`
- Average RSSI: average `rssi`
- Average Battery %: average `battery_pct`
- Average Consumption: average `consumption_kwh`

Additional overview visuals:

- Health Status Donut: `health_status` by distinct count `meter_id`
- Meter Health Trend: `event_date` by distinct count `meter_id`, grouped by `health_status`
- Fleet Summary Table: `state`, `district`, `discom`, distinct meters, average voltage, average RSSI, average battery, warning count, critical count

### Geography

Visuals:

- State-wise Health: stacked bar, `state` by distinct meters grouped by `health_status`
- District-wise Heatmap: `district` by `health_status`, color by distinct meters
- DISCOM Comparison: clustered bar, `discom` by healthy/warning/critical meters
- Map visual: state or district if geocoding is enabled in the account

### Communication

Visuals:

- RSSI Distribution: histogram of `rssi`
- Communication Issues: bar by `state` or `discom`, measure count where `comm_issue = true`
- Signal Quality Histogram: calculated `Signal Quality`
- Worst RSSI Table: `meter_id`, `state`, `district`, `discom`, `rssi`, `last_communication_time`, `health_status`

### Electrical

Visuals:

- Voltage Distribution: histogram of `voltage`
- Power Factor Distribution: histogram of `power_factor`
- Voltage Violations: bar by `state`, measure count where `voltage_issue = true`
- Current Distribution: histogram of `current`
- Electrical Health Table: `meter_id`, `voltage`, `current`, `power_factor`, issue flags

### Battery

Visuals:

- Battery % Distribution: histogram of `battery_pct`
- Battery Status: donut by `battery_status`
- Low Battery Devices: table filtered to `battery_issue = true`
- Battery by Firmware: `firmware_version` by average `battery_pct`

### Consumption

Visuals:

- Daily Consumption: line chart `event_date` by sum `consumption_kwh`
- State-wise Consumption: bar `state` by sum `consumption_kwh`
- Top Feeders: bar `feeder_id` by sum `consumption_kwh`, top 20
- Top Districts: bar `district` by sum `consumption_kwh`

### Firmware

Visuals:

- Firmware Version Distribution: bar `firmware_version` by distinct meters
- Firmware Health: stacked bar `firmware_version` grouped by `health_status`
- Firmware Issues Table: `firmware_version`, communication issues, signal issues, voltage issues, critical count

## Publishing Notes

1. Open QuickSight in `us-east-1`.
2. Use dataset `smart-meter-fleet-health-dataset`.
3. Create a new analysis named `Smart Meter Fleet Health Executive Dashboard`.
4. Build the sheets and visuals from this document.
5. Publish the analysis as a dashboard.
6. For production, switch to SPICE or create a SPICE copy of the dataset after the schema stabilizes.
7. Set row-level security later if state or DISCOM-level access separation is required.
8. Schedule SPICE refresh after the Glue ETL completes if you use SPICE.
