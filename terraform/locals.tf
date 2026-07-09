resource "random_id" "suffix" {
  byte_length = 4
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  bucket_name = coalesce(var.bucket_name, "${local.name_prefix}-${random_id.suffix.hex}")

  raw_prefix            = "${var.lake_prefix}/raw"
  processed_prefix      = "${var.lake_prefix}/processed"
  athena_results_prefix = "${var.lake_prefix}/athena-results"
  scripts_prefix        = "${var.lake_prefix}/scripts"
  dashboards_prefix     = "${var.lake_prefix}/dashboards"
  logs_prefix           = "${var.lake_prefix}/logs"

  raw_s3_uri       = "s3://${aws_s3_bucket.data_lake.bucket}/${local.raw_prefix}/"
  processed_s3_uri = "s3://${aws_s3_bucket.data_lake.bucket}/${local.processed_prefix}/"
  script_s3_uri    = "s3://${aws_s3_bucket.data_lake.bucket}/${local.scripts_prefix}/glue_smart_meter_etl.py"

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Workload    = "smart-meter-fleet-health"
  }
}
