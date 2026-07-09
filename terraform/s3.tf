resource "aws_s3_bucket" "data_lake" {
  bucket        = local.bucket_name
  force_destroy = var.force_destroy_bucket
}

resource "aws_s3_bucket_public_access_block" "data_lake" {
  bucket                  = aws_s3_bucket.data_lake.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  versioning_configuration {
    status = var.enable_s3_versioning ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "athena-results-expire"
    status = "Enabled"

    filter {
      prefix = "${local.athena_results_prefix}/"
    }

    expiration {
      days = 30
    }
  }

  rule {
    id     = "logs-expire"
    status = "Enabled"

    filter {
      prefix = "${local.logs_prefix}/"
    }

    expiration {
      days = 90
    }
  }
}

resource "aws_s3_object" "folders" {
  for_each = toset([
    "${local.raw_prefix}/",
    "${local.processed_prefix}/",
    "${local.athena_results_prefix}/",
    "${local.scripts_prefix}/",
    "${local.dashboards_prefix}/",
    "${local.logs_prefix}/"
  ])

  bucket       = aws_s3_bucket.data_lake.id
  key          = each.value
  content      = ""
  content_type = "application/x-directory"
}

resource "aws_s3_object" "raw_dataset" {
  bucket       = aws_s3_bucket.data_lake.id
  key          = "${local.raw_prefix}/smart_meter_fleet_health.csv"
  source       = var.local_dataset_path
  etag         = filemd5(var.local_dataset_path)
  content_type = "text/csv"
}

resource "aws_s3_object" "glue_script" {
  bucket       = aws_s3_bucket.data_lake.id
  key          = "${local.scripts_prefix}/glue_smart_meter_etl.py"
  source       = "${path.module}/../glue/glue_smart_meter_etl.py"
  etag         = filemd5("${path.module}/../glue/glue_smart_meter_etl.py")
  content_type = "text/x-python"
}

resource "aws_s3_object" "athena_sql" {
  for_each = fileset("${path.module}/../athena", "**/*.sql")

  bucket       = aws_s3_bucket.data_lake.id
  key          = "${local.scripts_prefix}/athena/${each.value}"
  source       = "${path.module}/../athena/${each.value}"
  etag         = filemd5("${path.module}/../athena/${each.value}")
  content_type = "text/sql"
}
