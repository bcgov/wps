import pandas as pd
from app.utils.s3 import get_client
from app import config

async def get_csv_list_from_s3(year: int):
    s3_csv_list = []
    async with get_client() as (client, bucket):
        response = await client.list_objects_v2(Bucket=bucket, Prefix=f'data_dumps/BCWS_datamart/{year}/BCWS_datamart_historical_wx_obs')

        for obj in response['Contents']:
            file_key = obj['Key']

            if file_key.endswith('.csv'):
                s3_csv_list.append(file_key)
        return s3_csv_list

def filter_wx_and_station_csv(csv_list: list):
    wx_obs_csv_list = [csv for csv in csv_list if 'OBS.csv' in csv]
    station_csv_list = [csv for csv in csv_list if 'STATIONS.csv' in csv]

    return wx_obs_csv_list, station_csv_list

def read_s3_csv_to_pandas(s3_key: str):
    server = config.get('OBJECT_STORE_SERVER')
    bucket = config.get('OBJECT_STORE_BUCKET')

    url = f'https://{server}/{bucket}/{s3_key}'
    df = pd.read_csv(url)
    
    return df

def load_all_csv_to_dataframe(csv_list: list, filter_dailies: bool = False) -> pd.DataFrame:
    dfs = []

    for csv in csv_list:

        df = read_s3_csv_to_pandas(csv)
 
        if filter_dailies:
            # DATE_TIME is provided in PST (GMT-8) and does not recognize DST. 
            # Daily records will therefor always show up as “YYYYMMDD12”
            df = df[df['DATE_TIME'].astype(str).str.endswith('12')]
        dfs.append(df)

    all_dailies_df = pd.concat(dfs, ignore_index=True)

    return all_dailies_df