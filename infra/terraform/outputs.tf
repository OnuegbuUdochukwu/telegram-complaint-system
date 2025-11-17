output "s3_bucket_name" {
  value       = aws_s3_bucket.attachments.bucket
  description = "Name of the attachments bucket"
}

output "cloudfront_domain" {
  value       = aws_cloudfront_distribution.attachments.domain_name
  description = "CloudFront distribution domain"
}

output "kms_key_arn" {
  value       = aws_kms_key.attachments.arn
  description = "KMS key ARN for SSE-KMS"
}

output "sqs_queue_arn" {
  value       = aws_sqs_queue.photo_events.arn
  description = "SQS queue for S3 object-created events"
}

