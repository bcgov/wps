"""
Experiment 3 - data analysis with Streamlit library
"""

import streamlit as st
import pandas as pd
import re

st.write("""
# Peak Burniness 2.0
""")

stations_dropdown_list = []
stations_json = pd.read_json('/Users/awilliam/Desktop/wps/api/app/data/weather_stations.json')
for row in stations_json.weather_stations:
    stations_dropdown_list.append('{} ({})'.format(row['name'], row['code']))

selected_station = st.selectbox('Select weather station:', stations_dropdown_list)
selected_code = re.search(r'\(\d*\)', selected_station).group(0).strip('()')
station_filename = '/Users/awilliam/Desktop/wps/api/app/data/peakValues/'+selected_code+'.json'

st.write("""
## Peak burning values for
""", selected_station)

station_peak_json = pd.read_json(station_filename)

st.table(data=station_peak_json)
