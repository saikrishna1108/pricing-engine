import json
import os
import boto3

# Read table names from environment variables
ARMS_TABLE = os.environ['DYNAMO_TABLE_ARMS']
LOG_TABLE = os.environ['DYNAMO_TABLE_LOG']

dynamo = boto3.resource('dynamodb')
arms_table = dynamo.Table(ARMS_TABLE)
log_table = dynamo.Table(LOG_TABLE)

def app(event, context):
    """
    Handler for POST /reportOutcome
    Body JSON: { "requestId": "<uuid>", "bought": true/false }
    Updates impressions/rewards in PricingArms and deletes the log entry.
    """
    try:
        data = json.loads(event.get('body') or '{}')
        request_id = data['requestId']
        bought = data.get('bought', False)
    except (KeyError, json.JSONDecodeError):
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid JSON or missing requestId.'})
        }

    # 1) Look up the impression log item to get productId and armId
    resp = log_table.get_item(Key={'requestId': request_id})
    log_item = resp.get('Item')
    if not log_item:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': f'No log found for requestId {request_id}.'})
        }

    product_id = log_item['productId']
    arm_id = log_item['armId']

    # 2) Fetch the PricingArms row for that product
    resp = arms_table.get_item(Key={'productId': product_id})
    item = resp.get('Item')
    if not item:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': f'Product {product_id} not found.'})
        }
    arms = item['arms']

    # 3) Find the index of the matching arm in the list
    idx = next((i for i, a in enumerate(arms) if a['armId'] == arm_id), None)
    if idx is None:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Arm {arm_id} not found for product {product_id}.'})
        }

    # 4) Build update expression: increment impressions always; if bought, increment rewards too
    update_expr = f"SET arms[{idx}].impressions = arms[{idx}].impressions + :inc"
    expr_values = {':inc': 1}
    if bought:
        update_expr += f", arms[{idx}].rewards = arms[{idx}].rewards + :inc"

    # 5) Update the PricingArms table
    arms_table.update_item(
        Key={'productId': product_id},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=expr_values
    )

    # 6) Delete the log entry so the table doesn’t grow indefinitely
    log_table.delete_item(Key={'requestId': request_id})

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Outcome recorded.'})
    }
