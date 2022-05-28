import streamlit as st
import pandas as pd
# import geopandas as gpd
import numpy as np

import os
from os.path import dirname, abspath


def load_data_from_geojson(filename):
    DATASET_FOLDER_PATH = os.path.join(dirname(abspath('')), 'data')
    raw_source = os.path.join(DATASET_FOLDER_PATH, filename)

    with open(raw_source) as f:
        data = pd.read_json(f)
    df = pd.json_normalize(data['features'])
    coords = 'properties.geometry.coordinates'
    df2 = (df[coords].apply(lambda r: [(i[0], i[1]) for i in r[0]])).apply(pd.Series).stack().reset_index(
        level=1).rename(columns={0: coords, "level_1": "point"}).join(df.drop(coords, 1), how='left').reset_index(level=0)
    df2[['lat', 'long']] = df2[coords].apply(pd.Series)
    return df2


st.title("Fire Starts by Human Activity")

df = load_data_from_geojson('historical_fires_extra_features.geojson')
st.table(df)
# st.map(df)
