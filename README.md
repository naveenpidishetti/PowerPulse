# PowerPulse ⚡
**Smart Electricity Consumption Prediction & Anomaly Detection System**

PowerPulse is a full-stack energy intelligence web application built with **Django 5.2, SQLite, Pandas, Scikit-learn, Chart.js, and ReportLab**. It allows households, facility managers, and energy auditors to record meter readings, ingest bulk historical CSV datasets, forecast future electricity loads with machine learning, flag abnormal consumption surges with Isolation Forests, and export executive PDF audit reports.

---

## Quick Launch (Windows)
Double-click `start_server.bat` in this folder to start the application, then open:
👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** (or `http://localhost:8000/`)

---

## Key Features

1. **Energy Intelligence Dashboard**
   - 30-day consumption metrics, daily averages, and cumulative cost estimations.
   - Interactive daily usage timeline charts rendered via Chart.js.
   - Proactive alert panel for statistical surges and hardware anomalies.

2. **Machine Learning Load Forecasting**
   - Time-series auto-regressive regression using **Random Forest Regressor** and **Ridge Regression**.
   - Calendar feature extraction (Day of Week, Day of Month, Month, Weekend status).
   - Dynamic lag features (`lag_1`, `lag_2`, `lag_7`) and rolling window averages (`rolling_7_mean`).
   - Benchmarked against naive persistence baselines with live **MAE** (Mean Absolute Error) and **RMSE** scores.

3. **Surge & Anomaly Detection**
   - Dual-layer unsupervised anomaly detection combining Scikit-learn **Isolation Forest** and $2.5\sigma$ / IQR statistical thresholding.
   - Automatically attributes human-readable diagnostic reasons to flagged readings.

4. **Meter Reading Management & CSV Bulk Ingestion**
   - Manual meter logger with automatic delta calculations (`Current - Previous = Net Consumption`) and cost estimation based on active tariff rates.
   - Bulk CSV file parser supporting standard headers.
   - Sample CSV available at `powerpulse/sample_data/sample_meter_readings.csv`.

5. **Utility Bill Auditing**
   - Monthly utility billing logs with effective cost-per-unit metrics to monitor rate inflation.

6. **Executive PDF Audit Report**
   - One-click generated PDF audit summary using **ReportLab** containing KPI scorecards, ML forecasts, and detected anomaly logs.

7. **One-Click Instant Demo**
   - Instant Demo login option with a pre-seeded 90-day synthetic dataset.

---

## Project Structure

```text
PowerPulse/
├── start_server.bat             # Root one-click server launcher
├── README.md                    # Root project documentation
└── powerpulse/                  # Django project root
    ├── manage.py                # Django CLI management script
    ├── start_server.bat         # Direct launcher
    ├── db.sqlite3               # SQLite database
    ├── requirements.txt         # Python dependencies
    ├── .env.example             # Environment configuration template
    ├── accounts/                # User authentication & demo session management
    ├── analytics/               # Visual charts, PDF export, metrics views
    ├── core/                    # Landing page & main authenticated dashboard
    ├── energy/                  # ElectricityReading & MonthlyElectricityBill models/views
    ├── ml/                      # Machine learning forecasting & anomaly detection algorithms
    ├── sample_data/             # Sample datasets for bulk CSV testing
    ├── templates/               # Responsive HTML templates with Bootstrap 5
    └── powerpulse/              # Project settings & URL routing
```

---

## Running Automated Tests

```powershell
cd powerpulse
.\venv\Scripts\python.exe manage.py test
```

