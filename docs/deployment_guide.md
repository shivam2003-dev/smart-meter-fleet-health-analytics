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

CLI option:

```bash
aws athena start-query-execution \
  --work-group "$(terraform output -raw athena_workgroup)" \
  --query-string file://../athena/sql/01_create_views.sql
```

If your shell does not expand `file://` content, paste the SQL into the Athena editor.

## QuickSight

Follow `dashboards/quicksight_dashboard_design.md`.

Recommended dataset:

- Database: `smart_meter_analytics`
- Table: `smart_meter_fleet_health`
- Import mode: SPICE

## Destroy

Only for non-production:

```bash
cd terraform
terraform destroy
```

If `force_destroy_bucket=false`, empty the S3 bucket first.
