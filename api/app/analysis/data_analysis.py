"""
Experiment 3 - data analysis with Streamlit library
"""

import datetime
import re
import numpy as np

import pandas as pd
import streamlit as st
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go


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

# The code necessary to render 3D histograms in Plotly is ugly because Plot doesn't officially support 3D histograms,
# but a hacky solution has been copied from https://stackoverflow.com/a/60403270 (which includes explanation
# for why we're repeating, inserting, and popping values from lists before graphing)
look_at = st.radio('Examine', ('maximum values', 'minimum values', 'noon values'))
if look_at == 'noon values':
    noon_df = pd.read_csv('../data/minMaxNoonValues/byDay/noon/'+selected_code+'.csv')

    noon_df['weather_date'] = pd.to_datetime(noon_df['weather_date'])

    selected_month = st.selectbox('Select month:', [
                                  'April-Sept', 'April', 'May', 'June', 'July', 'August', 'September'])

    if selected_month == 'April':
        noon_df = noon_df[noon_df['weather_date'].dt.month == 4]
    elif selected_month == 'May':
        noon_df = noon_df[noon_df['weather_date'].dt.month == 5]
    elif selected_month == 'June':
        noon_df = noon_df[noon_df['weather_date'].dt.month == 6]
    elif selected_month == 'July':
        noon_df = noon_df[noon_df['weather_date'].dt.month == 7]
    elif selected_month == 'August':
        noon_df = noon_df[noon_df['weather_date'].dt.month == 8]
    elif selected_month == 'September':
        noon_df = noon_df[noon_df['weather_date'].dt.month == 9]

    if st.checkbox("Show Raw Data for Noon Observed Weather Conditions", False):
        st.subheader('Noon values for {}'.format(selected_station))
        st.dataframe(noon_df)

    # TEMPERATURE
    temperature_fig = go.Figure()

    for year in noon_df['year'].unique():
        years_temps = noon_df[noon_df['year'] == year]
        a0 = np.histogram(years_temps['temperature'], bins='auto', density=False)[0].tolist()
        a0 = np.repeat(a0, 2).tolist()
        a0.insert(0, 0)
        a0.pop()
        a1 = np.histogram(years_temps['temperature'], bins='auto', density=False)[1].tolist()
        a1 = np.repeat(a1, 2)
        temperature_fig.add_traces(go.Scatter3d(x=[year]*len(a0), y=a1, z=a0, mode='lines', name=str(year)))
    temperature_fig.update_layout(scene=dict(yaxis_title='TEMPERATURE (°C)',
                                             xaxis_title='YEAR', zaxis_title='FREQUENCY'))
    temperature_fig.update_layout(title='Observed Noon Temperature in ' +
                                  selected_month + ' - Distribution by Year')

    # RELATIVE HUMIDITY
    rh_fig = go.Figure()

    for year in noon_df['year'].unique():
        year_rh = noon_df[noon_df['year'] == year]
        a0 = np.histogram(year_rh['relative_humidity'], bins='auto', density=False)[0].tolist()
        a0 = np.repeat(a0, 2).tolist()
        a0.insert(0, 0)
        a0.pop()
        a1 = np.histogram(year_rh['relative_humidity'], bins='auto', density=False)[1].tolist()
        a1 = np.repeat(a1, 2)
        rh_fig.add_traces(go.Scatter3d(x=[year]*len(a0), y=a1, z=a0, mode='lines', name=str(year)))
    rh_fig.update_layout(scene=dict(yaxis_title='RELATIVE HUMIDITY (%)',
                         xaxis_title='YEAR', zaxis_title='FREQUENCY'))
    rh_fig.update_layout(title='Observed Noon RH in ' + selected_month + ' - Distribution by Year')

    # WIND SPEED
    wind_fig = go.Figure()

    for year in noon_df['year'].unique():
        year_wind = noon_df[noon_df['year'] == year]
        a0 = np.histogram(year_wind['wind_speed'], bins='auto', density=False)[0].tolist()
        a0 = np.repeat(a0, 2).tolist()
        a0.insert(0, 0)
        a0.pop()
        a1 = np.histogram(year_wind['wind_speed'], bins='auto', density=False)[1].tolist()
        a1 = np.repeat(a1, 2)
        wind_fig.add_traces(go.Scatter3d(x=[year]*len(a0), y=a1, z=a0, mode='lines', name=str(year)))
    wind_fig.update_layout(scene=dict(yaxis_title='WIND SPEED (km/h)',
                           xaxis_title='YEAR', zaxis_title='FREQUENCY'))
    wind_fig.update_layout(title='Observed Noon Wind Speed in ' + selected_month + ' - Distribution by Year')

    # FFMC
    ffmc_fig = go.Figure()

    for year in noon_df['year'].unique():
        year_ffmc = noon_df[noon_df['year'] == year]
        a0 = np.histogram(year_ffmc['ffmc'], bins='auto', density=False)[0].tolist()
        a0 = np.repeat(a0, 2).tolist()
        a0.insert(0, 0)
        a0.pop()
        a1 = np.histogram(year_ffmc['ffmc'], bins='auto', density=False)[1].tolist()
        a1 = np.repeat(a1, 2)
        ffmc_fig.add_traces(go.Scatter3d(x=[year]*len(a0), y=a1, z=a0, mode='lines', name=str(year)))
    ffmc_fig.update_layout(scene=dict(yaxis_title='FFMC', xaxis_title='YEAR', zaxis_title='FREQUENCY'))
    ffmc_fig.update_layout(title='Observed Noon FFMC in ' + selected_month + ' - Distribution by Year')

    # FWI
    fwi_fig = go.Figure()

    for year in noon_df['year'].unique():
        year_fwi = noon_df[noon_df['year'] == year]
        a0 = np.histogram(year_fwi['fwi'], bins='auto', density=False)[0].tolist()
        a0 = np.repeat(a0, 2).tolist()
        a0.insert(0, 0)
        a0.pop()
        a1 = np.histogram(year_fwi['fwi'], bins='auto', density=False)[1].tolist()
        a1 = np.repeat(a1, 2)
        fwi_fig.add_traces(go.Scatter3d(x=[year]*len(a0), y=a1, z=a0, mode='lines', name=str(year)))
    fwi_fig.update_layout(scene=dict(yaxis_title='FWI', xaxis_title='YEAR', zaxis_title='FREQUENCY'))
    fwi_fig.update_layout(title='Observed Noon FWI in ' + selected_month + ' - Distribution by Year')

    st.plotly_chart(temperature_fig, use_container_width=True)
    st.plotly_chart(rh_fig, use_container_width=True)
    st.plotly_chart(wind_fig, use_container_width=True)
    st.plotly_chart(ffmc_fig, use_container_width=True)
    st.plotly_chart(fwi_fig, use_container_width=True)
