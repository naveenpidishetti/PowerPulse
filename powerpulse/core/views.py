from datetime import date, timedelta
from decimal import Decimal
import json

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum
from django.shortcuts import render

from energy.models import AnomalyAlert, ElectricityReading, MonthlyElectricityBill, PredictionRecord


def landing(request):
    """Modern public landing page introducing PowerPulse."""
    total_tracked_kwh = ElectricityReading.objects.aggregate(total=Sum("consumption_kwh"))["total"] or 0
    total_users = ElectricityReading.objects.values("user").distinct().count()
    total_anomalies = AnomalyAlert.objects.count()

    context = {
        "total_tracked_kwh": round(total_tracked_kwh, 1),
        "total_users": total_users,
        "total_anomalies": total_anomalies,
    }
    return render(request, "landing.html", context)


@login_required
def dashboard(request):
    """Main authenticated intelligence dashboard."""
    user = request.user
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)

    # All user readings
    readings_qs = ElectricityReading.objects.filter(user=user)
    total_readings_count = readings_qs.count()

    # 30-day stats
    readings_30d = readings_qs.filter(reading_date__gte=thirty_days_ago)
    kwh_30d = readings_30d.aggregate(total=Sum("consumption_kwh"))["total"] or Decimal("0")
    cost_30d = readings_30d.aggregate(total=Sum("estimated_cost"))["total"] or Decimal("0")
    daily_avg_30d = readings_30d.aggregate(avg=Avg("consumption_kwh"))["avg"] or Decimal("0")

    # Recent readings
    recent_readings = readings_qs.order_by("-reading_date")[:7]

    # Anomalies
    anomaly_alerts = AnomalyAlert.objects.filter(user=user).order_by("-reading_date")
    anomalies_count = anomaly_alerts.count()
    recent_anomalies = anomaly_alerts[:4]

    # Next 7-day predictions
    predictions = PredictionRecord.objects.filter(user=user, target_date__gte=today).order_by("target_date")[:7]
    predicted_next_7d_kwh = sum([float(p.predicted_kwh) for p in predictions]) if predictions else 0.0

    # Chart data (last 30 days daily consumption)
    chart_qs = list(readings_qs.order_by("-reading_date")[:30])
    chart_qs.reverse()
    
    chart_dates = [r.reading_date.strftime("%b %d") for r in chart_qs]
    chart_values = [float(r.consumption_kwh) for r in chart_qs]

    context = {
        "total_readings_count": total_readings_count,
        "kwh_30d": round(kwh_30d, 1),
        "cost_30d": round(cost_30d, 2),
        "daily_avg_30d": round(daily_avg_30d, 1),
        "anomalies_count": anomalies_count,
        "recent_anomalies": recent_anomalies,
        "predicted_next_7d_kwh": round(predicted_next_7d_kwh, 1),
        "predictions": predictions,
        "recent_readings": recent_readings,
        "chart_dates_json": json.dumps(chart_dates),
        "chart_values_json": json.dumps(chart_values),
    }
    return render(request, "core/dashboard.html", context)


def user_manual(request):
    """Interactive Book-Style User Manual for PowerPulse."""
    return render(request, "core/manual.html")

