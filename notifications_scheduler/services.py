from django.utils import timezone
from notifications_scheduler.models import ClientScheduledMessage, ErrorType
from .management.commands.send_scheduled_messages import SeleniumWhatsAppSender, WhatsAppSenderInterface

whatsapp_sender = SeleniumWhatsAppSender()  # instancia global para reutilizar sesión

def send_message_to_client(client_msg: ClientScheduledMessage, whatsapp_sender: WhatsAppSenderInterface) -> None:
    phone = client_msg.client.phone_number
    text = client_msg.scheduled_message.message_text
    image = client_msg.scheduled_message.image.path if client_msg.scheduled_message.image else None
    video = client_msg.scheduled_message.video.path if client_msg.scheduled_message.video else None

    msg_response = client_msg.response
    try:
        success, response_code = whatsapp_sender.send_message(phone, text, image, video)
        if success:
            msg_response.status = "sent"
            msg_response.error_type = None
            client_msg.sent_at = timezone.now()
        else:
            msg_response.status = "failed"
            error = ErrorType.objects.filter(code=response_code).first()
            if not error:
                error, _ = ErrorType.objects.get_or_create(
                    code="UNKNOWN", defaults={"name": "Unknown Error", "description": response_code}
                )
            msg_response.error_type = error
    except Exception as e:
        msg_response.status = "failed"
        error, _ = ErrorType.objects.get_or_create(
            code="EXCEPTION", defaults={"name": "Unhandled Exception", "description": str(e)}
        )
        msg_response.error_type = error

    msg_response.save()
    client_msg.save()
