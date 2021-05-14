"""
Experiment 3 - data analysis with Streamlit library
"""

import datetime
import re

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.figure_factory as ff


def convert_to_datetime(timestamp_string):
    """ Returns datetime.datetime object, and adjusts for formatting abnormality.
    BCFW P1 uses 24-hour clock with hours 1-24; Python datetime expects hours 0-23.
    '2020040124' from BCFW P1 is actually 2020-04-02 00:00 """
    try:
        return datetime.datetime.strptime(timestamp_string, '%Y%m%d%H')
    except ValueError:
        if timestamp_string[-2:] == '24':
            date_string = timestamp_string[:-2]
            date = datetime.datetime.strptime(date_string, '%Y%m%d')
            # add one more day, since 24:00 of one day is actually 00:00 of next day
            date = date + datetime.timedelta(days=1)
            date = date.replace(hour=0)
            return date
        else:
            raise Exception
    except:
        raise Exception


st.write("""
# Peak Burniness 2.0
""")

stations_dropdown_list = []
stations_json = pd.read_json('../data/weather_stations.json')
for row in stations_json.weather_stations:
    stations_dropdown_list.append('{} ({})'.format(row['name'], row['code']))

selected_station = st.selectbox('Select weather station:', stations_dropdown_list)
selected_code = re.search(r'\(\d*\)', selected_station).group(0).strip('()')
station_filename = '../data/peakValues/'+selected_code+'.json'

st.subheader("Peak burning values for {}".format(selected_station))

station_peak_json = pd.read_json(station_filename)

st.table(data=station_peak_json)

# Chart Fire Indices for station by year

st.subheader('Fire Indices by Year')
years = list(range(2011, 2021))

selected_year = st.selectbox('Select year:', years)

fires_df = pd.read_csv('../../sourceData/hist_fires_stations.csv')

fires_df['IGNITION_DATE'] = pd.to_datetime(fires_df['IGNITION_DATE'], format='%Y%m%d%H%M%S', errors='coerce')

fires_df = fires_df[fires_df['NEAREST_STATION'] == int(selected_code)]

fires_df = fires_df[(pd.Timestamp(selected_year, 4, 1) <= fires_df['IGNITION_DATE']) & (
    fires_df['IGNITION_DATE'] <= pd.Timestamp(selected_year, 9, 30))]
fires_df.reset_index(drop=True, inplace=True)
fires_df['CURRENT_SIZE'].fillna(value=0, inplace=True)
st.dataframe(fires_df)

fig = px.scatter(fires_df, x="IGNITION_DATE", y="STATION_DISTANCE", color="FIRE_CAUSE",
                 size=fires_df["CURRENT_SIZE"], hover_data=['LATITUDE', 'LONGITUDE', 'FIRE_NUMBER'])
st.plotly_chart(fig, use_container_width=True)


hourlies_filename = '../../sourceData/hourlies/'+str(selected_year)+'/'+selected_code+'.csv'

# load hourlies_filename into dataframe - only interested in certain columns, so only load those
station_hourlies_df = pd.read_csv(hourlies_filename, usecols=[
                                  'display_name', 'weather_date', 'ffmc', 'isi', 'fwi'])
station_hourlies_df['weather_date'] = station_hourlies_df['weather_date'].apply(
    lambda row: convert_to_datetime(str(row)))

ffmc_df = station_hourlies_df[['weather_date', 'ffmc']].copy()
ffmc_df.set_index('weather_date', inplace=True)
isi_df = station_hourlies_df[['weather_date', 'isi']].copy()
isi_df.set_index('weather_date', inplace=True)
fwi_df = station_hourlies_df[['weather_date', 'fwi']].copy()
fwi_df.set_index('weather_date', inplace=True)

st.write(selected_station, """ Hourly FFMC for fire season """, str(selected_year))
st.line_chart(ffmc_df)

st.write(selected_station, """ Hourly ISI for fire season """, str(selected_year))
st.line_chart(isi_df)

st.write(selected_station, """ Hourly FWI for fire season """, str(selected_year))
st.line_chart(fwi_df)
