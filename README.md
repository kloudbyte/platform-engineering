# platform-engineering
Monitoring and automation solutions for intermittent web application performance issue
# Monitoring and Auto-Remediation Solution

A Platform Engineering solution that automatically detects and resolves
web application performance degradation using Sumo Logic, AWS Lambda, and Terraform.

## Architecture

Sumo Logic detects slow API responses → Alert triggers Lambda →
Lambda restarts EC2 instance → SNS notifies the team

## Repository Structure

- `sumo_logic_query.txt` — Sumo Logic query for detecting slow /api/data responses
- `lambda_function/` — Python Lambda function for auto-remediation
- `terraform/` — Terraform IaC for EC2, Lambda, SNS, and IAM resources

## Prerequisites

- AWS CLI configured with appropriate permissions
- Terraform >= 1.5.0
- Sumo Logic account with log ingestion configured

## Deployment

cd terraform
terraform init
terraform apply -var="notification_email=your@email.com"

## Testing

Run a manual Lambda test via the AWS Console using the sample payload in the docs.
