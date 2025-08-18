from celery import shared_task
from django.core.management import call_command
from django.utils import timezone
from .models import ClientScheduledMessage, ErrorCode, MessageResponse, ErrorType
from .senders.whatsapp_sender import WhatsAppSeleniumSender

SocialNetworkSender = WhatsAppSeleniumSender()

@shared_task
def send_scheduled_messages_task():
    """Enqueue the task to send scheduled WhatsApp messages."""
    print("Celery está ejecutando la tarea de envío programado")
    call_command('send_scheduled_messages')

RETRYABLE_ERRORS = ["NETWORK", "TIMEOUT", "WHATSAPP_DOWN"]

def update_message_status(resp: MessageResponse, result: MessageResponse):
    """Actualiza el estado de la respuesta del mensaje basado en el resultado del envío."""
    if result.success:
        resp.status = MessageResponse.Status.SENT
        resp.error_type = None
    else:
        resp.status = MessageResponse.Status.FAILED
        error_enum = result.error_code if result.error_code in ErrorCode._value2member_map_ else ErrorCode.UNKNOWN
        error_type_obj = ErrorType.objects.filter(code=error_enum.value).first()
        if not error_type_obj:
            error_type_obj, _ = ErrorType.objects.get_or_create(
                code=ErrorCode.UNKNOWN.value,
                defaults={"name": "Unknown Error", "description": result.message}
            )
        resp.error_type = error_type_obj
    resp.save(update_fields=["status", "error_type"])

def process_failed_message(msg: ClientScheduledMessage):
    """Procesa un mensaje fallido, reintentando el envío si es posible."""
    msg.retry_count += 1
    msg.last_retry_at = timezone.now()
    msg.save(update_fields=["retry_count", "last_retry_at"])

    result = SocialNetworkSender.send_message(
        msg.client.area_code if hasattr(msg.client, 'area_code') else "",
        msg.client.phone_number,
        msg.scheduled_message.message_text,
        msg.scheduled_message.image.path if msg.scheduled_message.image else None,
        msg.scheduled_message.video.path if msg.scheduled_message.video else None
    )
    update_message_status(msg.response, result)
    msg.save()

@shared_task
def retry_failed_messages():
    """Reintenta el envío de mensajes fallidos que son retryables."""
    # Filtramos los mensajes que tienen respuesta fallida con errores retryables
    failed_messages = ClientScheduledMessage.objects.filter(
        response__status="failed",
        response__error_type__code__in=RETRYABLE_ERRORS
    )

    for msg in failed_messages:
        if msg.can_retry:
            # Aquí llamamos a tu función de reenvío / procesamiento
            process_failed_message(msg)
        else:
            print(f"Message {msg.id} cannot be retried due to max retries or non-retryable error.")
