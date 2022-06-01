from . import ModelResult, RegressionMethod
from sklearn.ensemble import (AdaBoostRegressor,
                              HistGradientBoostingRegressor,
                              RandomForestRegressor,
                              GradientBoostingRegressor,
                              BaggingRegressor,
                              ExtraTreesRegressor)
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error


def eval_model(method, input_df, features, target, test_pct) -> ModelResult:
    model_lookup = {RegressionMethod.RANDOM_FOREST: RandomForestRegressor(n_estimators=100, random_state=42),
                    RegressionMethod.GRADIENT_BOOST: GradientBoostingRegressor(n_estimators=100, random_state=42),
                    RegressionMethod.EXTRA_TREES: ExtraTreesRegressor(n_estimators=100, random_state=42),
                    RegressionMethod.BAGGING: BaggingRegressor(n_estimators=100, random_state=42),
                    RegressionMethod.ADA: AdaBoostRegressor(n_estimators=100, random_state=42),
                    RegressionMethod.LINEAR: LinearRegression(),
                    RegressionMethod.HIST_GRADIENT_BOOST: HistGradientBoostingRegressor()}
    model = model_lookup.get(method, None)
    if model is not None:
        return run_eval(model, input_df, features, target, test_pct)


def run_eval(model, input_df, features, target, test_pct) -> ModelResult:
    X = input_df[features]  # Features
    y = input_df[target]  # Labels

    # Split data, based on test percentage
    X_train, X_test, y_train, y_test = train_test_split(X.values, y, test_size=test_pct, shuffle=False)

    model.fit(X_train, y_train)

    score = model.score(X_train, y_train)

    y_pred = model.predict(X_test)

    mse = mean_squared_error(y_test, y_pred)

    return ModelResult(score=score,
                       mse=mse,
                       rmse=mse * (1 / 2.0),
                       model=model,
                       X_train=X_train,
                       X_test=X_test,
                       y_train=y_train,
                       y_test=y_test,
                       y_pred=y_pred)
