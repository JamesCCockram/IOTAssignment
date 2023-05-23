import boto3

dynamodb = boto3.resource('dynamodb')
table_name = 'alarm_table'  # Specify your DynamoDB table name
table = dynamodb.Table(table_name)

try:
    response = table.scan()
    items = response['Items']
except Exception as e:
    return f"Error occurred: {str(e)}"


import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.client('dynamodb')

table_name = 'alarm_table'
key_attribute_name = 'YourKeyAttributeName'
key_attribute_value = 'YourKeyAttributeValue'

response = dynamodb.query(
    TableName=table_name,
    KeyConditionExpression=f"{key_attribute_name} = :val",
    ExpressionAttributeValues={":val": {"S": key_attribute_value}}
)

items = response.get('Items', [])

array1 = []
array2 = []

for item in items:
    attribute_value1 = item.get('attribute_name1')
    attribute_value2 = item.get('attribute_name2')
    array1.append(attribute_value1)
    array2.append(attribute_value2)

print(array1)
print(array2)
