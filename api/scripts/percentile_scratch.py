from pathlib import Path
from typing import Generator
import pandas as pd

base_path = Path(R'/Users/breedwar/Downloads/BCWS_datamart_historical_wx_obs')

# # station_csv_list = base_path.rglob('*STATIONS.csv')



def load_all_csv_to_dataframe(all_csv: Generator, filter_dailies:bool = False) -> pd.DataFrame:
    dfs = []

    for csv in all_csv:
        df = pd.read_csv(csv)

        if filter_dailies:
            # DATE_TIME is provided in PST (GMT-8) and does not recognize DST. 
            # Daily records will therefor always show up as “YYYYMMDD12”
            df = df[df['DATE_TIME'].astype(str).str.endswith('12')]
        dfs.append(df)

    all_dailies_df = pd.concat(dfs, ignore_index=True)

    return all_dailies_df

def main():
    wx_csv_list = base_path.rglob('2023/*.csv')
    df = load_all_csv_to_dataframe(wx_csv_list)
    df.to_csv(base_path / '2023' / '2023_BCWS_WX_OBS.csv', index=False)

if __name__=='__main__':
    main()



# import requests
# import csv

# # Function to get data from API
# def get_api_data(url):
#     response = requests.get(url)
#     if response.status_code == 200:
#         return response.json()
#     else:
#         return None

# # API endpoint
# api_url = "https://bcwsapi.nrs.gov.bc.ca/wfwx-datamart-api/v1/stations?orderBy=stationName&from=2023070100&to=2023073100"

# # List to store all station data
# all_stations = []

# # Initial request
# data = get_api_data(api_url)

# # Continue fetching data while there are more pages
# while data:
#     # Extract relevant information from the response
#     stations = data["collection"]
    
#     # Append station data to the list
#     all_stations.extend(stations)
    
#     # Check for the next page
#     links = data['links']
#     next_page = next((item['href'] for item in links if item['rel'] == 'next'), None)
    
#     # Fetch the next page if it exists
#     if next_page:
#         data = get_api_data(next_page)
#     else:
#         data = None

# # Specify the CSV file name
# csv_file = R"/Users/breedwar/Downloads/BCWS_datamart_historical_wx_obs/2023/2023_BCWS_WX_STATIONS.csv"

# # Write the information to a CSV file
# with open(csv_file, mode='w', newline='') as file:
#     writer = csv.writer(file)

#     # Write the header
#     writer.writerow(["STATION_CODE", "STATION_NAME", "LATITUDE", "LONGITUDE"])

#     # Write each station's information
#     for station in all_stations:
#         writer.writerow([
#             station["stationCode"],
#             station["stationName"],
#             station["latitude"],
#             station["longitude"]
#         ])

# print(f"Data has been exported to {csv_file}")
