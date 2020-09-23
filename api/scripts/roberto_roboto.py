import matplotlib.pyplot as plt
import datetime
import numpy as np
import math
# import pymc3 as pm
import keras
from keras.models import Sequential
from keras.layers import Dense
import split_test_training_data

# import datasets
training_data, test_data = split_test_training_data.get_training_and_test_data()

# convert multi-index dataframe to dataframe with indices as columns (necessary for Patsy formula)
training_set = training_data.reset_index()
training_set.rename(columns={"level_0": "IGN_YEAR", "level_1": "IGN_DATE",
                             "level_2": "GRID_ID"}, inplace=True)

# change dataframe to numpy array
X = np.asarray(training_set.iloc[:, :3].values).astype(np.float32)
y = np.asarray(training_set.iloc[:, 3:4].values).astype(np.float32)

test_data = test_data.reset_index()
test_data.rename(columns={"level_0": "IGN_YEAR", "level_1": "IGN_DATE", "level_2": "GRID_ID"}, inplace=True)
# predicted_fires DF will be used for matching output y_pred to dates and grid_ids
predicted_fires = test_data.copy(deep=True)

# change test dataframe to numpy array
X_test = np.asarray(test_data.iloc[:, :3].values).astype(np.float32)
y_test = np.asarray(test_data.iloc[:, 3:4].values).astype(np.float32)

# TODO: normalize data

# build the neural net
model = Sequential()
model.add(Dense(6, input_dim=3, activation='tanh'))
# model.add(Dense(3, activation='tanh'))
model.add(Dense(1, activation='tanh'))
model.compile(optimizer='adam', loss=['mse', 'mape'])

# train the neural net
history = model.fit(X, y, validation_data=(X_test, y_test), epochs=50, batch_size=1500000)
train_mse = model.evaluate(X, y)
print(train_mse)

# validate
y_pred = model.predict(X_test)
pred = list()
for i in range(len(y_pred)):
    pred.append(max(y_pred[i], 0))

# flatten pred so the list only has depth of 1
flat_pred = []
for y in pred:
    if isinstance(y, np.ndarray):
        flat_pred.append(y[0])
    elif isinstance(y, int):
        flat_pred.append(y)

# write pred values to predicted_fires DF in SIZE_HA column
predicted_fires['SIZE_HA'] = flat_pred
predicted_fires.insert(loc=4, column='X', value=np.zeros(shape=(len(flat_pred),)))
predicted_fires.insert(loc=5, column='Y', value=np.zeros(shape=(len(flat_pred),)))

# make a copy of predicted_fires for iterating purposes
copy_predicted_fires = predicted_fires.copy(deep=True)
# iterate over rows in predicted_fires, inserting X and Y coordinates for grid_id
for index, row in predicted_fires.iterrows():
    x, y = split_test_training_data.get_albers_coords_for_grid_id(row['GRID_ID'])
    copy_predicted_fires.iat[index, 4] = x  # fifth column (index 4) is 'X'
    copy_predicted_fires.iat[index, 5] = y  # sixth column (index 5) is 'Y'

copy_test_data = test_data.copy(deep=True)
test_data.insert(loc=4, column='X', value=np.zeros(shape=(len(flat_pred),)))
test_data.insert(loc=5, column='Y', value=np.zeros(shape=(len(flat_pred),)))
for index, row in copy_test_data.iterrows():
    x, y = split_test_training_data.get_albers_coords_for_grid_id(row['GRID_ID'])
    test_data.iat[index, 4] = x
    test_data.iat[index, 5] = y

for index, row in copy_test_data.iterrows():
    predicted_fire = copy_predicted_fires.iloc[index]
    if predicted_fire['SIZE_HA'] == 0 and row['SIZE_HA'] == 0:
        print('date: {}\t\tpredicted: {}\t\tactual: {}'.format(
            row['IGN_DATE'], predicted_fire['SIZE_HA'], row['SIZE_HA']))

filename = 'predicted_fires-{}'.format(datetime.datetime.now())
test_data_filename = 'actual_test_fires-{}'.format(datetime.datetime.now())
copy_predicted_fires.to_csv(filename, index=False)
test_data.to_csv(test_data_filename, index=False)
print('max predicted fire size: {}'.format(copy_predicted_fires['SIZE_HA'].max()))
print('predicted data - value count: {}'.format(copy_predicted_fires['SIZE_HA'].value_counts()))
print('actual data - value count: {}'.format(test_data['SIZE_HA'].value_counts()))
