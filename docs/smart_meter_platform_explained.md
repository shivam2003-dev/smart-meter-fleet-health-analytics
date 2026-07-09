# Smart Meter Fleet Health Platform Explained

This document explains the project from two angles:

- Beginner view: what each part does and why it exists.
- Technical view: how the AWS services, data layout, ETL, Athena SQL, and QuickSight dashboard work together.

The goal is to make the platform understandable for someone new to AWS analytics while still being useful for engineers who need to operate or extend it.

## 1. What Problem This Solves

Electricity utilities can have thousands or millions of smart meters. Each meter sends readings such as voltage, current, consumption, signal strength, battery state, and last communication time.

Operations teams need to answer questions like:

- Which meters are healthy?
- Which meters stopped communicating?
- Which meters have poor signal?
- Which locations have voltage problems?
- Which firmware versions are causing issues?
- Which feeders, districts, or DISCOMs have abnormal consumption?

The platform turns raw smart meter readings into a dashboard that operations teams can use.

## 2. Simple Explanation

Think of the system like a factory line for data.

1. A CSV file arrives.
2. The file is stored safely in S3.
3. Glue reads the file and understands the columns.
4. Glue ETL cleans the file and converts it into a faster format.
5. Athena lets us ask SQL questions over the cleaned data.
6. QuickSight turns the SQL data into charts and tables.

In simple words:

```text
Raw file -> Clean data -> SQL tables -> Dashboard
```

## 3. Architecture

```text
final_dataset/smart_meter_fleet_health.csv
  |
  v
S3 raw/
  |
  v
Glue raw crawler
  |
  v
Glue Data Catalog
  |
  v
Glue ETL PySpark job
  |
  v
S3 processed/ as Snappy Parquet
  |
  v
Glue processed crawler
  |
  v
Athena table and views
  |
  v
QuickSight data source + dataset + dashboard
```

## 4. Dataset Columns

The dataset has 50,000 rows and these business fields:

```text
meter_id
timestamp
voltage
current
power_factor
last_communication_time
battery_status
battery_pct
rssi
firmware_version
state
district
discom
feeder_id
consumption_kwh
voltage_issue
power_factor_issue
comm_issue
signal_issue
battery_issue
health_status
```

The Glue ETL job adds these analytical fields:

```text
event_date
communication_lag_minutes
issue_count
year
month
day
```

## 5. AWS Services Used

### Amazon S3

S3 is object storage. In this project it stores:

- Raw CSV files.
- Processed Parquet files.
- Athena query results.
- Glue scripts.
- Spark UI logs.
- Dashboard support artifacts.

The project uses one bucket with this prefix layout:

```text
smart-meter-analytics/
  raw/
  processed/
  athena-results/
  scripts/
  dashboards/
  logs/
```

Why S3 is used:

- Cheap storage.
- Scales well.
- Works directly with Glue and Athena.
- Good base for a data lake.

### AWS Glue Crawlers

A crawler scans files and creates table metadata.

Example:

The raw crawler looks at the CSV in S3 and says:

```text
This file has columns like meter_id, timestamp, voltage, current...
```

The processed crawler looks at Parquet files and registers partitions:

```text
year=2024/month=01/day=01
year=2024/month=01/day=02
...
```

### AWS Glue Data Catalog

The Glue Data Catalog is a metadata store. It does not store the data itself. It stores information about where the data is and what columns it has.

Athena and QuickSight use the catalog to find the processed smart meter table.

Database:

```text
smart_meter_analytics
```

Main processed table:

```text
smart_meter_fleet_health
```

### AWS Glue ETL

Glue ETL runs the transformation code.

Main production job:

```text
smart-meter-analytics-dev-etl
```

Runtime:

```text
Glue 5.1
```

What the job does:

1. Reads the raw CSV.
2. Infers schema.
3. Fills missing values.
4. Casts columns to correct types.
5. Converts timestamps.
6. Removes duplicate `meter_id + timestamp` rows.
7. Calculates communication lag.
8. Recomputes issue count.
9. Recomputes health status.
10. Adds `event_date`, `year`, `month`, and `day`.
11. Writes Parquet files to S3.
12. Updates the Glue Data Catalog.

### Glue Studio Visual ETL

There is also a visual companion job:

```text
smart-meter-analytics-dev-visual-etl
```

This job is visible in AWS Glue Studio Visual ETL. It is not the main production ETL job. It exists so users can see a visual DAG.

Current visual nodes:

```text
Raw Smart Meter CSV
  -> Apply Smart Meter Schema
  -> Parquet Visual Preview Target
```

Why this is separate:

- The production ETL is a PySpark script because it has more precise transformation logic.
- The visual job helps people understand the flow inside Glue Studio.
- Keeping them separate avoids breaking the validated production pipeline.

