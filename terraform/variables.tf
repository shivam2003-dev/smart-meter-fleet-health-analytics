variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming."
  type        = string
  default     = "smart-meter-analytics"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "dev"
}

variable "bucket_name" {
  description = "Optional globally unique S3 bucket name. Leave null to generate one."
  type        = string
  default     = null
}

variable "lake_prefix" {
  description = "Top-level data lake prefix inside the bucket."
  type        = string
  default     = "smart-meter-analytics"
}

variable "local_dataset_path" {
  description = "Local path to the smart meter CSV file."
  type        = string
  default     = "../final_dataset/smart_meter_fleet_health.csv"
}

variable "glue_database_name" {
  description = "Glue database name."
  type        = string
  default     = "smart_meter_analytics"
}

variable "processed_table_name" {
  description = "Glue/Athena table name for processed Parquet data."
  type        = string
  default     = "smart_meter_fleet_health"
}

variable "raw_crawler_table_prefix" {
  description = "Prefix for raw tables discovered by the crawler."
  type        = string
  default     = "raw_"
}

variable "glue_job_worker_type" {
  description = "Glue worker type."
  type        = string
  default     = "G.1X"
}

variable "glue_job_number_of_workers" {
  description = "Number of Glue workers."
  type        = number
  default     = 2
}

variable "enable_s3_versioning" {
  description = "Enable versioning on the data lake bucket."
  type        = bool
  default     = true
}

variable "force_destroy_bucket" {
  description = "Allow Terraform to destroy non-empty buckets in non-production environments."
  type        = bool
  default     = false
}
