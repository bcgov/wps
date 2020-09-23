""" Split input CSV of historical fire incidents into training dataset and test dataset.
Training dataset is for fire years from start of recording to end of 2017.
Test dataset is for fire years 2018 - 2019.
"""
import datetime
import math
import pandas as pd
import numpy as np
from itertools import product

# X_ALBERS_OFFSET = 1305576
# Y_ALBERS_OFFSET = 600758
# X_ALBERS_MAX = 1550727
# Y_ALBERS_MAX = 809916
X_ALBERS_OFFSET = 1035214
Y_ALBERS_OFFSET = 458438
X_ALBERS_MAX = 1593370
Y_ALBERS_MAX = 812920
X_ALBERS_DISTANCE = X_ALBERS_MAX - X_ALBERS_OFFSET
Y_ALBERS_DISTANCE = Y_ALBERS_MAX - Y_ALBERS_OFFSET
GRID_SIZE_IN_METRES = 25000

FIRE_SEASON_START_MONTH = 4
FIRE_SEASON_END_MONTH = 9
FIRE_SEASON_START_DAY = 1
FIRE_SEASON_END_DAY = 30


def get_training_and_test_data():
    # import the CSV file
    with open('scripts/H_FIRE_PNT.csv', 'r') as csvfile:
        historic_fires = pd.read_csv(csvfile)
        # drop unneeded columns
        historic_fires.drop(['FIRE_NO', 'FIRELABEL', 'FRCNTR', 'ZONE', 'FIRE_ID',
                             'GEO_DESC', 'FCODE', 'SHAPE', 'OBJECTID'], axis=1, inplace=True)
        # drop rows where FIRE_TYPE is "Smoke Chase"
        historic_fires = historic_fires[historic_fires.FIRE_TYPE != 'Smoke Chase']
        # drop rows where FIRE_TYPE is "Duplicate"
        historic_fires = historic_fires[historic_fires.FIRE_TYPE != 'Duplicate']
        # drop rows where FIRE_YEAR < 2010
        historic_fires = historic_fires[(historic_fires.FIRE_YEAR > 2000)]
        # drop rows where IGN_DATE is NaN
        historic_fires.dropna(inplace=True)
        # reformat IGN_DATE column to be proper Datetime values
        # first convert the value to a str for convenience
        historic_fires['IGN_DATE'] = historic_fires['IGN_DATE'].apply(lambda x: str(x))
        historic_fires['IGN_YEAR'] = historic_fires['IGN_DATE'].apply(lambda x: int(x[:4]))
        historic_fires['IGN_MONTH'] = historic_fires['IGN_DATE'].apply(lambda x: int(x[4:6]))
        historic_fires['IGN_DAY'] = historic_fires['IGN_DATE'].apply(lambda x: int(x[6:8]))
        # drop the IGN_DATE column - it's now a duplicate of the _YEAR, _MONTH, and _DAY columns
        historic_fires.drop(columns=['IGN_DATE'], inplace=True)

        # create dataframe of training data for fire_years up to and incl. 2017
        training_df = build_data_df(2000, 2017, historic_fires)
        print('Training DF built. Size {}'.format(training_df.size))
        # create dataframe of testing data for fire_years 2018 and 2019
        testing_df = build_data_df(2019, 2019, historic_fires)
        print('Testing DF built. Size {}'.format(testing_df.size))

    return (training_df, testing_df)


