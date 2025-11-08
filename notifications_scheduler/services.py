from django.utils import timezone
from .models import ClientScheduledMessage, ErrorType, MessageResponse, ErrorCode
from .senders.base import SocialNetworkSenderInterface

def send_message_to_client(client_msg: ClientScheduledMessage, social_network_sender: SocialNetworkSenderInterface) -> None:
    area_code = client_msg.client.area_code or ""
    phone = client_msg.client.phone_number
    text = client_msg.scheduled_message.message_text
    image = client_msg.scheduled_message.image.path if client_msg.scheduled_message.image else None
    video = client_msg.scheduled_message.video.path if client_msg.scheduled_message.video else None

    msg_response = MessageResponse(
        client_message=client_msg,
        status=MessageResponse.Status.PENDING,
        error_type=None,
    )

    try:
        result = social_network_sender.send_message(area_code, phone, text, image, video)
        if result.success:
            msg_response.status = MessageResponse.Status.SENT
            msg_response.error_type = None
            client_msg.sent_at = timezone.now()
        else:
            msg_response.status = MessageResponse.Status.FAILED
            error_enum = result.error_code if result.error_code in ErrorCode._value2member_map_ else ErrorCode.UNKNOWN
            error = ErrorType.objects.filter(code=error_enum.value).first()
            if not error:
                error, _ = ErrorType.objects.get_or_create(
                    code=ErrorCode.UNKNOWN.value, defaults={"name": "Unknown Error", "description": result.message}
                )
            msg_response.error_type = error
            print(f"Failed to send message to {area_code} {phone}: {result.message}")

    except Exception as e:
        msg_response.status = MessageResponse.Status.FAILED
        error = ErrorType.objects.get_or_create(
            code=ErrorCode.EXCEPTION.value, defaults={"name": "Unhandled Exception", "description": str(e)}
        )[0]
        msg_response.error_type = error
        print(f"Exception sending message to {phone}: {e}")
    msg_response.save()
    client_msg.save()
