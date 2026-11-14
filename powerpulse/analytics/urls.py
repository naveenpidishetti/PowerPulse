from django.urls import path
from . import views

app_name = "analytics"

urlpatterns = [
    path("", views.analytics_overview, name="overview"),
    path("anomalies/", views.anomalies_view, name="anomalies"),
    path("anomalies/scan/", views.run_anomaly_scan, name="run_scan"),
    path("predict/", views.predict_view, name="predict"),
    path("export-pdf/", views.export_pdf_report, name="export_pdf"),
]
