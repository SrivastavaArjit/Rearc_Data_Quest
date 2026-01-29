import requests
import boto3
import json

# --- Configuration ---
API_URL = "https://api.datausa.io/tesseract/data.jsonrecords"
BUCKET_NAME = "data-quest-bucket-rearc"
S3_KEY = "raw/census_bureau/population_data.json"

QUERY_PARAMS = {
    "cube": "acs_yg_total_population_1",
    "drilldowns": "Year,Nation",
    "locale": "en",
    "measures": "Population"
}

s3 = boto3.client('s3')

def fetch_and_store_api_data():
    print(f"Fetching data from DataUSA API...")
    
    try:
        response = requests.get(API_URL, params=QUERY_PARAMS)
        response.raise_for_status()  # If the request fails immediately raise an error with error code
        
        data = response.json()
        json_data = json.dumps(data, indent=4).encode('utf-8')

        # 4. Upload directly to S3
        print(f"Uploading API results to s3://{BUCKET_NAME}/{S3_KEY}")
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=S3_KEY,
            Body=json_data,
            ContentType='application/json'
        )
        
        print("API data is safely stored in S3.")

    except Exception as e:
        print(f"Error during API ingestion: {e}")

if __name__ == "__main__":
    fetch_and_store_api_data()