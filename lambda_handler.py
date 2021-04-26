import json
import boto3
import os
import logging
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)
client = boto3.client('ecs')
slack_webhook = os.environ['SLACK_WEBHOOK']

def get_desired_capacity(cluster, service):
    try:
        response = client.describe_services(
            cluster=cluster,
            services=[
                service,
            ]
        )
    except ClientError as e:
        logger.error(e.response['Error']['Code'])
        logger.error(e.response['Error']['Message'])
        raise e
    desired_capacity = response['services'][0]['desiredCount']
    running_capacity = response['services'][0]['desiredCount']
    return desired_capacity - running_capacity
    
def update_desired_capacity(cluster, bkup_service, bkup_expected_desired_capacity):
    response = client.update_service(
        cluster=cluster,
        service=bkup_service,
        desiredCount=bkup_expected_desired_capacity
    )
    return 0

def put_message_to_slack():
    response = requests.post(
        slack_webhook
    )
    #レスポンスオブジェクトのjsonメソッドを使うと、
    #JSONデータをPythonの辞書オブジェクトを変換して取得できる。
    logger.info(response)

def lambda_handler(event, context):
    logger.info(event)
    cluster      = os.environ['ECS_CLUSTER']
    base_service = os.environ['ECS_SERVICE_BASE']
    bkup_service = os.environ['ECS_SERVICE_BACKUP']

    base_service_shortage_capacity = get_desired_capacity(cluster, base_service)
    bkup_service_desired_capacity = get_desired_capacity(cluster, bkup_service)

    # base_service_desired_capacity = 1
    expected_bkup_desired_capacity = base_service_shortage_capacity + bkup_service_desired_capacity
    if expected_bkup_desired_capacity > 0 : 
        update_desired_capacity(cluster, bkup_service, expected_bkup_desired_capacity)
    else :
        logger.info('expected_bkup_desired_capacity is 0, desired_capacity is filled.')
        
    put_message_to_slack()
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

