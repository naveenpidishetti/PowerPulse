import base64
import csv
from datetime import date, datetime
from decimal import Decimal
import json

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Avg, Max, Min, Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from energy.models import AnomalyAlert, ElectricityReading, MonthlyElectricityBill, PredictionRecord
from ml.anomaly_detector import detect_anomalies_for_user
from ml.predictor import run_consumption_prediction


def get_api_user(request):
    """Resolve user from session, HTTP Basic Auth, or default to admin/demo user."""
    if request.user.is_authenticated:
        return request.user

    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if auth_header.startswith("Basic "):
        try:
            encoded_credentials = auth_header.split(" ", 1)[1].strip()
            decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
            username, password = decoded_credentials.split(":", 1)
            user = authenticate(username=username, password=password)
            if user:
                return user
        except Exception:
            pass

    # Fallback to demo/admin user for smooth testing
    user = User.objects.filter(is_superuser=True).first() or User.objects.first()
    return user


def api_root(request):
    """API Directory with available endpoints and metadata."""
    base_url = request.build_absolute_uri("/api/")
    return JsonResponse({
        "name": "PowerPulse REST API",
        "version": "1.0.0",
        "currency": "INR (₹)",
        "description": "Smart Electricity Consumption Prediction & Anomaly Detection API",
        "documentation_url": request.build_absolute_uri("/api/docs/"),
        "endpoints": {
            "root": base_url,
            "readings": f"{base_url}readings/",
            "readings_upload_csv": f"{base_url}readings/upload-csv/",
            "bills": f"{base_url}bills/",
            "analytics_summary": f"{base_url}analytics/summary/",
            "analytics_forecast": f"{base_url}analytics/forecast/?horizon=7&model=rf",
            "analytics_anomalies": f"{base_url}analytics/anomalies/",
            "analytics_scan": f"{base_url}analytics/scan-anomalies/",
            "interactive_docs": f"{base_url}docs/",
        }
    })


@csrf_exempt
def readings_list_create(request):
    """GET /api/readings/ - List readings; POST /api/readings/ - Record a reading."""
    user = get_api_user(request)
    if not user:
        return JsonResponse({"status": "error", "message": "Authentication required"}, status=401)

    if request.method == "GET":
        qs = ElectricityReading.objects.filter(user=user).order_by("-reading_date")

        building = request.GET.get("building")
        if building:
            qs = qs.filter(building_name__icontains=building)

        start_date = request.GET.get("start_date")
        if start_date:
            qs = qs.filter(reading_date__gte=start_date)

        end_date = request.GET.get("end_date")
        if end_date:
            qs = qs.filter(reading_date__lte=end_date)

        limit = int(request.GET.get("limit", 50))
        offset = int(request.GET.get("offset", 0))
        total_count = qs.count()
        paginated_qs = qs[offset:offset + limit]

        results = []
        for r in paginated_qs:
            results.append({
                "id": r.id,
                "reading_date": r.reading_date.strftime("%Y-%m-%d"),
                "previous_reading": float(r.previous_reading) if r.previous_reading is not None else None,
                "current_reading": float(r.current_reading) if r.current_reading is not None else None,
                "consumption_kwh": float(r.consumption_kwh),
                "tariff_per_unit": float(r.tariff_per_unit) if r.tariff_per_unit is not None else 8.50,
                "estimated_cost": float(r.estimated_cost) if r.estimated_cost is not None else None,
                "currency": "₹",
                "building_name": r.building_name,
                "source": r.get_source_display(),
            })

        return JsonResponse({
            "status": "success",
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "results": results
        })

    elif request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8")) if request.body else request.POST
            raw_date = data.get("reading_date")
            if not raw_date:
                return JsonResponse({"status": "error", "message": "reading_date (YYYY-MM-DD) is required"}, status=400)

            reading_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
            prev_val = data.get("previous_reading")
            curr_val = data.get("current_reading")
            kwh_val = data.get("consumption_kwh")
            tariff_val = data.get("tariff_per_unit", "8.50")
            building_name = data.get("building_name", "Main Residence")

            prev_dec = Decimal(str(prev_val)) if prev_val is not None else None
            curr_dec = Decimal(str(curr_val)) if curr_val is not None else None
            tariff_dec = Decimal(str(tariff_val)) if tariff_val is not None else Decimal("8.50")

            if prev_dec is not None and curr_dec is not None:
                if curr_dec < prev_dec:
                    return JsonResponse({"status": "error", "message": "current_reading cannot be less than previous_reading"}, status=400)
                consumption = curr_dec - prev_dec
            elif kwh_val is not None:
                consumption = Decimal(str(kwh_val))
            else:
                return JsonResponse({"status": "error", "message": "Provide either previous & current reading, or consumption_kwh"}, status=400)

            reading, created = ElectricityReading.objects.update_or_create(
                user=user,
                reading_date=reading_date,
                building_name=building_name,
                defaults={
                    "previous_reading": prev_dec,
                    "current_reading": curr_dec,
                    "consumption_kwh": consumption,
                    "tariff_per_unit": tariff_dec,
                    "source": ElectricityReading.Source.MANUAL,
                }
            )

            # Auto-trigger anomaly detection on update
            detect_anomalies_for_user(user)

            return JsonResponse({
                "status": "success",
                "message": "Reading recorded successfully",
                "created": created,
                "reading": {
                    "id": reading.id,
                    "reading_date": reading.reading_date.strftime("%Y-%m-%d"),
                    "consumption_kwh": float(reading.consumption_kwh),
                    "estimated_cost": float(reading.estimated_cost or 0),
                    "currency": "₹",
                    "building_name": reading.building_name,
                }
            }, status=201 if created else 200)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)


