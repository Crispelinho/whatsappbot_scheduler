from celery import shared_task
from django.core.management import call_command
from django.utils import timezone
from .models import ClientScheduledMessage
from .management.commands.send_scheduled_messages import SeleniumWhatsAppSender

whatsapp_sender = SeleniumWhatsAppSender()

@shared_task
def send_scheduled_messages_task():
    print("Celery está ejecutando la tarea de envío programado")
    call_command('send_scheduled_messages')



@shared_task
def retry_failed_messages():
    failed_messages = ClientScheduledMessage.objects.filter(send_status="FAILED")
    for msg in failed_messages:
        if msg.can_retry():
            msg.retry_count += 1
            msg.last_retry_at = timezone.now()
            msg.save(update_fields=["retry_count", "last_retry_at"])

            success, response = whatsapp_sender.send_message(
                msg.client.phone_number,
                msg.scheduled_message.message_text,
                msg.scheduled_message.image.path if msg.scheduled_message.image else None,
                msg.scheduled_message.video.path if msg.scheduled_message.video else None
            )

            if success:
                msg.send_status = "SENT"
                msg.error_type = None
                msg.save(update_fields=["send_status", "error_type"])
        else:
            print(f"Message {msg.id} cannot be retried due to max retries or non-retryable error.")
            msg.send_status = "FAILED"
            msg.error_type = msg.error_type if msg.error_type else None
            msg.save(update_fields=["send_status"])