elif look_at == 'maximum values' or 'minimum values':
    min_max_df = pd.read_csv('../data/minMaxNoonValues/byDay/minMax/'+selected_code+'.csv')

    float_columns = ['temperature', 'temperature.1', 'relative_humidity',
                     'relative_humidity.1', 'wind_speed', 'wind_speed.1', 'ffmc', 'ffmc.1', 'fwi', 'fwi.1']
    for col_name in float_columns:
        min_max_df[col_name] = pd.to_numeric(min_max_df[col_name], errors='coerce')
    min_max_df.rename(columns={'Unnamed: 0': 'weather_date', 'temperature': 'min_temp',
                      'temperature.1': 'max_temp', 'relative_humidity': 'min_RH', 'relative_humidity.1': 'max_RH', 'wind_speed': 'min_wind_speed', 'wind_speed.1': 'max_wind_speed', 'ffmc': 'min_ffmc', 'ffmc.1': 'max_ffmc', 'fwi': 'min_fwi', 'fwi.1': 'max_fwi'}, inplace=True)
    min_max_df = min_max_df.iloc[2:, :]
    min_max_df['weather_date'] = pd.to_datetime(min_max_df['weather_date'])

    selected_month = st.selectbox('Select month:', [
                                  'April-Sept', 'April', 'May', 'June', 'July', 'August', 'September'])

    if selected_month == 'April':
        min_max_df = min_max_df[min_max_df['weather_date'].dt.month == 4]
    elif selected_month == 'May':
        min_max_df = min_max_df[min_max_df['weather_date'].dt.month == 5]
    elif selected_month == 'June':
        min_max_df = min_max_df[min_max_df['weather_date'].dt.month == 6]
    elif selected_month == 'July':
        min_max_df = min_max_df[min_max_df['weather_date'].dt.month == 7]
    elif selected_month == 'August':
        min_max_df = min_max_df[min_max_df['weather_date'].dt.month == 8]
    elif selected_month == 'September':
        min_max_df = min_max_df[min_max_df['weather_date'].dt.month == 9]

    if st.checkbox("Show Raw Data for Min & Max Observed Weather Conditions", False):
        st.subheader('Min & Max values for {}'.format(selected_station))
        st.dataframe(min_max_df)

    if look_at == 'minimum values':
        to_display = 'Min'
    else:
        to_display = 'Max'

    # TEMPERATURE
    temperature_fig = go.Figure()

    for year in min_max_df['year'].unique():
        years_temps = min_max_df[min_max_df['year'] == year]
        years_temps.dropna(subset=['min_temp', 'max_temp'], inplace=True)
        a0 = np.histogram(years_temps.iloc[2:, 4 if to_display ==
                          'Max' else 3], bins='auto', density=False)[0].tolist()
        a0 = np.repeat(a0, 2).tolist()
        a0.insert(0, 0)
        a0.pop()
        a1 = np.histogram(years_temps.iloc[2:, 4 if to_display ==
                          'Max' else 3], bins='auto', density=False)[1].tolist()
        a1 = np.repeat(a1, 2)
        temperature_fig.add_traces(go.Scatter3d(x=[year]*len(a0), y=a1, z=a0, mode='lines', name=str(year)))
    temperature_fig.update_layout(scene=dict(yaxis_title='TEMPERATURE (°C)',
                                             xaxis_title='YEAR', zaxis_title='FREQUENCY'))
    temperature_fig.update_layout(
        title=to_display + ' Daily Observed Temperature in ' + selected_month + ' - Distribution by Year')

    # RELATIVE HUMIDITY
    rh_fig = go.Figure()

    for year in min_max_df['year'].unique():
        year_rh = min_max_df[min_max_df['year'] == year]
        year_rh.dropna(subset=['min_RH', 'max_RH'], inplace=True)
        a0 = np.histogram(year_rh.iloc[2:, 6 if to_display == 'Max' else 5],
                          bins='auto', density=False)[0].tolist()
        a0 = np.repeat(a0, 2).tolist()
        a0.insert(0, 0)
        a0.pop()
        a1 = np.histogram(year_rh.iloc[2:, 6 if to_display == 'Max' else 5],
                          bins='auto', density=False)[1].tolist()
        a1 = np.repeat(a1, 2)
        rh_fig.add_traces(go.Scatter3d(x=[year]*len(a0), y=a1, z=a0, mode='lines', name=str(year)))
    rh_fig.update_layout(scene=dict(yaxis_title='RELATIVE HUMIDITY (%)',
                         xaxis_title='YEAR', zaxis_title='FREQUENCY'))
    rh_fig.update_layout(title=to_display + ' Daily Observed RH in ' +
                         selected_month + ' - Distribution by Year')

    # WIND SPEED
    wind_fig = go.Figure()

    for year in min_max_df['year'].unique():
        year_wind = min_max_df[min_max_df['year'] == year]
        year_wind.dropna(subset=['max_wind_speed', 'min_wind_speed'], inplace=True)
        a0 = np.histogram(year_wind.iloc[2:, 8 if to_display == 'Max' else 7],
                          bins='auto', density=False)[0].tolist()
        a0 = np.repeat(a0, 2).tolist()
        a0.insert(0, 0)
        a0.pop()
        a1 = np.histogram(year_wind.iloc[2:, 8 if to_display == 'Max' else 7],
                          bins='auto', density=False)[1].tolist()
        a1 = np.repeat(a1, 2)
        wind_fig.add_traces(go.Scatter3d(x=[year]*len(a0), y=a1, z=a0, mode='lines', name=str(year)))
    wind_fig.update_layout(scene=dict(yaxis_title='WIND SPEED (km/h)',
                                      xaxis_title='YEAR', zaxis_title='FREQUENCY'))
    wind_fig.update_layout(title=to_display + ' Daily Wind Speed in ' +
                           selected_month + ' - Distribution by Year')

    # FFMC
    ffmc_fig = go.Figure()

    for year in min_max_df['year'].unique():
        year_ffmc = min_max_df[min_max_df['year'] == year]
        year_ffmc.dropna(subset=['max_ffmc', 'min_ffmc'], inplace=True)
        a0 = np.histogram(year_ffmc.iloc[2:, 10 if to_display == 'Max' else 9],
                          bins='auto', density=False)[0].tolist()
        a0 = np.repeat(a0, 2).tolist()
        a0.insert(0, 0)
        a0.pop()
        a1 = np.histogram(year_ffmc.iloc[2:, 10 if to_display == 'Max' else 9],
                          bins='auto', density=False)[1].tolist()
        a1 = np.repeat(a1, 2)
        ffmc_fig.add_traces(go.Scatter3d(x=[year]*len(a0), y=a1, z=a0, mode='lines', name=str(year)))
    ffmc_fig.update_layout(scene=dict(yaxis_title='FFMC',
                                      xaxis_title='YEAR', zaxis_title='FREQUENCY'))
    ffmc_fig.update_layout(title=to_display + ' Daily Observed FFMC in ' +
                           selected_month + ' - Distribution by Year')

    # FWI
    fwi_fig = go.Figure()

    for year in min_max_df['year'].unique():
        year_fwi = min_max_df[min_max_df['year'] == year]
        year_fwi.dropna(subset=['max_fwi', 'min_fwi'], inplace=True)
        a0 = np.histogram(year_fwi.iloc[2:, 12 if to_display == 'Max' else 11],
                          bins='auto', density=False)[0].tolist()
        a0 = np.repeat(a0, 2).tolist()
        a0.insert(0, 0)
        a0.pop()
        a1 = np.histogram(year_fwi.iloc[2:, 12 if to_display == 'Max' else 11],
                          bins='auto', density=False)[1].tolist()
        a1 = np.repeat(a1, 2)
        fwi_fig.add_traces(go.Scatter3d(x=[year]*len(a0), y=a1, z=a0, mode='lines', name=str(year)))
    fwi_fig.update_layout(scene=dict(yaxis_title='FWI',
                                     xaxis_title='YEAR', zaxis_title='FREQUENCY'))
    fwi_fig.update_layout(title=to_display + ' Daily Observed FWI in ' +
                          selected_month + ' - Distribution by Year')

    st.plotly_chart(temperature_fig, use_container_width=True)
    st.plotly_chart(rh_fig, use_container_width=True)
    st.plotly_chart(wind_fig, use_container_width=True)
    st.plotly_chart(ffmc_fig, use_container_width=True)
    st.plotly_chart(fwi_fig, use_container_width=True)


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
fires_df.drop(columns=['Unnamed: 0'], inplace=True)
fires_df['CURRENT_SIZE'].fillna(value=0, inplace=True)

