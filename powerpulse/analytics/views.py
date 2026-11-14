from datetime import date, timedelta
from decimal import Decimal
import io
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Max, Min, Sum
from django.http import HttpResponse
from django.shortcuts import redirect, render

from energy.models import AnomalyAlert, ElectricityReading, MonthlyElectricityBill, PredictionRecord
from ml.anomaly_detector import detect_anomalies_for_user
from ml.predictor import run_consumption_prediction

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


@login_required
def analytics_overview(request):
    readings = ElectricityReading.objects.filter(user=request.user).order_by("reading_date")
    total_count = readings.count()

    if total_count == 0:
        return render(request, "analytics/overview.html", {
            "has_data": False,
        })

    # Summary KPIs
    agg = readings.aggregate(
        total_kwh=Sum("consumption_kwh"),
        avg_kwh=Avg("consumption_kwh"),
        max_kwh=Max("consumption_kwh"),
        min_kwh=Min("consumption_kwh"),
        total_cost=Sum("estimated_cost")
    )

    # Daily trend (last 60 days)
    recent_readings = list(readings.order_by("-reading_date")[:60])
    recent_readings.reverse()

    chart_dates = [r.reading_date.strftime("%Y-%m-%d") for r in recent_readings]
    chart_kwh = [float(r.consumption_kwh) for r in recent_readings]
    chart_costs = [float(r.estimated_cost or 0) for r in recent_readings]

    # Day of week averages
    dow_totals = {i: [] for i in range(7)}
    for r in readings:
        dow = r.reading_date.weekday()
        dow_totals[dow].append(float(r.consumption_kwh))

    dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    dow_averages = [
        round(sum(dow_totals[i]) / len(dow_totals[i]), 2) if dow_totals[i] else 0.0
        for i in range(7)
    ]

    # Peak reading record
    peak_reading = readings.order_by("-consumption_kwh").first()

    return render(request, "analytics/overview.html", {
        "has_data": True,
        "total_count": total_count,
        "total_kwh": round(agg["total_kwh"] or 0, 2),
        "avg_kwh": round(agg["avg_kwh"] or 0, 2),
        "max_kwh": round(agg["max_kwh"] or 0, 2),
        "min_kwh": round(agg["min_kwh"] or 0, 2),
        "total_cost": round(agg["total_cost"] or 0, 2),
        "peak_reading": peak_reading,
        "chart_dates_json": json.dumps(chart_dates),
        "chart_kwh_json": json.dumps(chart_kwh),
        "chart_costs_json": json.dumps(chart_costs),
        "dow_names_json": json.dumps(dow_names),
        "dow_averages_json": json.dumps(dow_averages),
    })


@login_required
def anomalies_view(request):
    alerts = AnomalyAlert.objects.filter(user=request.user).order_by("-reading_date")
    readings = ElectricityReading.objects.filter(user=request.user).order_by("-reading_date")[:60]
    readings_list = list(reversed(readings))

    chart_dates = [r.reading_date.strftime("%Y-%m-%d") for r in readings_list]
    chart_kwh = [float(r.consumption_kwh) for r in readings_list]

    alert_dates_set = {a.reading_date.strftime("%Y-%m-%d"): float(a.consumption_kwh) for a in alerts}
    anomaly_points = [
        alert_dates_set.get(d, None)
        for d in chart_dates
    ]

    return render(request, "analytics/anomalies.html", {
        "alerts": alerts,
        "total_alerts": alerts.count(),
        "chart_dates_json": json.dumps(chart_dates),
        "chart_kwh_json": json.dumps(chart_kwh),
        "anomaly_points_json": json.dumps(anomaly_points),
    })


@login_required
def run_anomaly_scan(request):
    count = detect_anomalies_for_user(request.user)
    messages.success(request, f"Scan complete! Identified {count} new anomalous reading pattern(s).")
    return redirect("analytics:anomalies")


