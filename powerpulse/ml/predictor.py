from datetime import timedelta
from decimal import Decimal
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

from energy.models import ElectricityReading, PredictionRecord


def run_consumption_prediction(user, horizon_days=7, model_type="rf"):
    """
    Train a machine learning model on historical electricity consumption data
    and predict consumption for upcoming days.
    
    Returns a dict with:
      - metrics: {baseline_mae, model_mae, model_rmse, r2, train_size, test_size}
      - historical: list of {date, actual}
      - forecasts: list of {date, predicted_kwh, estimated_cost}
      - model_name: string
    """
    readings = ElectricityReading.objects.filter(user=user).order_by("reading_date")
    count = readings.count()
    if count < 10:
        return {
            "success": False,
            "error": "At least 10 historical readings are needed to train the predictive model.",
            "count": count
        }

    # Build DataFrame
    df = pd.DataFrame(list(readings.values(
        "reading_date", "consumption_kwh", "tariff_per_unit"
    )))
    df["reading_date"] = pd.to_datetime(df["reading_date"])
    df["consumption_kwh"] = df["consumption_kwh"].astype(float)
    df = df.sort_values("reading_date").reset_index(drop=True)

    # Average tariff for cost estimation
    avg_tariff = df["tariff_per_unit"].dropna().astype(float).mean()
    if pd.isna(avg_tariff) or avg_tariff <= 0:
        avg_tariff = 8.50  # reasonable default $/INR per unit

    # Feature engineering
    df["dayofweek"] = df["reading_date"].dt.dayofweek
    df["day"] = df["reading_date"].dt.day
    df["month"] = df["reading_date"].dt.month
    df["is_weekend"] = df["dayofweek"].isin([5, 6]).astype(int)
    
    # Lags & Rolling
    df["lag_1"] = df["consumption_kwh"].shift(1)
    df["lag_2"] = df["consumption_kwh"].shift(2)
    df["lag_7"] = df["consumption_kwh"].shift(7)
    df["rolling_7_mean"] = df["consumption_kwh"].shift(1).rolling(window=7, min_periods=1).mean()

    # Fill NaNs from shifting with backfill/bfill
    df["lag_1"] = df["lag_1"].bfill()
    df["lag_2"] = df["lag_2"].bfill()
    df["lag_7"] = df["lag_7"].bfill()
    df["rolling_7_mean"] = df["rolling_7_mean"].bfill()

    feature_cols = ["dayofweek", "day", "month", "is_weekend", "lag_1", "lag_2", "lag_7", "rolling_7_mean"]
    X = df[feature_cols]
    y = df["consumption_kwh"]

    # Train / Test split (Holdout last min(7, 20% of data))
    test_size = max(3, min(horizon_days, int(len(df) * 0.2)))
    train_size = len(df) - test_size

    X_train, X_test = X.iloc[:train_size], X.iloc[train_size:]
    y_train, y_test = y.iloc[:train_size], y.iloc[train_size:]

    # Select model
    if model_type == "linear":
        model = Ridge(alpha=1.0)
        model_name = "Ridge Linear Regression"
    else:
        model = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42)
        model_name = "Random Forest Regressor"

    model.fit(X_train, y_train)

    # Evaluate
    y_pred_test = model.predict(X_test)
    y_pred_test = np.clip(y_pred_test, a_min=0, a_max=None)

    # Baseline: persistence / rolling mean
    baseline_pred = df["rolling_7_mean"].iloc[train_size:]
    baseline_mae = float(mean_absolute_error(y_test, baseline_pred))
    model_mae = float(mean_absolute_error(y_test, y_pred_test))
    model_rmse = float(root_mean_squared_error(y_test, y_pred_test))

    # Refit on full dataset for future forecasting
    model.fit(X, y)

    # Iterative forecast for future horizon
    last_date = df["reading_date"].max()
    curr_df = df.copy()
    future_forecasts = []

    for i in range(1, horizon_days + 1):
        next_date = last_date + timedelta(days=i)
        
        # Construct feature vector for next date
        dayofweek = next_date.dayofweek
        day = next_date.day
        month = next_date.month
        is_weekend = 1 if dayofweek in [5, 6] else 0

        lag_1 = curr_df["consumption_kwh"].iloc[-1]
        lag_2 = curr_df["consumption_kwh"].iloc[-2] if len(curr_df) >= 2 else lag_1
        lag_7 = curr_df["consumption_kwh"].iloc[-7] if len(curr_df) >= 7 else lag_1
        rolling_7 = curr_df["consumption_kwh"].iloc[-7:].mean()

        row_feat = pd.DataFrame([{
            "dayofweek": dayofweek,
            "day": day,
            "month": month,
            "is_weekend": is_weekend,
            "lag_1": lag_1,
            "lag_2": lag_2,
            "lag_7": lag_7,
            "rolling_7_mean": rolling_7,
        }])

        pred_val = max(0.0, float(model.predict(row_feat)[0]))
        pred_val = round(pred_val, 2)
        est_cost = round(pred_val * avg_tariff, 2)

        future_forecasts.append({
            "date": next_date.strftime("%Y-%m-%d"),
            "predicted_kwh": pred_val,
            "estimated_cost": est_cost,
        })

        # Append predicted row to curr_df for subsequent auto-regressive lags
        new_row = pd.DataFrame([{
            "reading_date": next_date,
            "consumption_kwh": pred_val,
            "tariff_per_unit": avg_tariff,
            "dayofweek": dayofweek,
            "day": day,
            "month": month,
            "is_weekend": is_weekend,
            "lag_1": lag_1,
            "lag_2": lag_2,
            "lag_7": lag_7,
            "rolling_7_mean": rolling_7
        }])
        curr_df = pd.concat([curr_df, new_row], ignore_index=True)

        # Save to database
        PredictionRecord.objects.update_or_create(
            user=user,
            target_date=next_date.date(),
            defaults={
                "predicted_kwh": Decimal(str(pred_val)),
                "model_name": model_name,
                "baseline_mae": round(baseline_mae, 3),
                "model_mae": round(model_mae, 3),
                "model_rmse": round(model_rmse, 3),
                "train_size": train_size,
                "test_size": test_size,
            }
        )

    # Historical sample for chart (last 30 readings)
    recent_history = [
        {
            "date": row["reading_date"].strftime("%Y-%m-%d"),
            "kwh": round(row["consumption_kwh"], 2)
        }
        for _, row in df.tail(30).iterrows()
    ]

    return {
        "success": True,
        "model_name": model_name,
        "metrics": {
            "baseline_mae": round(baseline_mae, 2),
            "model_mae": round(model_mae, 2),
            "model_rmse": round(model_rmse, 2),
            "improvement_pct": round(max(0, (baseline_mae - model_mae) / (baseline_mae + 1e-6) * 100), 1),
            "train_size": train_size,
            "test_size": test_size,
        },
        "forecasts": future_forecasts,
        "historical": recent_history,
        "avg_tariff": round(avg_tariff, 2),
    }

