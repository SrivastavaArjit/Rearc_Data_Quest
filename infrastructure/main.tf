provider "aws" {
  region = "ap-south-1" # Mumbai (Default)
}

provider "aws" {
  alias  = "bucket_region"
  region = "eu-north-1" # Stockholm (Bucket Home)
}

# 1. Reference the EXISTING S3 Bucket
data "aws_s3_bucket" "quest_bucket" {
  provider = aws.bucket_region
  bucket   = "data-quest-bucket-rearc"
}

# Create the Queue in Stockholm
resource "aws_sqs_queue" "analytics_queue" {
  provider = aws.bucket_region
  name     = "s3-json-upload-queue"
  visibility_timeout_seconds = 300
  
  # Policy allowing the Stockholm S3 bucket to send messages
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "s3.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = "arn:aws:sqs:eu-north-1:*:s3-json-upload-queue"
      Condition = {
        ArnLike = { "aws:SourceArn": data.aws_s3_bucket.quest_bucket.arn }
      }
    }]
  })
}

# Update Notification to point to the Queue
resource "aws_s3_bucket_notification" "bucket_notification" {
  provider = aws.bucket_region
  bucket   = data.aws_s3_bucket.quest_bucket.id

  queue {
    queue_arn     = aws_sqs_queue.analytics_queue.arn
    events        = ["s3:ObjectCreated:*"]
    filter_prefix = "raw/census_bureau/"
    filter_suffix = ".json"
  }
}