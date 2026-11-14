import csv
from datetime import date, datetime, timedelta
from decimal import Decimal
import io
import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from ml.anomaly_detector import detect_anomalies_for_user
from ml.predictor import run_consumption_prediction
from .forms import CSVUploadForm, ElectricityReadingForm, MonthlyBillForm
from .models import AnomalyAlert, ElectricityReading, MonthlyElectricityBill, PredictionRecord


@login_required
def reading_list_view(request):
    readings = ElectricityReading.objects.filter(user=request.user).order_by("-reading_date")
    
    # Optional search / filter
    building = request.GET.get("building")
    if building:
        readings = readings.filter(building_name__icontains=building)
    
    start_date = request.GET.get("start_date")
    if start_date:
        readings = readings.filter(reading_date__gte=start_date)

    end_date = request.GET.get("end_date")
    if end_date:
        readings = readings.filter(reading_date__lte=end_date)

    # Unique buildings for filter dropdown
    buildings = ElectricityReading.objects.filter(user=request.user).values_list("building_name", flat=True).distinct()

    paginator = Paginator(readings, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "energy/reading_list.html", {
        "page_obj": page_obj,
        "total_count": readings.count(),
        "buildings": [b for b in buildings if b],
        "selected_building": building or "",
        "start_date": start_date or "",
        "end_date": end_date or "",
    })


@login_required
def reading_create_view(request):
    if request.method == "POST":
        form = ElectricityReadingForm(request.POST)
        if form.is_valid():
            reading = form.save(commit=False)
            reading.user = request.user
            reading.source = ElectricityReading.Source.MANUAL
            reading.save()
            
            # Check for anomalies
            detect_anomalies_for_user(request.user)
            messages.success(request, f"Reading for {reading.reading_date} ({reading.consumption_kwh} kWh) logged successfully!")
            return redirect("energy:reading_list")
        else:
            messages.error(request, "Please check the form inputs.")
    else:
        initial_date = date.today().strftime("%Y-%m-%d")
        last_reading = ElectricityReading.objects.filter(user=request.user).order_by("-reading_date").first()
        initial = {"reading_date": initial_date}
        if last_reading and last_reading.current_reading:
            initial["previous_reading"] = last_reading.current_reading
            initial["tariff_per_unit"] = last_reading.tariff_per_unit
            initial["building_name"] = last_reading.building_name
        form = ElectricityReadingForm(initial=initial)

    return render(request, "energy/reading_form.html", {"form": form, "title": "Log Electricity Reading"})


@login_required
def reading_delete_view(request, pk):
    reading = get_object_or_404(ElectricityReading, pk=pk, user=request.user)
    if request.method == "POST":
        reading.delete()
        messages.success(request, "Reading record deleted successfully.")
        return redirect("energy:reading_list")
    return render(request, "energy/confirm_delete.html", {"object": reading, "type": "Reading"})


