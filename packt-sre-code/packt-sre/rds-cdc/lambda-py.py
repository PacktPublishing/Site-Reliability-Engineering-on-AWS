from __future__ import print_function
import boto3
import base64
from json import loads

dynamodb_client = boto3.client('dynamodb')

# The block below creates the DDB table with the specified column names.
table_name = "data_change"
row_id = "id"
row_timestamp = "time"
try:
    response = dynamodb_client.create_table(
        AttributeDefinitions=[
            {
                'AttributeName': row_id,
                'AttributeType': 'S',
            },
            {
                'AttributeName': row_timestamp,
                'AttributeType': 'S',
            }
        ],
        KeySchema=[
            {
                'AttributeName': row_id,
                'KeyType': 'HASH',
            },
            {
                'AttributeName': row_timestamp,
                'KeyType': 'RANGE',
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 1,
            'WriteCapacityUnits': 1,
        },
        TableName=table_name
    )
except dynamodb_client.exceptions.ResourceInUseException:
    # Table is created, skip
    pass


def lambda_handler(event, context):
    payload = event['Records']
    output = []
    success = 0
    failure = 0
    for record in payload:
        
        try:
            payload = base64.b64decode(record['kinesis']['data'])
        except Exception as e:
            failure += 1
            output.append({'recordId': record['eventID'], 'result': 'DeliveryFailed'})
            print(str(e))
        else:
            data_item = loads(payload)
            print("data:{}".format(data_item))
            if data_item['data'][0] == "table":
                ddb_item = { row_id: { 'S': data_item[row_id] },
                    "resource" : { 'S': str(data_item['data'][0]) },
                    "resource_name" : { 'S': str(data_item['data'][1]) },
                    "action" : { 'S': str(data_item['data'][2]) },
                    "detail" : { 'S': ", ".join(data_item['data'][3:-1]) },
                    row_timestamp: { 'S': data_item[row_timestamp] }
                }
            else:
                ddb_item = None
            if ddb_item is not None:
                try:
                    dynamodb_client.put_item(TableName=table_name, Item=ddb_item)
                except Exception as e:
                    print("error storing message {}".format(str(e)))
                    failure += 1
                else:
                    success += 1
                    output.append({'recordId': record['eventID'], 'result': 'Ok'})
            else:    
                print("cognito message not stored")            

    print('Successfully delivered {0} records, failed to deliver {1} records'.format(success, failure))
    return {'records': output}