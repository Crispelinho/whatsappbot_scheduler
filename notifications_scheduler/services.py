from django.utils import timezone
from .models import ClientScheduledMessage, ResponseCode, MessageResponse, ResponseCode
from .senders.base import SocialNetworkSenderInterface

def send_message_to_client(client_msg: ClientScheduledMessage, social_network_sender: SocialNetworkSenderInterface) -> None:
    phone = client_msg.client.phone_number
    text = client_msg.scheduled_message.message_text
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

    except Exception as e:
        msg_response.status = MessageResponse.Status.FAILED
        msg_response.response_code = ResponseCode.EXCEPTION.value
        msg_response.description = str(e)
        print(f"Exception sending message to {phone}: {e}")
    msg_response.save()
    client_msg.save()
