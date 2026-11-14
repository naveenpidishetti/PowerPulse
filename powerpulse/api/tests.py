import json
from datetime import date
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from energy.models import ElectricityReading, MonthlyElectricityBill


class APITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="apiuser", password="password123")
        self.client.login(username="apiuser", password="password123")

        # Seed initial reading
        self.reading = ElectricityReading.objects.create(
            user=self.user,
            reading_date=date(2026, 11, 1),
            previous_reading=Decimal("1000.00"),
            current_reading=Decimal("1040.00"),
            consumption_kwh=Decimal("40.00"),
            tariff_per_unit=Decimal("8.50"),
            building_name="Campus Beta"
        )

    def test_api_root(self):
        res = self.client.get(reverse("api:root"))
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["version"], "1.0.0")
        self.assertIn("readings", data["endpoints"])

    def test_readings_list(self):
        res = self.client.get(reverse("api:readings_list_create"))
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["total_count"], 1)
        self.assertEqual(data["results"][0]["consumption_kwh"], 40.0)

    def test_readings_create(self):
        payload = {
            "reading_date": "2026-11-02",
            "previous_reading": 1040.00,
            "current_reading": 1085.50,
            "tariff_per_unit": 8.50,
            "building_name": "Campus Beta"
        }
        res = self.client.post(
            reverse("api:readings_list_create"),
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["reading"]["consumption_kwh"], 45.5)

    def test_bills_list_and_create(self):
        payload = {
            "billing_month": "2026-10-01",
            "units_consumed": 500,
            "bill_amount": 4250
        }
        res_post = self.client.post(
            reverse("api:bills_list_create"),
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(res_post.status_code, 201)

        res_get = self.client.get(reverse("api:bills_list_create"))
        self.assertEqual(res_get.status_code, 200)
        data = res_get.json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["cost_per_unit"], 8.5)

    def test_analytics_summary(self):
        res = self.client.get(reverse("api:analytics_summary"))
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["has_data"])
        self.assertEqual(data["currency"], "₹")
        self.assertEqual(data["total_consumption_kwh"], 40.0)

    def test_docs_page(self):
        res = self.client.get(reverse("api:docs"))
        self.assertEqual(res.status_code, 200)
