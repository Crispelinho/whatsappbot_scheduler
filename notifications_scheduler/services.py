from django.utils import timezone
from .models import ClientScheduledMessage, ResponseCode, MessageResponse, ResponseCode, ScheduledMessageType
from .senders.base import SocialNetworkSenderInterface
from notifications_scheduler.exceptions.whatsapp import WhatsAppSessionException
from appointments.models import Appointment

def send_message_to_client(client_msg: ClientScheduledMessage, social_network_sender: SocialNetworkSenderInterface) -> None:
    area_code = client_msg.client.area_code or ""
    phone = client_msg.client.phone_number
    if phone and not phone.startswith("+"):
        phone = area_code + phone

    text = get_scheduled_message_text(client_msg)
    image = client_msg.scheduled_message.image.path if client_msg.scheduled_message.image else None
    video = client_msg.scheduled_message.video.path if client_msg.scheduled_message.video else None

    msg_response, _ = MessageResponse.objects.get_or_create(client_message=client_msg)
    
    try:
        message_send_result = social_network_sender.send_message(phone, text, image, video)
        if message_send_result.success:
            msg_response.status = MessageResponse.Status.SENT
            msg_response.response_code = ResponseCode.SUCCESS.value
            msg_response.description = message_send_result.message or "Sent successfully"
            client_msg.sent_at = timezone.now()
        else:
            msg_response.status = MessageResponse.Status.FAILED
            msg_response.response_code = message_send_result.error_code
            msg_response.description = message_send_result.message    
            print(f"Failed to send message to {phone}: {msg_response.response_code}")

    except WhatsAppSessionException as e:
        msg_response.status = MessageResponse.Status.FAILED
        msg_response.response_code = ResponseCode.WHATSAPP_SESSION_CRASHED.value
        msg_response.description = f"Sesión de WhatsApp Web inválida: {e}"
        print(f"WhatsApp session error sending message to {phone}: {e}")

    except Exception as e:
        msg_response.status = MessageResponse.Status.FAILED
        msg_response.response_code = ResponseCode.EXCEPTION.value
        msg_response.description = str(e)
        print(f"Exception sending message to {phone}: {e}")
    msg_response.save()
    client_msg.save()

def get_scheduled_message_text(client_msg: ClientScheduledMessage) -> str:

    if getattr(client_msg.scheduled_message, 'scheduled_message_type', None) == ScheduledMessageType.PROMOTIONAL.value:
        return client_msg.scheduled_message.message_text

    # Build context for appointment reminders (all keys in English)
    context = {
        "client_name": client_msg.client.full_name,
    }

    appointment = Appointment.objects.filter(client=client_msg.client, scheduled_datetime__gte=timezone.now()).order_by('scheduled_datetime').first()
    if appointment:
        context["service_name"] = getattr(appointment.service, "name", "")
        context["appointment_datetime"] = appointment.scheduled_datetime.strftime("%d/%m/%Y at %H:%M")
        context["notes"] = appointment.notes

    return client_msg.scheduled_message.render_message(context)