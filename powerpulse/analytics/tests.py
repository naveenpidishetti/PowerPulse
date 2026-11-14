from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from energy.models import ElectricityReading
from ml.anomaly_detector import detect_anomalies_for_user
from ml.predictor import run_consumption_prediction


class AnalyticsAndMLTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="analyticsuser", password="password123")
        self.client.login(username="analyticsuser", password="password123")

        # Seed 20 historical readings with one obvious anomaly spike
        base_date = date(2026, 10, 1)
        meter = 5000.0
        for i in range(20):
            d = base_date + timedelta(days=i)
            # Inject spike on day 15
            kwh = 120.0 if i == 15 else (30.0 + (i % 5))
            prev = meter
            curr = meter + kwh
            meter = curr
            ElectricityReading.objects.create(
                user=self.user,
                reading_date=d,
                previous_reading=Decimal(str(prev)),
                current_reading=Decimal(str(curr)),
                consumption_kwh=Decimal(str(kwh)),
                tariff_per_unit=Decimal("8.50"),
                building_name="Campus Alpha"
            )

    def test_overview_view(self):
        response = self.client.get(reverse("analytics:overview"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["has_data"])

    def test_anomalies_detection(self):
        created_count = detect_anomalies_for_user(self.user)
        self.assertGreaterEqual(created_count, 1)
        response = self.client.get(reverse("analytics:anomalies"))
        self.assertEqual(response.status_code, 200)

    def test_predict_view(self):
        result = run_consumption_prediction(self.user, horizon_days=7)
        self.assertTrue(result["success"])
        self.assertEqual(len(result["forecasts"]), 7)
        response = self.client.get(reverse("analytics:predict"))
        self.assertEqual(response.status_code, 200)

    def test_export_pdf(self):
        response = self.client.get(reverse("analytics:export_pdf"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

