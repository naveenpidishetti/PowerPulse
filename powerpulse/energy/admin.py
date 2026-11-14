from django.contrib import admin

from .models import (
    AnomalyAlert,
    ElectricityReading,
    MonthlyElectricityBill,
    PredictionRecord,
)


@admin.register(ElectricityReading)
class ElectricityReadingAdmin(admin.ModelAdmin):
    list_display = ("user", "reading_date", "consumption_kwh", "estimated_cost", "source")
    list_filter = ("source", "reading_date")
    search_fields = ("user__username", "building_name")


@admin.register(MonthlyElectricityBill)
class MonthlyElectricityBillAdmin(admin.ModelAdmin):
    list_display = ("user", "billing_month", "units_consumed", "bill_amount")


@admin.register(AnomalyAlert)
class AnomalyAlertAdmin(admin.ModelAdmin):
    list_display = ("user", "reading_date", "consumption_kwh", "reason")


@admin.register(PredictionRecord)
class PredictionRecordAdmin(admin.ModelAdmin):
    list_display = ("user", "target_date", "predicted_kwh", "model_name", "created_at")
