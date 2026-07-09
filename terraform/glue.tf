resource "aws_cloudwatch_log_group" "glue" {
  name              = "/aws-glue/jobs/${local.name_prefix}"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "glue_crawlers" {
  name              = "/aws-glue/crawlers/${local.name_prefix}"
  retention_in_days = 30
}

resource "aws_glue_catalog_database" "smart_meter" {
  name        = var.glue_database_name
  description = "Smart meter fleet health analytics catalog."
}

resource "aws_glue_crawler" "raw" {
  name          = "${local.name_prefix}-raw-crawler"
  role          = aws_iam_role.glue_role.arn
  database_name = aws_glue_catalog_database.smart_meter.name
  table_prefix  = var.raw_crawler_table_prefix

  s3_target {
    path = local.raw_s3_uri
  }

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Tables = {
        AddOrUpdateBehavior = "MergeNewColumns"
      }
      Partitions = {
        AddOrUpdateBehavior = "InheritFromTable"
      }
    }
  })

  depends_on = [aws_s3_object.raw_dataset]
}

resource "aws_glue_crawler" "processed" {
  name          = "${local.name_prefix}-processed-crawler"
  role          = aws_iam_role.glue_role.arn
  database_name = aws_glue_catalog_database.smart_meter.name

  s3_target {
    path = local.processed_s3_uri
  }

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Tables = {
        AddOrUpdateBehavior = "MergeNewColumns"
      }
      Partitions = {
        AddOrUpdateBehavior = "InheritFromTable"
      }
    }
  })
}

resource "aws_glue_job" "smart_meter_etl" {
  name              = "${local.name_prefix}-etl"
  role_arn          = aws_iam_role.glue_role.arn
  glue_version      = "4.0"
  worker_type       = var.glue_job_worker_type
  number_of_workers = var.glue_job_number_of_workers
  timeout           = 30
  max_retries       = 1

  command {
    name            = "glueetl"
    script_location = local.script_s3_uri
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--enable-metrics"                   = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-spark-ui"                  = "true"
    "--spark-event-logs-path"            = "s3://${aws_s3_bucket.data_lake.bucket}/${local.logs_prefix}/spark-ui/"
    "--RAW_S3_PATH"                      = local.raw_s3_uri
    "--PROCESSED_S3_PATH"                = local.processed_s3_uri
    "--GLUE_DATABASE"                    = aws_glue_catalog_database.smart_meter.name
    "--PROCESSED_TABLE_NAME"             = var.processed_table_name
    "--CLEAR_PROCESSED"                  = "true"
  }

  execution_property {
    max_concurrent_runs = 1
  }

  depends_on = [
    aws_s3_object.glue_script,
    aws_cloudwatch_log_group.glue
  ]
}