### Amazon Athena

Athena lets you run SQL over S3 data.

Instead of loading data into a database server, Athena reads the Parquet files directly from S3 using the Glue Catalog.

Example query:

```sql
SELECT health_status, COUNT(*) AS readings
FROM smart_meter_fleet_health
GROUP BY health_status;
```

Athena workgroup:

```text
smart-meter-analytics-dev-wg
```

### Athena Views

Views are saved SQL queries. They make dashboard building easier.

Created views:

```text
vw_fleet_summary
vw_communication_health
vw_electrical_health
vw_battery_health
vw_daily_consumption
vw_monthly_consumption
vw_geographic_health
vw_firmware_distribution
vw_top_consumers
```

### Amazon QuickSight

QuickSight is the BI dashboard layer.

Created assets:

```text
Data source: smart-meter-athena
Dataset: smart-meter-fleet-health-dataset
Dashboard: Smart Meter Fleet Health Executive Dashboard
```

Published dashboard version:

```text
Version 2
```

Dashboard sheets:

```text
Executive Overview
Operations Detail
```

## 6. Why Parquet Instead Of CSV

CSV is easy to read but inefficient for analytics.

Parquet is better because:

- It stores data by column.
- Athena can scan less data.
- It compresses well.
- It keeps column types.
- It works well with partitioning.

The ETL writes:

```text
Snappy-compressed Parquet
```

This helps reduce Athena scan cost and improves query speed.

## 7. Why Partition By Date

Processed data is partitioned like this:

```text
processed/year=2024/month=01/day=01/
processed/year=2024/month=01/day=02/
```

Partitioning helps Athena skip data.

Example:

If a query only needs January data, Athena does not need to scan every day in the full year.

Good query pattern:

```sql
SELECT *
FROM smart_meter_fleet_health
WHERE year = '2024'
  AND month = '01';
```

## 8. Health Logic

The dataset contains issue flags:

```text
voltage_issue
power_factor_issue
comm_issue
signal_issue
battery_issue
```

The ETL calculates:

```text
issue_count =
  voltage_issue
  + power_factor_issue
  + comm_issue
  + signal_issue
  + battery_issue
```

Then it classifies health:

```text
0 issues       -> Healthy
1 or 2 issues  -> Warning
3+ issues      -> Critical
```

This makes the dashboard easy to scan.

## 9. Communication Health

Important fields:

```text
timestamp
last_communication_time
communication_lag_minutes
rssi
comm_issue
signal_issue
```

Meaning:

- `communication_lag_minutes` shows how stale the last meter communication is.
- `rssi` shows signal strength.
- Lower RSSI usually means weaker signal.
- `comm_issue` marks communication problems.
- `signal_issue` marks RF signal problems.

## 10. Electrical Health

Important fields:

```text
voltage
current
power_factor
voltage_issue
power_factor_issue
```

Use cases:

- Find over-voltage or under-voltage areas.
- Detect low power factor.
- Compare electrical quality across state, district, DISCOM, or feeder.

## 11. Battery Health

Important fields:

```text
battery_status
battery_pct
battery_issue
```

Use cases:

- Find meters with low battery.
- Compare low battery issues by geography.
- Check whether specific firmware versions drain batteries faster.

## 12. Consumption Analytics

Important fields:

```text
consumption_kwh
feeder_id
discom
district
state
```

Use cases:

- Daily consumption trend.
- Monthly consumption trend.
- Top consuming meters.
- Top feeders.
- Consumption by DISCOM.

## 13. How The Dashboard Is Built

The dashboard reads from this QuickSight dataset:

```text
smart-meter-fleet-health-dataset
```

The dataset uses Athena Direct Query.

Current dashboard visuals include:

Executive Overview:

- Total Smart Meters KPI.
- Average Voltage KPI.
- Average RSSI KPI.
- Average Battery % KPI.
- Average kWh KPI.
- Fleet Health Status donut.
- State-wise Health stacked bar.
- Consumption by DISCOM.
- Battery Status.
- Fleet Summary table.

Operations Detail:

- Firmware Distribution.
- District Health.
- Average Voltage by State.
- Average RSSI by DISCOM.
- Consumption by Feeder.
- Device Detail table.

## 14. What Terraform Creates

Terraform creates most infrastructure:

- S3 bucket.
- S3 prefixes.
- Glue database.
- Glue crawlers.
- Glue ETL job.
- IAM Glue role.
- Athena workgroup.
- CloudWatch log groups.
- QuickSight service role policy for Athena/S3 access.

