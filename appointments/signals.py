from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Appointment
from notifications_scheduler.models import ClientScheduledMessage, MessageResponse, ScheduledMessage, ClientMessage

@receiver(post_save, sender=Appointment)
def create_scheduled_message_for_appointment(sender, instance, created, **kwargs):
    if created:
        scheduled_message = ScheduledMessage.objects.create(
            subject=f"Recordatorio de cita para {instance.client}",
            message_text=f"Estimado/a {instance.client}, tiene una cita para {instance.service} el día {instance.scheduled_datetime:%d/%m/%Y a las %H:%M}.",
            start_datetime=instance.scheduled_datetime,
            status='active'
        )
        # Crear ClientScheduledMessage para cada cliente asociado a la cita
        client_msg = ClientScheduledMessage.objects.create(
            scheduled_message=scheduled_message,
            client=instance.client
        )
        MessageResponse.objects.create(
            client_message=client_msg,
            status=MessageResponse.Status.PENDING
        )
