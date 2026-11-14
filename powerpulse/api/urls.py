from django.urls import path
from . import views

app_name = "api"

urlpatterns = [
    path("", views.api_root, name="root"),
    path("docs/", views.api_docs_view, name="docs"),
    path("readings/", views.readings_list_create, name="readings_list_create"),
    path("readings/upload-csv/", views.readings_upload_csv, name="readings_upload_csv"),
    path("bills/", views.bills_list_create, name="bills_list_create"),
    path("analytics/summary/", views.analytics_summary, name="analytics_summary"),
    path("analytics/forecast/", views.analytics_forecast, name="analytics_forecast"),
    path("analytics/anomalies/", views.analytics_anomalies, name="analytics_anomalies"),
    path("analytics/scan-anomalies/", views.analytics_scan, name="analytics_scan"),
]