if st.checkbox("Show Raw Fire Data", False):
    st.subheader('Raw Fire Data for {}'.format(selected_year))
    st.dataframe(fires_df)

if fires_df.shape[0] > 0:
    fig = px.scatter(fires_df, x="IGNITION_DATE", y="STATION_DISTANCE", color="FIRE_CAUSE",
                     size=fires_df["CURRENT_SIZE"], hover_data=['LATITUDE', 'LONGITUDE', 'FIRE_NUMBER'])
    st.plotly_chart(fig, use_container_width=True)
else:
    st.write('No historic fires found for station {} in {}'.format(selected_code, selected_year))


hourlies_filename = '../../sourceData/hourlies/'+str(selected_year)+'/'+selected_code+'.csv'

# load hourlies_filename into dataframe - only interested in certain columns, so only load those
station_hourlies_df = pd.read_csv(hourlies_filename, usecols=[
                                  'display_name', 'weather_date', 'ffmc', 'isi', 'fwi'])
station_hourlies_df['weather_date'] = station_hourlies_df['weather_date'].apply(
    lambda row: convert_to_datetime(str(row)))

ffmc_df = station_hourlies_df[['weather_date', 'ffmc']].copy()
isi_df = station_hourlies_df[['weather_date', 'isi']].copy()
fwi_df = station_hourlies_df[['weather_date', 'fwi']].copy()

st.write(selected_station, """ Hourly FFMC for fire season """, str(selected_year))
ffmc_fig = px.scatter(ffmc_df, x='weather_date', y='ffmc')
st.plotly_chart(ffmc_fig, use_container_width=True)

st.write(selected_station, """ Hourly ISI for fire season """, str(selected_year))
isi_fig = px.scatter(isi_df, x='weather_date', y='isi')
st.plotly_chart(isi_fig, use_container_width=True)

st.write(selected_station, """ Hourly FWI for fire season """, str(selected_year))
fwi_fig = px.scatter(fwi_df, x='weather_date', y='fwi')
st.plotly_chart(fwi_fig, use_container_width=True)