@login_required
def reading_upload_csv_view(request):
    if request.method == "POST":
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES["csv_file"]
            try:
                decoded_file = csv_file.read().decode("utf-8-sig")
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string)
                
                created_count = 0
                errors = 0
                for row in reader:
                    # Normalize keys
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
                            errors += 1
                            continue

                    kwh_val = row_clean.get("consumption_kwh") or row_clean.get("kwh") or row_clean.get("units")
                    prev_val = row_clean.get("previous_reading")
                    curr_val = row_clean.get("current_reading")
                    tariff_val = row_clean.get("tariff_per_unit") or row_clean.get("tariff")
                    bldg_val = row_clean.get("building_name") or row_clean.get("building") or "Main"

                    prev_dec = Decimal(prev_val) if prev_val else None
                    curr_dec = Decimal(curr_val) if curr_val else None
                    tariff_dec = Decimal(tariff_val) if tariff_val else Decimal("8.50")

                    if kwh_val:
                        consumption = Decimal(kwh_val)
                    elif curr_dec is not None and prev_dec is not None:
                        consumption = curr_dec - prev_dec
                    else:
                        errors += 1
                        continue

                    ElectricityReading.objects.update_or_create(
                        user=request.user,
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

                detect_anomalies_for_user(request.user)
                messages.success(request, f"Successfully processed {created_count} readings from CSV! ({errors} skipped/errors)")
                return redirect("energy:reading_list")
            except Exception as e:
                messages.error(request, f"Error parsing CSV file: {str(e)}")
    else:
        form = CSVUploadForm()

    return render(request, "energy/upload_csv.html", {"form": form})


@login_required
def download_sample_csv_view(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="powerpulse_sample_template.csv"'
    
    writer = csv.writer(response)
    writer.writerow(["reading_date", "previous_reading", "current_reading", "consumption_kwh", "tariff_per_unit", "building_name"])
    
    today = date.today()
    base_reading = 12000.0
    for i in range(14, 0, -1):
        d = today - timedelta(days=i)
        prev = base_reading
        kwh = round(random.uniform(25.0, 48.0), 2)
        curr = prev + kwh
        base_reading = curr
        writer.writerow([d.strftime("%Y-%m-%d"), round(prev, 2), round(curr, 2), kwh, "8.50", "Main Residence"])
        
    return response


@login_required
def bill_list_view(request):
    bills = MonthlyElectricityBill.objects.filter(user=request.user).order_by("-billing_month")
    return render(request, "energy/bill_list.html", {"bills": bills})


@login_required
def bill_create_view(request):
    if request.method == "POST":
        form = MonthlyBillForm(request.POST)
        if form.is_valid():
            bill = form.save(commit=False)
            bill.user = request.user
            bill.save()
            messages.success(request, f"Monthly bill for {bill.billing_month:%B %Y} recorded.")
            return redirect("energy:bill_list")
        else:
            messages.error(request, "Please check the form inputs.")
    else:
        form = MonthlyBillForm(initial={"billing_month": date.today().replace(day=1).strftime("%Y-%m-%d")})
    return render(request, "energy/bill_form.html", {"form": form, "title": "Record Monthly Bill"})


@login_required
def bill_delete_view(request, pk):
    bill = get_object_or_404(MonthlyElectricityBill, pk=pk, user=request.user)
    if request.method == "POST":
        bill.delete()
        messages.success(request, "Monthly bill record deleted.")
        return redirect("energy:bill_list")
    return render(request, "energy/confirm_delete.html", {"object": bill, "type": "Monthly Bill"})


@login_required
def seed_demo_data_view(request):
    """Generates realistic 90 days of daily readings and triggers ML models."""
    user = request.user
    today = date.today()

    # Clear old demo readings if any
    ElectricityReading.objects.filter(user=user, source=ElectricityReading.Source.DEMO).delete()

    meter = 15400.00
    tariff = Decimal("8.50")
    created_count = 0

    # Generate 90 days of synthetic data
    for i in range(90, 0, -1):
        day_date = today - timedelta(days=i)
        is_weekend = day_date.weekday() in [5, 6]

        # Base daily usage (higher on weekends, slightly higher in summer/warmer months)
        base = 32.0 if not is_weekend else 42.0
        noise = random.uniform(-4.5, 5.0)
        kwh = round(base + noise, 2)

        # Inject realistic anomalies:
        # Day 65: AC compressor stuck on (surge)
        if i == 65:
            kwh = 88.40
        # Day 28: EV fast-charging overnight test (spike)
        elif i == 28:
            kwh = 96.20
        # Day 12: House empty for holiday weekend (unusually low)
        elif i == 12:
            kwh = 7.10

        prev_reading = Decimal(str(round(meter, 2)))
        curr_reading = Decimal(str(round(meter + kwh, 2)))
        meter += kwh

        ElectricityReading.objects.create(
            user=user,
            reading_date=day_date,
            previous_reading=prev_reading,
            current_reading=curr_reading,
            consumption_kwh=Decimal(str(kwh)),
            tariff_per_unit=tariff,
            building_name="HQ & Main Campus",
            source=ElectricityReading.Source.DEMO,
        )
        created_count += 1

    # Seed 3 monthly bills
    MonthlyElectricityBill.objects.filter(user=user).delete()
    for month_offset in [1, 2, 3]:
        # First day of that month
        m_date = (today.replace(day=1) - timedelta(days=28 * month_offset)).replace(day=1)
        units = Decimal(str(random.randint(950, 1250)))
        bill_amt = (units * tariff).quantize(Decimal("0.01"))
        MonthlyElectricityBill.objects.create(
            user=user,
            billing_month=m_date,
            units_consumed=units,
            bill_amount=bill_amt
        )

    # Trigger ML Models
    anomalies_found = detect_anomalies_for_user(user)
    prediction_result = run_consumption_prediction(user, horizon_days=7)

    messages.success(
        request,
        f"Seeded {created_count} historical readings! Detected {anomalies_found} anomalies and trained ML forecast model."
    )
    return redirect("core:dashboard")