@csrf_exempt
def readings_upload_csv(request):
    """POST /api/readings/upload-csv/ - Ingest bulk meter readings from CSV."""
    user = get_api_user(request)
    if not user:
        return JsonResponse({"status": "error", "message": "Authentication required"}, status=401)

    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST method required with 'csv_file'"}, status=405)

    if "csv_file" not in request.FILES:
        return JsonResponse({"status": "error", "message": "Missing 'csv_file' in form-data payload"}, status=400)

    csv_file = request.FILES["csv_file"]
    try:
        decoded = csv_file.read().decode("utf-8-sig")
        lines = decoded.splitlines()
        reader = csv.DictReader(lines)

        created_count = 0
        error_count = 0

        for row in reader:
            row_clean = {k.strip().lower(): v.strip() for k, v in row.items() if k}
            raw_date = row_clean.get("date") or row_clean.get("reading_date")
            if not raw_date:
                continue

            try:
                parsed_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
            except ValueError:
                try:
                    parsed_date = datetime.strptime(raw_date, "%d-%m-%Y").date()
                except ValueError:
                    error_count += 1
                    continue

            kwh_val = row_clean.get("consumption_kwh") or row_clean.get("kwh") or row_clean.get("units")
            prev_val = row_clean.get("previous_reading")
            curr_val = row_clean.get("current_reading")
            tariff_val = row_clean.get("tariff_per_unit") or row_clean.get("tariff")
            bldg_val = row_clean.get("building_name") or row_clean.get("building") or "Main Residence"

            prev_dec = Decimal(prev_val) if prev_val else None
            curr_dec = Decimal(curr_val) if curr_val else None
            tariff_dec = Decimal(tariff_val) if tariff_val else Decimal("8.50")

            if kwh_val:
                consumption = Decimal(kwh_val)
            elif curr_dec is not None and prev_dec is not None:
                consumption = curr_dec - prev_dec
            else:
                error_count += 1
                continue

            ElectricityReading.objects.update_or_create(
                user=user,
                reading_date=parsed_date,
                building_name=bldg_val,
                defaults={
                    "previous_reading": prev_dec,
                    "current_reading": curr_dec,
                    "consumption_kwh": consumption,
                    "tariff_per_unit": tariff_dec,
                    "source": ElectricityReading.Source.CSV,
                }
            )
            created_count += 1

        anomalies = detect_anomalies_for_user(user)

        return JsonResponse({
            "status": "success",
            "message": f"Successfully ingested {created_count} readings from CSV",
            "created_count": created_count,
            "errors_skipped": error_count,
            "anomalies_detected": anomalies,
        })

    except Exception as e:
        return JsonResponse({"status": "error", "message": f"Failed to parse CSV: {str(e)}"}, status=400)


