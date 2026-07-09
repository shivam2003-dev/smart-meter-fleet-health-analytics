resource "aws_athena_workgroup" "smart_meter" {
  name        = "${local.name_prefix}-wg"
  description = "Athena workgroup for smart meter fleet health analytics."
  state       = "ENABLED"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.data_lake.bucket}/${local.athena_results_prefix}/"

      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }
  }
}

resource "aws_cloudwatch_log_group" "athena" {
  name              = "/aws/athena/${local.name_prefix}"
  retention_in_days = 30
}
