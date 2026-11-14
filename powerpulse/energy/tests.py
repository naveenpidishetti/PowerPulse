from datetime import date
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase, Client
from django.urls import reverse

from energy.models import ElectricityReading, MonthlyElectricityBill


class EnergyModelAndViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="energyuser", password="password123")
        self.client.login(username="energyuser", password="password123")

    def test_reading_calculation(self):
        reading = ElectricityReading(
            user=self.user,
            reading_date=date(2026, 11, 1),
            previous_reading=Decimal("1000.00"),
            current_reading=Decimal("1050.50"),
            tariff_per_unit=Decimal("10.00"),
            consumption_kwh=Decimal("0.00")
        )
        reading.save()
        self.assertEqual(reading.consumption_kwh, Decimal("50.50"))
        self.assertEqual(reading.estimated_cost, Decimal("505.00"))

    def test_invalid_reading_validation(self):
        reading = ElectricityReading(
            user=self.user,
            reading_date=date(2026, 11, 1),
            previous_reading=Decimal("1050.00"),
            current_reading=Decimal("1000.00"),
            consumption_kwh=Decimal("0.00")
        )
        with self.assertRaises(ValidationError):
            reading.clean()

    def test_monthly_bill_cost_per_unit(self):
        bill = MonthlyElectricityBill(
            user=self.user,
            billing_month=date(2026, 10, 15),
            units_consumed=Decimal("500.00"),
            bill_amount=Decimal("4250.00")
        )
        bill.save()
        self.assertEqual(bill.billing_month, date(2026, 10, 1))
        self.assertEqual(bill.cost_per_unit, Decimal("8.50"))

    def test_reading_list_view(self):
        response = self.client.get(reverse("energy:reading_list"))
        self.assertEqual(response.status_code, 200)

    def test_create_reading_view(self):
        response = self.client.post(reverse("energy:reading_create"), {
            "reading_date": "2026-11-02",
            "previous_reading": "2000.00",
            "current_reading": "2045.00",
            "tariff_per_unit": "8.50",
            "building_name": "Test Site"
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ElectricityReading.objects.filter(building_name="Test Site").exists())

    def test_download_sample_csv(self):
        response = self.client.get(reverse("energy:download_sample_csv"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")

