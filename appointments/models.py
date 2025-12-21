from enum import Enum
from django.db import models

class StatusAppointment(Enum):
    SHOW = 'SHOW', 'Asistida'
    NO_SHOW = 'NO_SHOW', 'No Asistida'
    SCHEDULED = 'SCHEDULED', 'Programada'
    COMPLETED = 'COMPLETED', 'Completada'
    RESCHEDULED = 'RESCHEDULED', 'Reprogramada'
    CLOSED = 'CLOSED', 'Cerrada'
    CANCELLED = 'CANCELLED', 'Cancelada'
    

class Appointment(models.Model):
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE)
    service = models.ForeignKey('sales.Service', on_delete=models.CASCADE)
    operator = models.ForeignKey('sales.Operator', on_delete=models.SET_NULL, null=True, blank=True)
    scheduled_datetime = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=[(tag.value[0], tag.value[1]) for tag in StatusAppointment],
        default=StatusAppointment.SCHEDULED.value[0]
    )
    scheduled_message_client = models.ForeignKey(
        'notifications_scheduler.ClientScheduledMessage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client} - {self.service} at {self.scheduled_datetime}"
