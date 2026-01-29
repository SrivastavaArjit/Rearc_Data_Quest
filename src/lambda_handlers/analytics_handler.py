import json
import boto3
import pandas as pd
from analytics.data_analytics import run_analytics_report

def analytics_handler(event, context):

    # SQS events can contain multiple records
    for record in event['Records']:
        # The S3 event is hidden inside the SQS body
        body = json.loads(record['body'])
        
        # Check if it's an S3 event
        if 'Records' in body:
            s3_record = body['Records'][0]
            bucket = s3_record['s3']['bucket']['name']
            key = s3_record['s3']['object']['key']

            print("key: ", key)
            print("bucket: ", bucket)
            print("s3_record: ", s3_record)
            
            print(f"Triggered by file: {key} in bucket: {bucket}")
            
            if key.endswith('.json'):
                try:
                    run_analytics_report()
                    print("Analysis Successfull...")
                except Exception as e:
                    print(f"Analysis Failed: {str(e)}")
                    raise e
            else:
                print(f"⏭️ Skipping non-JSON file: {key}")
            
    return {'statusCode': 200}