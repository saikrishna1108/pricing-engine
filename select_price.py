import json
import os
import uuid
import time
import boto3
from decimal import Decimal
import random

# Read table names from environment variables
ARMS_TABLE = os.environ['DYNAMO_TABLE_ARMS']
LOG_TABLE = os.environ['DYNAMO_TABLE_LOG']

dynamo = boto3.resource('dynamodb')
arms_table = dynamo.Table(ARMS_TABLE)
log_table = dynamo.Table(LOG_TABLE)

EPSILON = 0.1  # 10% chance to explore a random arm

def app(event, context):
    """
    Handler for GET /getPrice?productId=<id>
    Selects a price-arm using ε-greedy, logs the impression, and returns {price, armId, requestId}.
    """
    # 1) Read productId from query string
    params = event.get('queryStringParameters') or {}
    product_id = params.get('productId')
    if not product_id:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing productId parameter.'})
        }

    # 2) Fetch the current arms data from DynamoDB
    resp = arms_table.get_item(Key={'productId': product_id})
    item = resp.get('Item')
    if not item:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': f'Product {product_id} not found.'})
        }

    arms = item['arms']  # list of { armId, price, impressions, rewards }

    # 3) Compute conversion rate for each arm (rewards/impressions)
    rates = []
    for a in arms:
        imp = int(a['impressions'])
        rew = int(a['rewards'])
        rate = rew / imp  # impressions seeded at 1, so no div-by-zero
        rates.append(rate)

    # 4) With probability EPSILON, pick a random arm; otherwise pick highest-rate arm
    if random.random() < EPSILON:
        choice_index = random.randrange(len(arms))
    else:
        choice_index = rates.index(max(rates))

    chosen_arm = arms[choice_index]
    chosen_price = float(chosen_arm['price'])
    arm_id = chosen_arm['armId']

    # 5) Generate a unique requestId and log the impression
    request_id = str(uuid.uuid4())
    log_table.put_item(Item={
        'requestId': request_id,
        'productId': product_id,
        'armId': arm_id,
        'timestamp': Decimal(str(time.time()))
    })

    # 6) Return JSON with price, armId, requestId
    response_body = {
        'price': chosen_price,
        'armId': arm_id,
        'requestId': request_id
    }
    return {
        'statusCode': 200,
        'headers': { 'Content-Type': 'application/json' },
        'body': json.dumps(response_body)
    }
