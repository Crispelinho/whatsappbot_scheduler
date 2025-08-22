from celery import shared_task
from django.core.management import call_command
from django.utils import timezone

from notifications_scheduler.senders.base import MessageSendResult
from .models import ClientScheduledMessage, ResponseCode, MessageResponse, ResponseCode
from .senders.whatsapp_sender import WhatsAppSeleniumSender

@shared_task
def send_scheduled_messages_task():
    print("Celery está ejecutando la tarea de envío programado")
    call_command('send_scheduled_messages')

RETRYABLE_ERRORS = ["NETWORK", "TIMEOUT", "WHATSAPP_DOWN", "RATE_LIMIT"]

def update_message_status(resp: MessageResponse, success: bool, message_send_result: MessageSendResult):
    if success:
        resp.status = MessageResponse.Status.SENT
        resp.response_code = ResponseCode.SUCCESS.value
        resp.description = message_send_result.message or "Sent successfully"
    else:
        resp.status = MessageResponse.Status.FAILED
        resp.response_code = message_send_result.error_code
        resp.description = message_send_result.message
    resp.save(update_fields=["status", "response_code", "description"])

def process_failed_message(msg):

    msg.retry_count += 1
    msg.last_retry_at = timezone.now()
    msg.save(update_fields=["retry_count", "last_retry_at"])

    success, message_send_result = WhatsAppSeleniumSender.send_message(
        msg.client.phone_number,
        msg.scheduled_message.message_text,
        msg.scheduled_message.image.path if msg.scheduled_message.image else None,
        msg.scheduled_message.video.path if msg.scheduled_message.video else None
    )

    update_message_status(msg.response, success, message_send_result)
    msg.save()

@shared_task
def retry_failed_messages():
    
    # Filtramos los mensajes que tienen respuesta fallida con response_code retryable
    failed_messages = ClientScheduledMessage.objects.filter(
        response__status="failed",
        response__response_code__in=RETRYABLE_ERRORS
    )

    for msg in failed_messages:
        if msg.can_retry:
            # Aquí llamamos a tu función de reenvío / procesamiento
            process_failed_message(msg)
        else:
            print(f"Message {msg.id} cannot be retried due to max retries or non-retryable error.")
