import numpy as np
import pandas as pd
from decimal import Decimal
from sklearn.ensemble import IsolationForest
from energy.models import ElectricityReading, AnomalyAlert


def detect_anomalies_for_user(user, contamination=0.07):
    """
    Detect statistical and ML-based anomalies in electricity readings for a given user.
    Uses a hybrid approach:
    1. Isolation Forest for multidimensional outlier detection
    2. Statistical Z-Score / IQR thresholding for surge/spike identification
    """
    readings = ElectricityReading.objects.filter(user=user).order_by("reading_date")
    if readings.count() < 5:
        return 0

    df = pd.DataFrame(list(readings.values("id", "reading_date", "consumption_kwh", "building_name")))
    df["consumption_kwh"] = df["consumption_kwh"].astype(float)
    df["reading_date"] = pd.to_datetime(df["reading_date"])

    values = df["consumption_kwh"].values.reshape(-1, 1)
    
    # 1. Isolation Forest
    actual_contamination = min(max(contamination, 0.02), 0.2)
    iso = IsolationForest(contamination=actual_contamination, random_state=42)
    iso_preds = iso.fit_predict(values)
    anomaly_scores = -iso.score_samples(values)  # higher = more anomalous

    # 2. Statistical benchmarks
    mean_val = float(df["consumption_kwh"].mean())
    std_val = float(df["consumption_kwh"].std()) if df["consumption_kwh"].std() > 0 else 1.0
    q75, q25 = np.percentile(df["consumption_kwh"], [75, 25])
    iqr = q75 - q25
    upper_threshold = q75 + (1.75 * iqr) if iqr > 0 else (mean_val + 2 * std_val)

    created_count = 0
    for idx, row in df.iterrows():
        is_iso_anomaly = (iso_preds[idx] == -1)
        kwh = row["consumption_kwh"]
        is_spike = kwh > upper_threshold
        is_surge = kwh > (mean_val + 2.2 * std_val)

        if is_iso_anomaly or is_spike or is_surge:
            reading_obj = readings.get(id=row["id"])
            
            # Determine human-friendly diagnostic reason
            if kwh > (mean_val * 2.0) and kwh > 50:
                pct = int(((kwh - mean_val) / mean_val) * 100)
                reason = f"Severe Consumption Spike: {kwh:.1f} kWh ({pct}% above average {mean_val:.1f} kWh)"
            elif is_surge:
                reason = f"Unusual Consumption Surge: {kwh:.1f} kWh deviates significantly from normal baseline ({mean_val:.1f} kWh)"
            elif is_spike:
                reason = f"Above Normal Pattern: {kwh:.1f} kWh exceeds the 75th percentile ceiling ({upper_threshold:.1f} kWh)"
            else:
                reason = f"Atypical Pattern Detected: {kwh:.1f} kWh flagged by machine learning model"

            alert, created = AnomalyAlert.objects.update_or_create(
                user=user,
                reading=reading_obj,
                reading_date=row["reading_date"].date(),
                defaults={
                    "consumption_kwh": Decimal(str(round(kwh, 2))),
                    "reason": reason,
                    "anomaly_score": round(float(anomaly_scores[idx]), 3),
                }
            )
            if created:
                created_count += 1

    return created_count

