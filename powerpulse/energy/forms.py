from django import forms
from .models import ElectricityReading, MonthlyElectricityBill


class ElectricityReadingForm(forms.ModelForm):
    class Meta:
        model = ElectricityReading
        fields = [
            "reading_date",
            "previous_reading",
            "current_reading",
            "consumption_kwh",
            "tariff_per_unit",
            "building_name",
        ]
        widgets = {
            "reading_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "previous_reading": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "e.g. 1420.50"}),
            "current_reading": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "e.g. 1465.80"}),
            "consumption_kwh": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Or enter net kWh directly"}),
            "tariff_per_unit": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "e.g. 8.50 (₹/kWh)"}),
            "building_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Main Residence, Building A"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["consumption_kwh"].required = False

    def clean(self):
        cleaned_data = super().clean()
        prev = cleaned_data.get("previous_reading")
        curr = cleaned_data.get("current_reading")
        kwh = cleaned_data.get("consumption_kwh")

        if prev is not None and curr is not None:
            if curr < prev:
                raise forms.ValidationError("Current meter reading cannot be lower than previous reading.")
            cleaned_data["consumption_kwh"] = curr - prev
        elif kwh is None:
            raise forms.ValidationError("Please provide either Previous & Current readings, or enter Net Consumption (kWh).")

        return cleaned_data


class MonthlyBillForm(forms.ModelForm):
    class Meta:
        model = MonthlyElectricityBill
        fields = ["billing_month", "units_consumed", "bill_amount"]
        widgets = {
            "billing_month": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "units_consumed": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Total units (kWh)"}),
            "bill_amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Total amount in ₹"}),
        }


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="Select Electricity Readings CSV File",
        widget=forms.FileInput(attrs={"class": "form-control", "accept": ".csv"}),
        help_text="Expected headers: reading_date, consumption_kwh (or current_reading, previous_reading), tariff_per_unit (optional), building_name (optional)"
    )
