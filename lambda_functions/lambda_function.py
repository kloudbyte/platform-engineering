import boto3
import logging
import os
import json
import threading
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def restart_instance(instance_id, sns_arn, region):
    """Runs in background thread — after immediate 200 response to Sumo Logic"""
    ec2 = boto3.client('ec2', region_name=region)
    sns = boto3.client('sns', region_name=region)
    timestamp = datetime.utcnow().isoformat()

    try:
        # Step 1: Stop the EC2 instance
        logger.info(f"Stopping instance {instance_id}")
        ec2.stop_instances(InstanceIds=[instance_id])

        # Wait until the instance is fully stopped
        waiter = ec2.get_waiter('instance_stopped')
        waiter.wait(
            InstanceIds=[instance_id],
            WaiterConfig={'Delay': 15, 'MaxAttempts': 20}
        )
        # Step 2: Start the EC2 instance
        logger.info("Instance stopped. Starting now...")

        ec2.start_instances(InstanceIds=[instance_id])
        # Wait until the instance is running
        waiter = ec2.get_waiter('instance_running')
        waiter.wait(
            InstanceIds=[instance_id],
            WaiterConfig={'Delay': 15, 'MaxAttempts': 20}
        )
        logger.info("Instance running.")

        # Step 3: Send SNS notification
        sns.publish(
            TopicArn=sns_arn,
            Subject="[ALERT] Auto-Remediation: EC2 Restarted",
            Message=(
                f"[AUTO-REMEDIATION] {timestamp}\n"
                f"EC2 instance {instance_id} was automatically restarted.\n"
                f"Trigger: Sumo Logic slow-api-response-alert\n"
                f"Endpoint: /api/data exceeded 3s response time threshold."
            )
        )
        logger.info("SNS notification sent successfully.")

    except Exception as e:
        logger.error(f"Background restart failed: {str(e)}")


def lambda_handler(event, context):
    timestamp = datetime.utcnow().isoformat()
    logger.info(f"Triggered at {timestamp} | Event: {json.dumps(event)}")

    region      = os.environ.get('AWS_REGION_NAME', 'us-east-1')
    instance_id = os.environ.get('EC2_INSTANCE_ID')
    sns_arn     = os.environ.get('SNS_TOPIC_ARN')

    if not instance_id or not sns_arn:
        logger.error("Missing environment variables")
        return {"statusCode": 500, "body": "Missing environment variables"}

    # Start EC2 restart in background thread
    thread = threading.Thread(
        target=restart_instance,
        args=(instance_id, sns_arn, region)
    )
    thread.start()

    # Return 200 immediately so Sumo Logic doesn't time out
    logger.info("Acknowledged Sumo Logic alert. EC2 restart initiated in background.")
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Auto-remediation initiated",
            "instance": instance_id,
            "timestamp": timestamp
        })
    }
