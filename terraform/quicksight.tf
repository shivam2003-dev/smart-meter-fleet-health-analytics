data "aws_iam_role" "quicksight_service_role" {
  count = var.enable_quicksight_service_role_policy ? 1 : 0

  name = var.quicksight_service_role_name
}

data "aws_iam_policy_document" "quicksight_athena_access" {
  count = var.enable_quicksight_service_role_policy ? 1 : 0

  statement {
    sid = "SmartMeterAthenaResultsBucketAccess"
    actions = [
      "s3:GetBucketLocation",
      "s3:ListBucket",
      "s3:ListBucketMultipartUploads"
    ]
    resources = [aws_s3_bucket.data_lake.arn]
  }

  statement {
    sid = "SmartMeterAthenaResultsObjectAccess"
    actions = [
      "s3:AbortMultipartUpload",
      "s3:DeleteObject",
      "s3:GetObject",
      "s3:ListMultipartUploadParts",
      "s3:PutObject"
    ]
    resources = ["${aws_s3_bucket.data_lake.arn}/${var.lake_prefix}/*"]
  }

  statement {
    sid = "SmartMeterAthenaQueryAccess"
    actions = [
      "athena:GetQueryExecution",
      "athena:GetQueryResults",
      "athena:GetWorkGroup",
      "athena:StartQueryExecution",
      "athena:StopQueryExecution"
    ]
    resources = [aws_athena_workgroup.smart_meter.arn]
  }

  statement {
    sid = "SmartMeterGlueCatalogRead"
    actions = [
      "glue:GetDatabase",
      "glue:GetDatabases",
      "glue:GetPartition",
      "glue:GetPartitions",
      "glue:GetTable",
      "glue:GetTables"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "quicksight_athena_access" {
  count = var.enable_quicksight_service_role_policy ? 1 : 0

  name   = "smart-meter-athena-access"
  role   = data.aws_iam_role.quicksight_service_role[0].id
  policy = data.aws_iam_policy_document.quicksight_athena_access[0].json
}
