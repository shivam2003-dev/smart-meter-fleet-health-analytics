# Deployment Guide

## Prerequisites

- AWS CLI authenticated for the target account.
- Terraform 1.6 or newer.
- QuickSight enabled in the target AWS account if the dashboard will be created.
- Local dataset present at `final_dataset/smart_meter_fleet_health.csv`.

Do not commit AWS access keys or session tokens. Export credentials in the shell running Terraform.

## Deploy Infrastructure

```bash
export AWS_DEFAULT_REGION="us-east-1"

cd terraform
terraform init
terraform plan -out tfplan
terraform apply tfplan
```

Terraform uploads:

- Raw CSV to `s3://<bucket>/smart-meter-analytics/raw/`
- Glue ETL script to `s3://<bucket>/smart-meter-analytics/scripts/`
- Athena SQL scripts to `s3://<bucket>/smart-meter-analytics/scripts/athena/`

## Run the Data Pipeline

Use the Terraform outputs for exact names:

```bash
aws glue start-crawler --name "$(terraform output -raw raw_crawler_name)"

aws glue start-job-run --job-name "$(terraform output -raw glue_job_name)"

aws glue start-crawler --name "$(terraform output -raw processed_crawler_name)"
```

Check status:

```bash
aws glue get-crawler --name "$(terraform output -raw raw_crawler_name)"
aws glue get-job-runs --job-name "$(terraform output -raw glue_job_name)" --max-results 5
aws glue get-crawler --name "$(terraform output -raw processed_crawler_name)"
```

## Create Athena Views

Open Athena and run `athena/sql/01_create_views.sql` in the workgroup printed by Terraform.

Athena `StartQueryExecution` accepts one SQL statement at a time. If using the CLI, split the view file on semicolons and submit each statement separately. Skip the `USE smart_meter_analytics` statement when you pass `--query-execution-context Database=smart_meter_analytics`.

```bash
cd ..
python3 - <<'PY'
import pathlib

for statement in pathlib.Path("athena/sql/01_create_views.sql").read_text().split(";"):
    statement = statement.strip()
    if statement and not statement.lower().startswith("use "):
        print(statement + ";\n")
PY
```

Paste each printed statement into Athena, or wrap the same split logic around `aws athena start-query-execution`.

## QuickSight

Follow `dashboards/quicksight_dashboard_design.md`.

Live assets created during validation:

- Data source: `smart-meter-athena`
- Dataset: `smart-meter-fleet-health-dataset`
- Import mode: `DIRECT_QUERY`
- Database: `smart_meter_analytics`
- Table: `smart_meter_fleet_health`
- Dashboard: `Smart Meter Fleet Health Executive Dashboard`
- Published dashboard version: `2`

QuickSight requires access to the Athena result bucket. Terraform attaches the `smart-meter-athena-access` inline policy to the existing QuickSight service role `aws-quicksight-service-role-v0`.

## Glue Studio Visual ETL

The production AWS Glue job is a PySpark script job:

```text
smart-meter-analytics-dev-etl
```

There is also a visual companion job for Glue Studio:

```text
smart-meter-analytics-dev-visual-etl
```

Open AWS Glue > ETL jobs > Visual ETL and search for that job. It shows:

```text
Raw Smart Meter CSV
  -> Apply Smart Meter Schema
  -> Parquet Visual Preview Target
```

The visual job is for inspection and demonstration. The production analytics pipeline uses the PySpark job because it contains the full cleaning, partitioning, deduplication, health-status recomputation, and catalog update logic.

Dashboard visuals are built in QuickSight, not in the Glue job editor.

## Destroy

Only for non-production:

```bash
cd terraform
terraform destroy
```

If `force_destroy_bucket=false`, empty the S3 bucket first.
