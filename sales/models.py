# sales/models.py
from django.db import models
from clients.models import Client

class Operator(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2)  # e.g. 0.60 = 60%

    def __str__(self):
        return self.name

class ServiceType(models.Model):
    name = models.CharField(max_length=100)
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2)  # e.g. 0.60 = 60%

    def __str__(self):
        return self.name

class Service(models.Model):
    name = models.CharField(max_length=100)
    service_type = models.ForeignKey(ServiceType, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes = models.IntegerField(help_text="Approximate duration in minutes")

    def __str__(self):
        return f"{self.name} ({self.service_type})"

class SaleRecord(models.Model):
    date = models.DateField()
    month = models.IntegerField()
    year = models.IntegerField()
    month_year = models.CharField(max_length=20)
    week = models.IntegerField()

    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True)
    operator = models.ForeignKey(Operator, on_delete=models.SET_NULL, null=True)

    quantity = models.IntegerField()
    service_discount = models.DecimalField(max_digits=10, decimal_places=2)
    service_price = models.DecimalField(max_digits=10, decimal_places=2)
    adjustment = models.DecimalField(max_digits=10, decimal_places=2)
    total_service = models.DecimalField(max_digits=10, decimal_places=2)

    salon_discount = models.DecimalField(max_digits=10, decimal_places=2)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.CharField(max_length=10)  # Yes / No or amount

    payment_method = models.CharField(max_length=50)
    notes = models.TextField(blank=True, null=True)
    errors = models.TextField(blank=True, null=True)

    worker_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    settled = models.BooleanField(default=False)

    settled_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_to_pay = models.DecimalField(max_digits=10, decimal_places=2)
    net_weekly_payment = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.date} - {self.service} - {self.client}"
