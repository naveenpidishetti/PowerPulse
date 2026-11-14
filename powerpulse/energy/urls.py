from django.urls import path
from . import views

app_name = "energy"

urlpatterns = [
    path("readings/", views.reading_list_view, name="reading_list"),
    path("readings/add/", views.reading_create_view, name="reading_create"),
    path("readings/<int:pk>/delete/", views.reading_delete_view, name="reading_delete"),
    path("readings/upload/", views.reading_upload_csv_view, name="reading_upload"),
    path("readings/upload-csv/", views.reading_upload_csv_view, name="upload_csv"),
    path("readings/sample-csv/", views.download_sample_csv_view, name="download_sample_csv"),
    path("bills/", views.bill_list_view, name="bill_list"),
    path("bills/add/", views.bill_create_view, name="bill_create"),
    path("bills/<int:pk>/delete/", views.bill_delete_view, name="bill_delete"),
    path("seed-demo/", views.seed_demo_data_view, name="seed_demo"),
]
