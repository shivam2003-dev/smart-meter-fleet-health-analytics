output "bucket_name" {
  description = "S3 data lake bucket."
  value       = aws_s3_bucket.data_lake.bucket
}

output "raw_s3_uri" {
  description = "Raw data S3 URI."
  value       = local.raw_s3_uri
}

output "processed_s3_uri" {
  description = "Processed Parquet S3 URI."
  value       = local.processed_s3_uri
}

output "glue_database_name" {
  description = "Glue database name."
  value       = aws_glue_catalog_database.smart_meter.name
}

output "raw_crawler_name" {
  description = "Raw crawler name."
  value       = aws_glue_crawler.raw.name
}

output "processed_crawler_name" {
  description = "Processed crawler name."
  value       = aws_glue_crawler.processed.name
}

output "glue_job_name" {
  description = "Glue ETL job name."
  value       = aws_glue_job.smart_meter_etl.name
}

output "athena_workgroup" {
  description = "Athena workgroup name."
  value       = aws_athena_workgroup.smart_meter.name
}
