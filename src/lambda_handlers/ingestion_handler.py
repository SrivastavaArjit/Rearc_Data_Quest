import json
from ingestion.ingest_bls import sync_bls_data  # Refactor your script to be a function
from ingestion.ingest_api_data import sync_api_data

def ingestion_handler(event, context):
    print("Starting Ingestion Pipeline...")
    
    # 1. Sync BLS Data
    try:
        sync_bls_data()
        print("BLS Data Sync Successful")
    except Exception as e:
        print(f"Error syncing BLS: {e}")
        
    # 2. Sync API Data
    try:
        sync_api_data()
        print("API Data Sync Successful")
    except Exception as e:
        print(f"Error syncing API: {e}")

    return {
        'statusCode': 200,
        'body': json.dumps('Ingestion Complete')
    }