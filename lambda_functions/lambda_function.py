import boto3
import logging
import os
import json
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
ec2_client = boto3.client('ec2', region_name=os.environ['AWS_REGION_NAME'])
sns_client = boto3.client('sns', region_name=os.environ['AWS_REGION_NAME'])

# Environment variables
INSTANCE_ID = os.environ['EC2_INSTANCE_ID']
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']


def lambda_handler(event, context):
    """
    Triggered by Sumo Logic alert when /api/data response time exceeds 3s
    for more than 5 requests within a 10-minute window.

    Actions:
    1. Restart the specified EC2 instance
    2. Log the action
    3. Send an SNS notification
    """
    timestamp = datetime.utcnow().isoformat()

    logger.info(f"[{timestamp}] Auto-remediation triggered by Sumo Logic alert.")
    logger.info(f"Event received: {json.dumps(event)}")

    try:
        # Step 1: Stop the EC2 instance
        logger.info(f"Stopping EC2 instance: {INSTANCE_ID}")
        ec2_client.stop_instances(InstanceIds=[INSTANCE_ID])

        # Wait until the instance is fully stopped
        waiter = ec2_client.get_waiter('instance_stopped')
        waiter.wait(InstanceIds=[INSTANCE_ID])
        logger.info(f"Instance {INSTANCE_ID} is now stopped.")

        # Step 2: Start the EC2 instance
        logger.info(f"Starting EC2 instance: {INSTANCE_ID}")
        ec2_client.start_instances(InstanceIds=[INSTANCE_ID])

        # Wait until the instance is running
        waiter = ec2_client.get_waiter('instance_running')
        waiter.wait(InstanceIds=[INSTANCE_ID])
        logger.info(f"Instance {INSTANCE_ID} is now running.")

        # Step 3: Send SNS notification
        message = (
            f"[AUTO-REMEDIATION] [{timestamp}]\n"
            f"Sumo Logic alert detected: /api/data response time exceeded 3s "
            f"for more than 5 requests in a 10-minute window.\n"
            f"Action taken: EC2 instance {INSTANCE_ID} has been restarted automatically.\n"
            f"Please verify application health and investigate root cause."
        )

        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="[ALERT] Auto-Remediation: EC2 Instance Restarted",
            Message=message
        )

        logger.info("SNS notification sent successfully.")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"Instance {INSTANCE_ID} restarted successfully.",
                "timestamp": timestamp
            })
        }

    except ec2_client.exceptions.ClientError as ec2_error:
        logger.error(f"EC2 error: {ec2_error}")
        raise

    except sns_client.exceptions.ClientError as sns_error:
        logger.error(f"SNS error: {sns_error}")
        raise

    except Exception as e:
        logger.error(f"Unexpected error during auto-remediation: {e}")
        raise