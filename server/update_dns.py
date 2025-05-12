import boto3
import requests
import json
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Update Route 53 DNS record with current EC2 IP."""
    try:
        # Get current public IP
        response = requests.get('https://api.ipify.org?format=json')
        current_ip = response.json()['ip']
        logger.info(f"Current IP: {current_ip}")

        # Initialize Route 53 client
        route53 = boto3.client('route53')

        # Get the hosted zone ID (you'll need to replace this with your actual hosted zone ID)
        hosted_zone_id = 'YOUR_HOSTED_ZONE_ID'  # We'll get this in the next step

        # Update the A record
        response = route53.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': 'quintilian.finora.live',
                            'Type': 'A',
                            'TTL': 300,
                            'ResourceRecords': [
                                {
                                    'Value': current_ip
                                }
                            ]
                        }
                    }
                ]
            }
        )

        logger.info(f"DNS update response: {json.dumps(response)}")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'DNS record updated successfully',
                'ip': current_ip
            })
        }

    except Exception as e:
        logger.error(f"Error updating DNS: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        } 