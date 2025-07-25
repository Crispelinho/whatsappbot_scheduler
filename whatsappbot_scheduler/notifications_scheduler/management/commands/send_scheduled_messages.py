# notifications_scheduler/management/commands/send_scheduled_messages.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from notifications_scheduler.models import ScheduledMessage, ClientMessage

def send_whatsapp_message(phone_number: str, message: str):
    """
    Función simulada para enviar mensaje por WhatsApp.
    Aquí va la integración real con Selenium o API.
    """
    print(f"Sending message to {phone_number}: {message}")
    # Simular envío exitoso
    return True, "Sent successfully"


class Command(BaseCommand):
    help = "Send scheduled WhatsApp messages to clients"

    def handle(self, *args, **kwargs):
        now = timezone.now()
        scheduled_messages = ScheduledMessage.objects.filter(status='active', start_datetime__lte=now)

        for scheduled in scheduled_messages:
            pending_messages = ClientMessage.objects.filter(
                scheduled_message=scheduled,
                send_status='pending'
            )[:50]  # enviar en bloques de 50

            if not pending_messages.exists():
                self.stdout.write(f"No pending messages for scheduled message '{scheduled.subject}'")
                continue

            for client_msg in pending_messages:
                phone = client_msg.client.phone_number
                text = scheduled.message_text
                try:
                    success, response = send_whatsapp_message(phone, text)
                    if success:
                        client_msg.send_status = 'sent'
                        client_msg.send_datetime = timezone.now()
                        client_msg.response = response
                        client_msg.save()
                        self.stdout.write(f"Sent message to {phone}")
                    else:
                        client_msg.send_status = 'failed'
                        client_msg.response = response
                        client_msg.save()
                        self.stderr.write(f"Failed to send message to {phone}: {response}")
                except Exception as e:
                    client_msg.send_status = 'failed'
                    client_msg.response = str(e)
                    client_msg.save()
                    self.stderr.write(f"Exception sending message to {phone}: {e}")