@csrf_exempt
def bills_list_create(request):
    """GET /api/bills/ - List monthly bills; POST /api/bills/ - Record a bill."""
    user = get_api_user(request)
    if not user:
        return JsonResponse({"status": "error", "message": "Authentication required"}, status=401)

    if request.method == "GET":
        bills = MonthlyElectricityBill.objects.filter(user=user).order_by("-billing_month")
        results = []
        for b in bills:
            results.append({
                "id": b.id,
                "billing_month": b.billing_month.strftime("%Y-%m-%d"),
                "billing_month_label": b.billing_month.strftime("%B %Y"),
                "units_consumed": float(b.units_consumed),
                "bill_amount": float(b.bill_amount),
                "cost_per_unit": float(b.cost_per_unit) if b.cost_per_unit else None,
                "currency": "₹",
            })
        return JsonResponse({"status": "success", "count": len(results), "results": results})

    elif request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8")) if request.body else request.POST
            raw_month = data.get("billing_month")
            if not raw_month:
                return JsonResponse({"status": "error", "message": "billing_month (YYYY-MM-DD) is required"}, status=400)

            b_date = datetime.strptime(raw_month, "%Y-%m-%d").date().replace(day=1)
            units = Decimal(str(data.get("units_consumed", 0)))
            amount = Decimal(str(data.get("bill_amount", 0)))

            bill, created = MonthlyElectricityBill.objects.update_or_create(
                user=user,
                billing_month=b_date,
                defaults={
                    "units_consumed": units,
                    "bill_amount": amount,
                }
            )
            return JsonResponse({
                "status": "success",
                "message": "Monthly bill recorded",
                "bill": {
                    "id": bill.id,
                    "billing_month": bill.billing_month.strftime("%Y-%m-%d"),
                    "units_consumed": float(bill.units_consumed),
                    "bill_amount": float(bill.bill_amount),
                    "cost_per_unit": float(bill.cost_per_unit) if bill.cost_per_unit else None,
                    "currency": "₹",
                }
            }, status=201 if created else 200)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)


def analytics_summary(request):
    """GET /api/analytics/summary/ - KPI metrics summary."""
    user = get_api_user(request)
    if not user:
        return JsonResponse({"status": "error", "message": "Authentication required"}, status=401)

    readings = ElectricityReading.objects.filter(user=user)
    count = readings.count()
    if count == 0:
        return JsonResponse({"status": "success", "has_data": False, "count": 0})

    agg = readings.aggregate(
        total_kwh=Sum("consumption_kwh"),
        avg_kwh=Avg("consumption_kwh"),
        max_kwh=Max("consumption_kwh"),
        min_kwh=Min("consumption_kwh"),
        total_cost=Sum("estimated_cost")
    )
    anomaly_count = AnomalyAlert.objects.filter(user=user).count()

    return JsonResponse({
        "status": "success",
        "has_data": True,
        "total_readings": count,
        "total_consumption_kwh": round(float(agg["total_kwh"] or 0), 2),
        "average_daily_kwh": round(float(agg["avg_kwh"] or 0), 2),
        "peak_draw_kwh": round(float(agg["max_kwh"] or 0), 2),
        "min_draw_kwh": round(float(agg["min_kwh"] or 0), 2),
        "total_cost": round(float(agg["total_cost"] or 0), 2),
        "currency": "₹",
        "anomaly_alerts_count": anomaly_count,
    })


def analytics_forecast(request):
    """GET /api/analytics/forecast/ - Multi-step machine learning forecast."""
    user = get_api_user(request)
    if not user:
        return JsonResponse({"status": "error", "message": "Authentication required"}, status=401)

    horizon = int(request.GET.get("horizon", 7))
    model_type = request.GET.get("model", "rf")
    result = run_consumption_prediction(user, horizon_days=horizon, model_type=model_type)

    if not result.get("success"):
        return JsonResponse({
            "status": "error",
            "message": result.get("error", "Unable to compute forecast")
        }, status=400)

    return JsonResponse({
        "status": "success",
        "model_name": result.get("model_name"),
        "model_type": model_type,
        "horizon_days": horizon,
        "rmse": result.get("rmse"),
        "mae": result.get("mae"),
        "currency": "₹",
        "forecasts": result.get("forecasts", []),
    })


def analytics_anomalies(request):
    """GET /api/analytics/anomalies/ - List detected anomalies."""
    user = get_api_user(request)
    if not user:
        return JsonResponse({"status": "error", "message": "Authentication required"}, status=401)

    alerts = AnomalyAlert.objects.filter(user=user).order_by("-reading_date")
    results = []
    for a in alerts:
        results.append({
            "id": a.id,
            "reading_date": a.reading_date.strftime("%Y-%m-%d"),
            "consumption_kwh": float(a.consumption_kwh),
            "anomaly_score": float(a.anomaly_score) if a.anomaly_score is not None else None,
            "reason": a.reason,
            "created_at": a.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        })

    return JsonResponse({
        "status": "success",
        "total_anomalies": len(results),
        "results": results
    })


@csrf_exempt
def analytics_scan(request):
    """POST /api/analytics/scan-anomalies/ - Trigger anomaly detection scan."""
    user = get_api_user(request)
    if not user:
        return JsonResponse({"status": "error", "message": "Authentication required"}, status=401)

    anomalies_found = detect_anomalies_for_user(user)
    return JsonResponse({
        "status": "success",
        "message": f"Anomaly detection scan completed. Identified {anomalies_found} anomalous pattern(s).",
        "anomalies_detected": anomalies_found,
    })


def api_docs_view(request):
    """Render interactive API documentation & testing console."""
    return render(request, "api/docs.html", {
        "title": "PowerPulse REST API Documentation",
    })
