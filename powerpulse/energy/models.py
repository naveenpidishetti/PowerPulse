from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class ElectricityReading(models.Model):
    """One electricity consumption reading belonging to one user."""

    class Source(models.TextChoices):
        MANUAL = "manual", "Manual entry"
        CSV = "csv", "CSV upload"
        DEMO = "demo", "Demonstration data"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="readings"
    )
    reading_date = models.DateField()
    previous_reading = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )
    current_reading = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )
    consumption_kwh = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        help_text="Units (kWh) consumed.",
    )
    tariff_per_unit = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )
    estimated_cost = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    building_name = models.CharField(max_length=100, blank=True)
    source = models.CharField(
        max_length=10, choices=Source.choices, default=Source.MANUAL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-reading_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "reading_date", "building_name"],
                name="unique_reading_per_user_date_building",
            )
        ]
        indexes = [models.Index(fields=["user", "reading_date"])]

    def __str__(self):
        return f"{self.user} | {self.reading_date} | {self.consumption_kwh} kWh"

    def clean(self):
        if self.previous_reading is not None and self.current_reading is not None:
            if self.current_reading < self.previous_reading:
                raise ValidationError(
                    "Current meter reading cannot be lower than the previous reading."
                )

    def calculate(self):
        """Consumption = current - previous; cost = consumption x tariff."""
        if self.previous_reading is not None and self.current_reading is not None:
            self.consumption_kwh = self.current_reading - self.previous_reading
        if self.tariff_per_unit is not None and self.consumption_kwh is not None:
            self.estimated_cost = (
                Decimal(self.consumption_kwh) * Decimal(self.tariff_per_unit)
            ).quantize(Decimal("0.01"))
        else:
            self.estimated_cost = None

    def save(self, *args, **kwargs):
        self.calculate()
        super().save(*args, **kwargs)


class MonthlyElectricityBill(models.Model):
    """A monthly electricity bill entered by the user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bills"
    )
    billing_month = models.DateField(help_text="Stored as the first day of the month.")
    units_consumed = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    bill_amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-billing_month"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "billing_month"], name="unique_bill_per_user_month"
            )
        ]

    def __str__(self):
        return f"{self.user} | {self.billing_month:%b %Y} | {self.bill_amount}"

    @property
    def cost_per_unit(self):
        if self.units_consumed and self.units_consumed > 0:
            return (self.bill_amount / self.units_consumed).quantize(Decimal("0.01"))
        return None

    def save(self, *args, **kwargs):
        self.billing_month = self.billing_month.replace(day=1)
        super().save(*args, **kwargs)


class AnomalyAlert(models.Model):
    """A reading flagged as potentially unusual by the anomaly detector.
    This is a statistical flag only, not proof of an electrical fault."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="anomaly_alerts"
    )
    reading = models.ForeignKey(
        ElectricityReading, on_delete=models.CASCADE, null=True, blank=True,
        related_name="alerts",
    )
    reading_date = models.DateField()
    consumption_kwh = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=255)
    anomaly_score = models.FloatField(null=True, blank=True)
    detected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-reading_date"]

    def __str__(self):
        return f"Possible anomaly: {self.user} | {self.reading_date}"


class PredictionRecord(models.Model):
    """A saved forecast together with its evaluation metrics."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="predictions"
    )
    target_date = models.DateField()
    predicted_kwh = models.DecimalField(max_digits=12, decimal_places=2)
    model_name = models.CharField(max_length=50)
    baseline_mae = models.FloatField(null=True, blank=True)
    model_mae = models.FloatField(null=True, blank=True)
    model_rmse = models.FloatField(null=True, blank=True)
    train_size = models.PositiveIntegerField(default=0)
    test_size = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} | {self.target_date} | {self.predicted_kwh} kWh"
