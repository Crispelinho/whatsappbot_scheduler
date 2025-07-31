from django.db import models

class Appointment(models.Model):
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE)
    service = models.ForeignKey('sales.Service', on_delete=models.CASCADE)
    operator = models.ForeignKey('sales.Operator', on_delete=models.SET_NULL, null=True, blank=True)
    scheduled_datetime = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('scheduled', 'Scheduled'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
            ('no_show', 'No Show'),
        ],
        default='scheduled'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client} - {self.service} at {self.scheduled_datetime}"
