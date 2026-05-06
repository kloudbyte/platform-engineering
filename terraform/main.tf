terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.5.0"
}

provider "aws" {
  region = var.aws_region
}

# ─────────────────────────────────────────
# EC2 Instance
# ─────────────────────────────────────────
# Fetch latest Amazon Linux 2 AMI automatically
data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
  filter {
    name   = "state"
    values = ["available"]
  }
}

resource "aws_instance" "web_server" {
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = var.instance_type

  user_data = <<-EOF
    #!/bin/bash
    yum update -y
    yum install -y httpd
    systemctl start httpd
    systemctl enable httpd
    echo "<h1>Auto-Remediation Demo Server</h1>" > /var/www/html/index.html
  EOF

  tags = {
    Name    = "${var.project_name}-web-server"
    Project = var.project_name
  }
}

# ─────────────────────────────────────────
# SNS Topic and Email Subscription
# ─────────────────────────────────────────
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-alerts"

  tags = {
    Name    = "${var.project_name}-alerts"
    Project = var.project_name
  }
}

resource "aws_sns_topic_subscription" "email_alert" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.notification_email
}

# ─────────────────────────────────────────
# Lambda Function
# ─────────────────────────────────────────

# Package the Lambda function code into a ZIP
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda_functions/lambda_function.py"
  output_path = "${path.module}/lambda_function.zip"
}

resource "aws_lambda_function" "auto_remediation" {
  function_name    = "${var.project_name}-restart"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.11"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  timeout          = 300  # 5 minutes for EC2 stop/start cycle

  environment {
    variables = {
      EC2_INSTANCE_ID  = aws_instance.web_server.id
      SNS_TOPIC_ARN    = aws_sns_topic.alerts.arn
      AWS_REGION_NAME  = var.aws_region
    }
  }

  tags = {
    Name    = "${var.project_name}-lambda"
    Project = var.project_name
  }
}
  resource "aws_lambda_function_url" "auto_remediation_url" {
  function_name      = aws_lambda_function.auto_remediation.function_name
  authorization_type = "NONE"

  cors {
    allow_credentials = false
    allow_origins     = ["*"]
    allow_methods     = ["POST"]
    allow_headers     = ["Content-Type"]
    max_age           = 86400
  }
}

resource "aws_lambda_permission" "allow_public_function_url" {
  statement_id           = "AllowPublicFunctionURL"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.auto_remediation.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}