@login_required
def predict_view(request):
    horizon = int(request.GET.get("horizon", 7))
    model_type = request.GET.get("model", "rf")
    
    result = run_consumption_prediction(request.user, horizon_days=horizon, model_type=model_type)
    
    chart_hist_dates = []
    chart_hist_values = []
    chart_pred_dates = []
    chart_pred_values = []

    if result.get("success"):
        for h in result["historical"]:
            chart_hist_dates.append(h["date"])
            chart_hist_values.append(h["kwh"])
        for f in result["forecasts"]:
            chart_pred_dates.append(f["date"])
            chart_pred_values.append(f["predicted_kwh"])

    return render(request, "analytics/predict.html", {
        "result": result,
        "horizon": horizon,
        "model_type": model_type,
        "chart_hist_dates_json": json.dumps(chart_hist_dates),
        "chart_hist_values_json": json.dumps(chart_hist_values),
        "chart_pred_dates_json": json.dumps(chart_pred_dates),
        "chart_pred_values_json": json.dumps(chart_pred_values),
    })


@login_required
def export_pdf_report(request):
    """Generate an official PowerPulse Electricity Consumption Audit & Forecast PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    elements = []
    styles = getSampleStyleSheet()

    # Title style
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=colors.HexColor("#1e3a8a"),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=15,
    )

    elements.append(Paragraph("PowerPulse — Smart Electricity Audit & ML Forecast", title_style))
    elements.append(Paragraph(f"Generated for: <b>{request.user.username}</b> | Date: <b>{date.today().strftime('%B %d, %Y')}</b>", subtitle_style))
    elements.append(Spacer(1, 10))

    # Summary metrics
    readings = ElectricityReading.objects.filter(user=request.user)
    agg = readings.aggregate(
        total_kwh=Sum("consumption_kwh"),
        avg_kwh=Avg("consumption_kwh"),
        max_kwh=Max("consumption_kwh"),
        total_cost=Sum("estimated_cost")
    )
    alerts_count = AnomalyAlert.objects.filter(user=request.user).count()

    summary_data = [
        ["Metric", "Value", "Metric", "Value"],
        ["Total Readings Logged", str(readings.count()), "Total Energy Consumed", f"{round(agg['total_kwh'] or 0, 1)} kWh"],
        ["Average Daily Load", f"{round(agg['avg_kwh'] or 0, 1)} kWh", "Peak Single-Day Surge", f"{round(agg['max_kwh'] or 0, 1)} kWh"],
        ["Estimated Total Cost", f"₹{round(agg['total_cost'] or 0, 2)}", "Flagged Anomalies", str(alerts_count)],
    ]
    t = Table(summary_data, colWidths=[130, 140, 130, 140])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 15))

    # ML Predictions section
    predictions = PredictionRecord.objects.filter(user=request.user).order_by("target_date")[:7]
    elements.append(Paragraph("<b>Machine Learning 7-Day Forecast & Load Expectations</b>", styles["Heading2"]))
    elements.append(Spacer(1, 6))

    if predictions.exists():
        pred_data = [["Target Date", "Model Used", "Predicted Consumption", "Model RMSE", "Model MAE"]]
        for p in predictions:
            pred_data.append([
                p.target_date.strftime("%a, %b %d %Y"),
                p.model_name,
                f"{p.predicted_kwh} kWh",
                f"{p.model_rmse or 0:.2f}",
                f"{p.model_mae or 0:.2f}"
            ])
        t_pred = Table(pred_data, colWidths=[110, 140, 120, 85, 85])
        t_pred.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#eff6ff"), colors.white]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(t_pred)
    else:
        elements.append(Paragraph("No prediction records generated yet. Run ML Prediction on the portal to populate.", styles["Normal"]))

    elements.append(Spacer(1, 15))

    # Anomalies section
    alerts = AnomalyAlert.objects.filter(user=request.user).order_by("-reading_date")[:6]
    elements.append(Paragraph("<b>Recent Detected Consumption Anomalies</b>", styles["Heading2"]))
    elements.append(Spacer(1, 6))

    if alerts.exists():
        alert_data = [["Date", "Observed kWh", "Anomaly Reason", "Score"]]
        for a in alerts:
            alert_data.append([
                a.reading_date.strftime("%Y-%m-%d"),
                f"{a.consumption_kwh} kWh",
                Paragraph(a.reason, styles["Normal"]),
                f"{a.anomaly_score or 0:.2f}"
            ])
        t_alerts = Table(alert_data, colWidths=[90, 100, 290, 60])
        t_alerts.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dc2626")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#fca5a5")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#fef2f2"), colors.white]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(t_alerts)
    else:
        elements.append(Paragraph("No unusual surges or anomalies recorded.", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="powerpulse_report_{date.today().strftime("%Y%m%d")}.pdf"'
    return response
