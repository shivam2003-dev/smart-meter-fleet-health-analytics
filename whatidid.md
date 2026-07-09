# Smart Meter AWS Deployment Runbook

This file records the deployment and validation flow for the Smart Meter Fleet Health Analytics platform.

Do not paste or commit AWS secret values into this repository. Use temporary shell exports only when running commands.

## 1. Credential Safety

I first found that the terminal had old default AWS CLI credentials configured. Those credentials pointed to the wrong AWS account and caused an accidental partial Terraform apply.

The old local AWS auth files were moved to a backup folder:

```bash
/Users/shivamkumar/.aws/codex-disabled-20260709-120151
```

The active AWS files were replaced with empty files:

```bash
~/.aws/config
~/.aws/credentials
```

Validation command:

```bash
aws sts get-caller-identity
```

Expected result without explicit credentials:

```text
NoCredentials
```

## 2. Wrong Account Cleanup

The first accidental partial deploy happened in account:

```text
149465616208
```

Principal:

```text
arn:aws:iam::149465616208:user/terraform
```

Terraform created a partial stack there, then failed on missing Glue/Athena permissions. I destroyed those partial resources with:

```bash
cd terraform
terraform destroy -auto-approve -var='force_destroy_bucket=true'
```

Result:

```text
30 resources destroyed
```

## 3. Intended Account

The intended deployment account is:

```text
469863270891
```

Principal type:

```text
arn:aws:sts::469863270891:assumed-role/WSParticipantRole/Participant
```

Before doing any deploy or validation, confirm the active identity:

```bash
export AWS_DEFAULT_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="<temporary-access-key>"
export AWS_SECRET_ACCESS_KEY="<temporary-secret-key>"
export AWS_SESSION_TOKEN="<temporary-session-token>"

aws sts get-caller-identity --query '{Account:Account,Arn:Arn}' --output json
```

Only continue if the account is `469863270891`.

## 4. Terraform Deploy

From the repo root:

```bash
cd terraform
terraform init
terraform fmt -recursive
terraform validate
terraform apply -auto-approve
```

The successful deploy created:

```text
S3 bucket: smart-meter-analytics-dev-529159d1
Glue database: smart_meter_analytics
Raw crawler: smart-meter-analytics-dev-raw-crawler
Processed crawler: smart-meter-analytics-dev-processed-crawler
Glue ETL job: smart-meter-analytics-dev-etl
Athena workgroup: smart-meter-analytics-dev-wg
```

Terraform output command:

```bash
terraform output
```

## 5. Raw Crawler

Run the raw crawler to catalog the uploaded CSV:

```bash
aws glue start-crawler --name smart-meter-analytics-dev-raw-crawler
```

Poll until it returns `READY`:

```bash
aws glue get-crawler \
  --name smart-meter-analytics-dev-raw-crawler \
  --query 'Crawler.{State:State,LastCrawl:LastCrawl}' \
  --output json
```

Validated result:

```text
Status: SUCCEEDED
```

## 6. Glue ETL

Run the ETL job:

```bash
aws glue start-job-run --job-name smart-meter-analytics-dev-etl
```

Poll the job run:

```bash
aws glue get-job-run \
  --job-name smart-meter-analytics-dev-etl \
  --run-id <job-run-id> \
  --query 'JobRun.{State:JobRunState,ErrorMessage:ErrorMessage,ExecutionTime:ExecutionTime,DPUSeconds:DPUSeconds}' \
  --output json
```

Validated result:

```text
State: SUCCEEDED
Execution time: 105 seconds
DPU seconds: 210.0
```

The job reads the raw CSV, cleans and deduplicates rows, converts timestamps, adds `year`, `month`, and `day`, then writes Snappy-compressed Parquet to:

```text
s3://smart-meter-analytics-dev-529159d1/smart-meter-analytics/processed/
```

## 7. Processed Crawler

Run the processed crawler to catalog the Parquet partitions:

```bash
aws glue start-crawler --name smart-meter-analytics-dev-processed-crawler
```

Poll until it returns `READY`:

```bash
aws glue get-crawler \
  --name smart-meter-analytics-dev-processed-crawler \
  --query 'Crawler.{State:State,LastCrawl:LastCrawl}' \
  --output json
```

Validated result:

```text
Status: SUCCEEDED
```

## 8. Remaining Validation Checklist

After the processed crawler succeeds, validate these items:

```bash
aws s3 ls s3://smart-meter-analytics-dev-529159d1/smart-meter-analytics/raw/
aws s3 ls s3://smart-meter-analytics-dev-529159d1/smart-meter-analytics/processed/ --recursive --summarize

aws glue get-database --name smart_meter_analytics
aws glue get-tables --database-name smart_meter_analytics
aws glue get-partitions --database-name smart_meter_analytics --table-name <processed-table-name>
```

Then run Athena queries through workgroup:

