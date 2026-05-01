variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "notification_email" {
  description = "Email address for SNS alert notifications"
  type        = string
}

variable "project_name" {
  description = "Project name used for resource naming and tagging"
  type        = string
  default     = "auto-remediation"
}
