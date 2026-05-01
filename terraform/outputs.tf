output "ec2_instance_id" {
  description = "ID of the EC2 instance managed by auto-remediation"
  value       = aws_instance.web_server.id
}

output "ec2_public_ip" {
  description = "Public IP of the EC2 instance"
  value       = aws_instance.web_server.public_ip
}

output "sns_topic_arn" {
  description = "ARN of the SNS alerts topic"
  value       = aws_sns_topic.alerts.arn
}

output "lambda_function_name" {
  description = "Name of the auto-remediation Lambda function"
  value       = aws_lambda_function.auto_remediation.function_name
}

output "lambda_function_url" {
  description = "Use this URL in the Sumo Logic webhook connection"
  value       = aws_lambda_function_url.auto_remediation_url.function_url
}
