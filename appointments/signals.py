from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Appointment
from notifications_scheduler.models import ClientScheduledMessage, MessageResponse, ScheduledMessage, ScheduledMessageType
from django.utils import timezone

# Constante para el asunto de recordatorio de cita
APPOINTMENT_REMINDER_SUBJECT = "Recordatorio de Cita Programada"

@receiver(post_save, sender=Appointment)
def create_scheduled_message_for_appointment(sender, instance, created, **kwargs):
    print("XXXXXXXXXXXXXXXXXXXXXXXXx")
    print("Appointment post_save signal triggered for Appointment ID:", instance.id)
    # Evitar bucle infinito usando un flag en kwargs
    if getattr(instance, "_signal_skip", False):
        print("Signal skip flag detected, exiting signal handler.")
        return

    # Solo crear/actualizar recordatorio si la cita no está vencida (usando zona horaria de Colombia)
    import pytz
    colombia_tz = pytz.timezone("America/Bogota")
    now_colombia = timezone.now().astimezone(colombia_tz)
    if instance.scheduled_datetime < now_colombia:
        print("Appointment is in the past, no scheduled message will be created.")
        return
    print("Creating or updating scheduled message for Appointment ID:", instance.id)
    # Usar un asunto fijo para todos los recordatorios de cita
    subject = APPOINTMENT_REMINDER_SUBJECT
    message_text = "Estimado/a {client_name}, tiene una cita para {service_name} el día {appointment_datetime}."
    print("ScheduledMessageType:", ScheduledMessageType.REMINDER.value[0])
    scheduled_message, _ = ScheduledMessage.objects.get_or_create(
        subject=subject,
        defaults={
            "message_text": message_text,
            "replace_text_message_variables": True,
            "status": "active",
            "scheduled_message_type": ScheduledMessageType.REMINDER.value[0]
        }
    )
    print("ScheduledMessage ID:", scheduled_message.id)
    client_msg, _ = ClientScheduledMessage.objects.update_or_create(
        scheduled_message=scheduled_message,
        client=instance.client
    )
    MessageResponse.objects.update_or_create(
        client_message=client_msg,
        defaults={"status": MessageResponse.Status.PENDING}
    )
    if instance.scheduled_message_client != client_msg:
        instance.scheduled_message_client = client_msg
        # Usar un atributo temporal para evitar el bucle de señales
        instance._signal_skip = True
        instance.save(update_fields=["scheduled_message_client"])
        del instance._signal_skip