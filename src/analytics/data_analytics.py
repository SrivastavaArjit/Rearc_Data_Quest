# imports 
import pandas as pd
import numpy as np
import json
import boto3
from io import StringIO

s3 = boto3.client('s3')
BUCKET_NAME = 'data-quest-bucket-rearc'
S3_PREFIX = "raw/bls/"

def run_analytics_report():
    s3 = boto3.client('s3')
    bucket = 'data-quest-bucket-rearc'
    bls_key = 'raw/bls/pr.data.0.Current'
    api_data_key = 'raw/census_bureau/population_data.json'

    # Fetch the object from S3
    bls_response = s3.get_object(Bucket=bucket, Key=bls_key)
    api_data_response = s3.get_object(Bucket=bucket, Key=api_data_key)
    # Read the content as a string
    bls_data = bls_response['Body'].read().decode('utf-8')
    api_data = api_data_response['Body'].read().decode('utf-8')

    bls_dtypes = {
        'series_id': str,
        'year': int,
        'period': str,
        'value': float,
        'footnote_codes': str
    }

    # Load into Pandas
    df_bls = pd.read_csv(StringIO(bls_data), sep='\t',dtype=bls_dtypes)
    df_api = pd.DataFrame(json.loads(api_data)['data'])

    print(f"The schema of the bls dataframe is: {df_bls.dtypes}")
    print(df_bls.head(10))

    print(f"The schema of the census bureau api dataframe is: {df_bls.dtypes}")
    print(df_api.head(10))

    # CLEANING: Trim column names and string values
    df_bls.columns = df_bls.columns.str.strip()

    # Strip whitespace from all string columns at once
    df_bls = df_bls.apply(lambda x: x.str.strip() if isinstance(x, str) else x)

    # errors='coerce' turns non-numeric junk (like empty strings or text) into NaN
    df_bls['value'] = pd.to_numeric(df_bls['value'], errors='coerce')

    # 2. Fill all NaNs (including those created above) with 0
    df_bls['value'] = df_bls['value'].fillna(0)

    # 3. (Optional) Convert to a specific type if needed, like float
    df_bls['value'] = df_bls['value'].astype(float)

    # Population statistics for 2013 - 2018 inclusive
    # To Calculate the mean and standard deviation of the US population.

    mask = (df_api['Year'] >= 2013) & (df_api['Year'] <= 2018)
    pop_subset = df_api.loc[mask, 'Population']

    mean_pop = pop_subset.mean()
    std_pop = pop_subset.std()

    print(f"Mean Population [2013-2018]: {mean_pop:,.2f}")
    print(f"Standard Deviation: {std_pop:,.2f}")

    # Best Year per Series
    # Find the year with the highest total value for each series_id.

    df_yearly = df_bls.groupby(['series_id', 'year'])['value'].sum().reset_index()

    df_best_years = df_yearly.sort_values('value', ascending=False) \
                            .drop_duplicates('series_id') \
                            .sort_values('series_id')

    print("Best Year per Series (Sample):")
    print(df_best_years.head())

    # 1. Filter BLS for the target series and period
    df_target_bls = df_bls[(df_bls['series_id'] == 'PRS30006032') & (df_bls['period'] == 'Q01')]

    # 2. Merge (Join) with the Population dataframe
    # We use an 'inner' join on the year columns
    report_df = pd.merge(
        df_target_bls, 
        df_api, 
        left_on='year', 
        right_on='Year', 
        how='inner'
    )

    # 3. Select only the required columns
    final_report = report_df[['series_id', 'year', 'period', 'value', 'Population']]

    print("Final Combined Report:")
    print(final_report.sort_values('year'))