def build_data_df(start_year: int, end_year: int, input_data: pd.DataFrame):
    """ Builds up pandas dataframe of data, based on dataframe from imported CSV data.
    Dataframe contains a row for each year, month in fire season, day, and grid_id within grid.
    SIZE_HA is the size of the largest wildfire that occurred on that date in that grid_id.
    SIZE_HA = 0 means that there was no fire, or that the fire was so small in size that it was recorded as 0.
    """
    OUTSIDE_FIRE_SEASON = 0

    fire_datetimes = []
    fire_years = list(x for x in range(start_year, end_year + 1))

    # temporarily create datetime objects for easy addition of one day at a time
    date = datetime.date(year=start_year, month=FIRE_SEASON_START_MONTH, day=FIRE_SEASON_START_DAY)
    end_season = datetime.date(year=start_year, month=FIRE_SEASON_END_MONTH, day=FIRE_SEASON_END_DAY)
    while date <= end_season:
        fire_datetimes.append(date)
        date += datetime.timedelta(days=1)

    # now rewrite the fire_datetimes as MMDD ints
    fire_datetimes = [str(x) for x in fire_datetimes]
    fire_dates = [x[5:10].replace('-', '') for x in fire_datetimes]

    grid_ids = np.array(get_list_of_valid_grid_ids())

    first = list(product(fire_dates, grid_ids))
    second = list(product(fire_years, first))

    fire_dates = np.repeat(np.array(fire_dates), len(grid_ids))
    fire_years = np.repeat(np.array(fire_years), len(first))

    grids = np.tile(grid_ids, int(len(second)/len(grid_ids)))
    dates = np.tile(np.array(fire_dates), int(len(second)/len(fire_dates)))
    years = np.tile(np.array(fire_years), int(len(second)/len(fire_years)))

    # build a Dataframe with columns ['IGN_YEAR', 'IGN_DATE', 'GRID_ID']
    fire_data = pd.DataFrame(np.zeros(len(second)), index=[years, dates, grids], columns=['SIZE_HA'])

    # insert input_data into correct SIZE_HA cell iteratively
    for index, row in input_data.iterrows():
        # ignore rows where X,Y is not within our bounds of interest
        if row['X'] < X_ALBERS_OFFSET or row['Y'] < Y_ALBERS_OFFSET or row['X'] > X_ALBERS_MAX or row['Y'] > Y_ALBERS_MAX:
            continue

        fire_month = row['IGN_MONTH']
        fire_year = row['IGN_YEAR']
        fire_day = row['IGN_DAY']
        # ignore rows where IGN_DATE is not within fire season:
        if fire_month < FIRE_SEASON_START_MONTH or fire_month > FIRE_SEASON_END_MONTH:
            OUTSIDE_FIRE_SEASON += 1
            continue
        # ignore rows where IGN_DATE year is not within (start_year, end_year) bounds
        if fire_year < start_year or fire_year > end_year:
            continue

        grid_id = get_grid_id_for_albers_coords(row['X'], row['Y'])
        fire_size = row['SIZE_HA']
        fire_month = str(fire_month).zfill(2)
        fire_day = str(fire_day).zfill(2)
        fire_month_day = fire_month + fire_day
        mi = fire_data.loc[fire_year, fire_month_day, grid_id]
        mi['SIZE_HA'] += fire_size

    print('num of rows outside fire season: {}'.format(OUTSIDE_FIRE_SEASON))
    return fire_data


def get_grid_id_for_albers_coords(x: float, y: float):
    """ Returns corresponding grid_id based on value of BC Albers coordinates """
    grid_x = math.floor((x - X_ALBERS_OFFSET) / GRID_SIZE_IN_METRES)
    grid_y = math.floor((y - Y_ALBERS_OFFSET) / GRID_SIZE_IN_METRES)
    grid_id = grid_y * math.floor(X_ALBERS_DISTANCE / GRID_SIZE_IN_METRES) + grid_x
    return grid_id


def get_albers_coords_for_grid_id(grid_id: int):
    """ Returns corresponding BC Albers coordinates (X,Y) for given grid_id """
    grid_x = grid_id % math.floor(X_ALBERS_DISTANCE/GRID_SIZE_IN_METRES)
    grid_y = math.floor((GRID_SIZE_IN_METRES*(grid_id - grid_x + 1))/X_ALBERS_DISTANCE)
    x = X_ALBERS_OFFSET + (grid_x * GRID_SIZE_IN_METRES)
    y = Y_ALBERS_OFFSET + (grid_y * GRID_SIZE_IN_METRES)
    return (x, y)


def get_list_of_valid_grid_ids():
    """ Returns list of all valid grid_ids """
    max_grid_x = math.floor(X_ALBERS_DISTANCE / GRID_SIZE_IN_METRES) + 1
    max_grid_y = math.floor(Y_ALBERS_DISTANCE / GRID_SIZE_IN_METRES) + 1
    max_grid_id = max_grid_y * max_grid_x
    valid_ids = list(range(0, max_grid_id + 1))
    return valid_ids
