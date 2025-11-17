terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.66"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  bucket_name = var.s3_bucket_name
  tags = {
    Project     = "telegram-complaint-system"
    Environment = var.environment
  }
}

data "aws_caller_identity" "current" {}

resource "aws_kms_key" "attachments" {
  description             = "S3 encryption key for complaint attachments"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  tags                    = local.tags
}

resource "aws_kms_alias" "attachments" {
  name          = "alias/${var.environment}-complaint-attachments"
  target_key_id = aws_kms_key.attachments.key_id
}

resource "aws_s3_bucket" "attachments" {
  bucket = local.bucket_name
  tags   = local.tags
}

resource "aws_s3_bucket_public_access_block" "attachments" {
  bucket                  = aws_s3_bucket.attachments.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "attachments" {
  bucket = aws_s3_bucket.attachments.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_logging" "attachments" {
  bucket = aws_s3_bucket.attachments.id
  target_bucket = var.access_log_bucket != "" ? var.access_log_bucket : aws_s3_bucket.attachments.id
  target_prefix = "logs/"
}

resource "aws_s3_bucket_lifecycle_configuration" "attachments" {
  bucket = aws_s3_bucket.attachments.id

  rule {
    id     = "transition"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 365
      storage_class = "GLACIER_IR"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "attachments" {
  bucket = aws_s3_bucket.attachments.id
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.attachments.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_cloudfront_origin_access_control" "attachments" {
  name                              = "${var.environment}-complaint-oac"
  description                       = "CloudFront access control for complaint attachments"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "attachments" {
  enabled             = true
  default_root_object = ""
  comment             = "Complaint attachments distribution"

  origin {
    domain_name              = aws_s3_bucket.attachments.bucket_regional_domain_name
    origin_id                = "attachments"
    origin_access_control_id = aws_cloudfront_origin_access_control.attachments.id
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "attachments"
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      headers      = []
    }
  }

  price_class = "PriceClass_100"

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = local.tags
}

resource "aws_iam_role" "backend" {
  name               = "${var.environment}-complaint-backend"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
  tags               = local.tags
}

resource "aws_iam_policy" "backend_s3" {
  name   = "${var.environment}-complaint-backend-s3"
  policy = data.aws_iam_policy_document.backend.json
}

resource "aws_iam_role_policy_attachment" "backend_attach" {
  role       = aws_iam_role.backend.name
  policy_arn = aws_iam_policy.backend_s3.arn
}

resource "aws_iam_role" "worker" {
  name               = "${var.environment}-complaint-worker"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
  tags               = local.tags
}

resource "aws_iam_policy" "worker_s3" {
  name   = "${var.environment}-complaint-worker-s3"
  policy = data.aws_iam_policy_document.worker.json
}

resource "aws_iam_role_policy_attachment" "worker_attach" {
  role       = aws_iam_role.worker.name
  policy_arn = aws_iam_policy.worker_s3.arn
}

resource "aws_sqs_queue" "photo_events" {
  name                      = "${var.environment}-complaint-photo-events"
  visibility_timeout_seconds = 120
  message_retention_seconds   = 1209600
  tags                       = local.tags
}

resource "aws_sqs_queue_policy" "photo_events" {
  queue_url = aws_sqs_queue.photo_events.id
  policy    = data.aws_iam_policy_document.sqs_policy.json
}

resource "aws_s3_bucket_notification" "attachments" {
  bucket = aws_s3_bucket.attachments.id

  queue {
    queue_arn     = aws_sqs_queue.photo_events.arn
    events        = ["s3:ObjectCreated:*"]
    filter_suffix = ".jpg"
  }
}

data "aws_iam_policy_document" "ecs_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com", "ec2.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "backend" {
  statement {
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:DeleteObject",
      "s3:ListBucket"
    ]
    resources = [
      aws_s3_bucket.attachments.arn,
      "${aws_s3_bucket.attachments.arn}/*"
    ]
  }

  statement {
    actions = [
      "kms:Decrypt",
      "kms:Encrypt",
      "kms:GenerateDataKey"
    ]
    resources = [aws_kms_key.attachments.arn]
  }
}

data "aws_iam_policy_document" "worker" {
  statement {
    actions = [
      "s3:GetObject",
      "s3:PutObject"
    ]
    resources = [
      "${aws_s3_bucket.attachments.arn}/complaints/*"
    ]
  }

  statement {
    actions = [
      "kms:Decrypt",
      "kms:Encrypt",
      "kms:GenerateDataKey"
    ]
    resources = [aws_kms_key.attachments.arn]
  }

  statement {
    actions   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
    resources = [aws_sqs_queue.photo_events.arn]
  }
}

data "aws_iam_policy_document" "sqs_policy" {
  statement {
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.photo_events.arn]
    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }
    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_s3_bucket.attachments.arn]
    }
  }
}

