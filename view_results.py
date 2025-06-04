import boto3
import pandas as pd

# Make sure your AWS CLI is configured, or
# set AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY env vars.

# 1) Connect to DynamoDB and fetch the "widget-A" item
dynamo = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamo.Table('PricingArms')

resp = table.get_item(Key={'productId': 'widget-A'})
item = resp.get('Item')
if not item:
    print("No item found for productId=widget-A")
    exit(1)

# 2) Build a DataFrame from the 'arms' list
arms = item['arms']
df = pd.DataFrame(arms)

# Convert Decimal → float so pandas can handle it
df['price'] = df['price'].astype(float)
df['impressions'] = df['impressions'].astype(int)
df['rewards'] = df['rewards'].astype(int)
df['conversion_rate'] = df['rewards'] / df['impressions']

# 3) Display the table in console
print(df[['armId', 'price', 'impressions', 'rewards', 'conversion_rate']])
# 3) Save the DataFrame to a CSV file
csv_filename = 'pricing_arms_widget_A.csv'
df.to_csv(csv_filename, index=False)
print(f"DataFrame saved to {csv_filename}")