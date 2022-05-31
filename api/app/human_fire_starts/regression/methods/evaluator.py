from . import ModelResult
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error


def eval_model(method, input_df, features, target, test_pct) -> ModelResult:
    if method == "Random Forest":
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        return run_eval(model, input_df, features, target, test_pct)
    elif method == "Gradient Boost":
        model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        return run_eval(model, input_df, features, target, test_pct)
    pass


def run_eval(model, input_df, features, target, test_pct) -> ModelResult:
    X = input_df[features]  # Features
    y = input_df[target]  # Labels

    # Split data, based on test percentage
    X_train, X_test, y_train, y_test = train_test_split(X.values, y, test_size=test_pct)

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
