variable "environment" {
  description = "Deployment environment name"
  type        = string
  default     = "staging"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "s3_bucket_name" {
  description = "Name for the attachments bucket"
  type        = string
}

variable "access_log_bucket" {
  description = "Optional bucket for server access logs"
  type        = string
  default     = ""
}

