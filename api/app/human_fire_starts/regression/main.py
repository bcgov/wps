import os
import streamlit as st
from os.path import dirname, realpath
import matplotlib.pyplot as plt
import pandas
import datetime
from dateutil.parser import parse

from methods.evaluator import eval_model


def parse_date(datestr: str):
    """ Extract relevant date details from input string,
        normalize to midnight, return date string YYYY/MM/DD
    """
    dt = parse(datestr, yearfirst=True)
    return dt.timestamp()


DATASET_FOLDER_PATH = os.path.join(dirname(realpath(dirname(__file__))), 'data')
ALL_FIRES_CSV_PATH = os.path.join(DATASET_FOLDER_PATH, 'FIRE_STARTS_PER_ZONE.csv')
HUMAN_FIRES_CSV_PATH = os.path.join(DATASET_FOLDER_PATH, 'HUMAN_FIRE_STARTS_PER_ZONE.csv')


with st.sidebar:
    date_range = st.date_input(
        "Select date range",
        value=[datetime.date(1950, 1, 1), datetime.date.today()]
    )
    dataset = st.radio(
        "Select dataset",
        ('All Fires', 'Human Caused Fires'))
    method = st.radio(
        "Select regression method",
        ('Random Forest', 'Gradient Boost'))
    training_pct = st.number_input('Set training % to split data by',
                                   min_value=int(0), max_value=int(100), value=int(70))
    training_pct = round(training_pct * 0.01, 2)
    test_pct = round(1 - training_pct, 2)
    st.write('Training %:', training_pct, "Test %: ", test_pct)


if dataset == "All Fires":
    df = pandas.read_csv(ALL_FIRES_CSV_PATH)
else:
    df = pandas.read_csv(HUMAN_FIRES_CSV_PATH)

st.title("Fire Starts by Human Activity")
st.dataframe(df)
st.caption("Input data")
st.header("Random Forest Results")
df = df.set_index('DATE_ISO')

features = ['FIRE_CENTRE', 'ZONE', 'TIMESTAMP']
target = 'COUNT'


try:
    start_date, end_date = date_range
    selected_range = df[(df.index >= start_date.isoformat()) & (df.index <= end_date.isoformat())]
    output_label = f'{start_date.isoformat()} to {end_date.isoformat()}'
    model_result = eval_model(method, df, features, target, test_pct)

    # Plot
    st.subheader(output_label)
    st.write("R-squared: ", model_result.score, "MSE: ", model_result.mse, "RMSE: ", model_result.rmse)

    fig, ax = plt.subplots()
    x_ax = range(len(model_result.y_test))
    ax.plot(x_ax, model_result.y_test, linewidth=1, label="original")
    ax.plot(x_ax, model_result.y_pred, linewidth=1.1, label="predicted")
    ax.legend(loc='best', fancybox=True, shadow=True)
    ax.set_ylabel("Fire starts")
    ax.grid(True)
    st.pyplot(fig)
except Exception:
    # do nothing
    pass

# last_2_years = df[(df.index > '2020-05-01') & (df.index <= '2022-05-1')]
# eval_model(last_2_years, "May 1, 2020 to May 1, 2022 (Last 2 years)")

# last_5_years = df[(df.index > '2017-05-01') & (df.index <= '2022-05-1')]
# eval_model(last_5_years, "May 1, 2017 to May 1, 2022 (Last 5 years)")

# last_decade = df[(df.index > '2012-05-01') & (df.index <= '2022-05-1')]
# eval_model(last_decade, "May 1, 2012 to May 1, 2022 (Last Decade)")

# last_two_decade = df[(df.index > '2002-05-01') & (df.index <= '2022-05-1')]
# eval_model(last_two_decade, "May 1, 2002 to May 1, 2022 (Last 2 decades)")

# last_three_decade = df[(df.index > '1992-05-01') & (df.index <= '2022-05-1')]
# eval_model(last_three_decade, "May 1, 1992 to May 1, 2022 (Last three decades)")