Terraform does not fully manage Glue Studio visual nodes because the current Terraform AWS provider used here does not expose `CodeGenConfigurationNodes` for `aws_glue_job`. The visual job was created through the AWS Glue API and is documented in this repo.

## 15. What Was Deployed

AWS account:

```text
469863270891
```

Main deployed resources:

```text
S3 bucket: smart-meter-analytics-dev-529159d1
Glue database: smart_meter_analytics
Glue production job: smart-meter-analytics-dev-etl
Glue visual job: smart-meter-analytics-dev-visual-etl
Raw crawler: smart-meter-analytics-dev-raw-crawler
Processed crawler: smart-meter-analytics-dev-processed-crawler
Athena workgroup: smart-meter-analytics-dev-wg
QuickSight dashboard: smart-meter-fleet-health-executive-dashboard
```

## 16. How To Run The Pipeline

Export fresh temporary AWS credentials first. Do not save them in files.

Then:

```bash
cd terraform
terraform output
```

Run the raw crawler:

```bash
aws glue start-crawler --name smart-meter-analytics-dev-raw-crawler
```

Run the ETL:

```bash
aws glue start-job-run --job-name smart-meter-analytics-dev-etl
```

Run the processed crawler:

```bash
aws glue start-crawler --name smart-meter-analytics-dev-processed-crawler
```

Run Athena validation:

```sql
SELECT COUNT(*) AS rows,
       COUNT(DISTINCT meter_id) AS meters
FROM smart_meter_fleet_health;
```

Expected result:

```text
rows = 50000
meters = 50000
```

## 17. How To See The Visual Glue Job

In AWS Console:

1. Open AWS Glue.
2. Go to ETL jobs.
3. Open Visual ETL.
4. Search for:

```text
smart-meter-analytics-dev-visual-etl
```

You should see:

```text
Raw Smart Meter CSV
  -> Apply Smart Meter Schema
  -> Parquet Visual Preview Target
```

## 18. How To See The Dashboard

In QuickSight:

1. Open Dashboards.
2. Open:

```text
Smart Meter Fleet Health Executive Dashboard
```

3. Use the two sheets:

```text
Executive Overview
Operations Detail
```

## 19. Beginner Glossary

### Data Lake

A storage area where raw and processed data is kept. Here, S3 is the data lake.

### Raw Zone

The place where original files are stored without modification.

### Processed Zone

The place where cleaned and optimized files are stored.

### Crawler

A service that scans files and creates table metadata.

### Data Catalog

A metadata database that stores table names, columns, partitions, and file locations.

### ETL

Extract, Transform, Load.

In this project:

- Extract from raw CSV.
- Transform into clean typed records.
- Load to Parquet.

### Parquet

A column-based file format optimized for analytics.

### Athena

A serverless SQL query engine for S3 data.

### QuickSight

AWS dashboard and BI service.

### IAM

Identity and Access Management. IAM controls what services can access.

## 20. Advanced Engineering Notes

### Rerunnable ETL

The production ETL supports clearing the processed path before writing. This avoids stale files and makes reruns predictable for this sample workload.

### Catalog Updates

The ETL writes DynamicFrames through a Glue sink with catalog update behavior enabled. The processed crawler then confirms the final partition metadata.

### Direct Query Vs SPICE

Current QuickSight mode:

```text
DIRECT_QUERY
```

This is useful while the schema is changing.

For production dashboards, consider SPICE:

- Faster dashboard loads.
- Less Athena query load.
- Scheduled refresh after ETL completes.

### Security

The S3 bucket blocks public access and uses encryption. IAM policies are scoped to the project bucket, Glue catalog operations, and Athena workgroup access.

### Cost Optimization

Main cost controls:

- Parquet instead of CSV for Athena.
- Snappy compression.
- Date partitions.
- Athena workgroup output location.
- S3 lifecycle expiration for Athena results and logs.
- QuickSight SPICE option for high dashboard usage.

## 21. Production Extensions

For real AMI/HES integrations:

- Land real exports in the same S3 raw prefix.
- Keep the same logical columns.
- Add schema drift checks.
- Add EventBridge or Lambda trigger after upload.
- Add Glue workflow orchestration.
- Add SNS notifications for failed jobs.
- Add row-level security in QuickSight by state, district, or DISCOM.
- Add data quality checks for voltage ranges, RSSI ranges, duplicate readings, and missing timestamps.

## 22. References

- AWS Glue Visual Job API: https://docs.aws.amazon.com/glue/latest/dg/visual-job-api-chapter.html
- AWS Glue Visual Job API data types: https://docs.aws.amazon.com/glue/latest/dg/aws-glue-api-visual-job-api.html
- AWS Glue CreateJob API: https://docs.aws.amazon.com/glue/latest/webapi/API_CreateJob.html