```text
smart-meter-analytics-dev-wg
```

The view DDL is in:

```text
athena/sql/01_create_views.sql
```

Query examples are in:

```text
athena/queries/
```

Validated results from this deployment:

```text
Raw CSV object: present
Processed Parquet objects: 1,461
Processed table partitions: 365
Athena row count: 50,000
Athena distinct meters: 50,000
Date range: 2024-01-01 to 2024-12-30
Health status readings: Healthy 40,134; Warning 9,848; Critical 18
Athena views created: 9
Dashboard query files executed: 17 SQL statements, all succeeded
```

The created Athena views are:

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

## 9. QuickSight

QuickSight is enabled in the target account:

```text
Edition: ENTERPRISE
Namespace: default
QuickSight user: WSParticipantRole/Participant
Role: ADMIN_PRO
```

I created and validated the Athena data source:

```text
Data source ID: smart-meter-athena
Status: UPDATE_SUCCESSFUL
Athena workgroup: smart-meter-analytics-dev-wg
```

The first QuickSight data source attempt failed because QuickSight could not access the Athena output bucket. I fixed that by attaching an inline policy named `smart-meter-athena-access` to the existing QuickSight service role:

```text
aws-quicksight-service-role-v0
```

That policy is now managed by Terraform in:

```text
terraform/quicksight.tf
```

I also created the QuickSight Direct Query dataset:

```text
Dataset ID: smart-meter-fleet-health-dataset
Dataset name: Smart Meter Fleet Health
Output columns: 27
Source table: smart_meter_analytics.smart_meter_fleet_health
```

I created the actual QuickSight dashboard:

```text
Dashboard name: Smart Meter Fleet Health Executive Dashboard
Dashboard ID: smart-meter-fleet-health-executive-dashboard
Dashboard ARN: arn:aws:quicksight:us-east-1:469863270891:dashboard/smart-meter-fleet-health-executive-dashboard
Published version: 2
Status: CREATION_SUCCESSFUL
```

The compact published dashboard contains two sheets:

```text
Executive Overview
Operations Detail
```

Executive Overview contains:

```text
Total Smart Meters KPI
Average Voltage KPI
Average RSSI KPI
Average Battery % KPI
Average kWh KPI
Fleet Health Status donut
State-wise Health stacked bar
Consumption by DISCOM bar
Battery Status bar
Fleet Summary table
```

Operations Detail contains:

```text
Firmware Distribution
District Health
Average Voltage by State
Average RSSI by DISCOM
Consumption by Feeder
Device Detail table
```

For dashboard design notes, use:

```text
dashboards/quicksight_dashboard_design.md
```

Important: the production AWS Glue job page is a script editor for the PySpark ETL job. It will not show dashboard charts. The dashboard charts belong in QuickSight.

## 10. Glue Studio Visual ETL Job

I created a separate Glue Studio visual companion job:

```text
Job name: smart-meter-analytics-dev-visual-etl
Job mode: VISUAL
Glue version: 5.1
Visual nodes: 3
```

The visual DAG is:

```text
Raw Smart Meter CSV
  -> Apply Smart Meter Schema
  -> Parquet Visual Preview Target
```

This visual job is for Glue Studio visual inspection. The production analytics ETL remains:

```text
smart-meter-analytics-dev-etl
```

I kept them separate so the validated production PySpark job stays stable while Glue Studio still shows a visual flow.

## 11. Glue Version Update

I updated the Glue runtime from `4.0` to `5.1` through Terraform:

```text
terraform/variables.tf: glue_version default is 5.1
terraform/glue.tf: aws_glue_job.smart_meter_etl uses var.glue_version
```

Terraform apply succeeded and AWS accepted the Glue job update:

```text
Glue job: smart-meter-analytics-dev-etl
Glue version: 5.1
```

I attempted to rerun the ETL after the upgrade. AWS first reported `ConcurrentRunsExceededException`, meaning a job run was still active or locked by the configured max concurrency. Immediately after that, the temporary AWS session token stopped working and AWS returned `UnrecognizedClientException`.

Post-upgrade ETL rerun is the only remaining validation step. To finish it, export fresh temporary AWS credentials for account `469863270891` and run:

```bash
aws glue get-job --job-name smart-meter-analytics-dev-etl --query 'Job.GlueVersion' --output text
aws glue get-job-runs --job-name smart-meter-analytics-dev-etl --max-results 10
aws glue start-job-run --job-name smart-meter-analytics-dev-etl
```

## 11. GitHub

The project was committed and pushed to:

```text
https://github.com/shivam2003-dev/smart-meter-fleet-health-analytics
```

Before pushing more changes:

```bash
git status --short
git add <files>
git commit -m "<message>"
git push
```

Never commit:

```text
terraform.tfstate
.terraform/
AWS credentials
Hugging Face tokens
API keys
```
