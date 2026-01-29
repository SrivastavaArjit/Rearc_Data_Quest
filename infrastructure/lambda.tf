# Zip the source code
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../src"
  output_path = "${path.module}/../build/payload.zip"
}

data "aws_iam_role" "lambda_role" {
  name = "react-quest-role"
}

# =====================================================
# INGESTION LAMBDA (Runs in Mumbai)
# =====================================================
resource "aws_lambda_function" "ingestion_lambda" {
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  function_name    = "rearc-ingestion"
  role             = data.aws_iam_role.lambda_role.arn
  handler          = "lambda_handlers.ingestion_handler.ingestion_handler"
  runtime          = "python3.12"
  timeout          = 300
  
  environment {
    variables = { S3_BUCKET_NAME = data.aws_s3_bucket.quest_bucket.id }
  }

  layers = ["arn:aws:lambda:ap-south-1:336392948345:layer:AWSSDKPandas-Python312:1"]
}

resource "aws_cloudwatch_event_rule" "daily" {
  schedule_expression = "rate(1 day)"
}

resource "aws_cloudwatch_event_target" "ingestion_target" {
  rule = aws_cloudwatch_event_rule.daily.name
  arn  = aws_lambda_function.ingestion_lambda.arn
}

# =====================================================
# ANALYTICS LAMBDA (Runs in Stockholm)
# =====================================================
resource "aws_lambda_function" "analytics_lambda" {
  provider         = aws.bucket_region
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  function_name    = "rearc-analytics"
  role             = data.aws_iam_role.lambda_role.arn
  handler          = "lambda_handlers.analytics_handler.analytics_handler"
  runtime          = "python3.12"
  timeout          = 300

  # Use the STOCKHOLM (eu-north-1) Pandas Layer ARN
  layers = ["arn:aws:lambda:eu-north-1:336392948345:layer:AWSSDKPandas-Python312:1"]
}

# Connect SQS to Lambda
resource "aws_lambda_event_source_mapping" "sqs_to_lambda" {
  provider         = aws.bucket_region
  event_source_arn = aws_sqs_queue.analytics_queue.arn
  function_name    = aws_lambda_function.analytics_lambda.arn
  batch_size       = 1
}

# Allow Analytics Lambda to read from SQS
resource "aws_iam_role_policy" "lambda_sqs_policy" {
  name = "lambda-sqs-read-policy"
  role = data.aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Effect   = "Allow"
        Resource = aws_sqs_queue.analytics_queue.arn
      }
    ]
  })
}