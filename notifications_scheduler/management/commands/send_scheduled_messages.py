# notifications_scheduler/management/commands/send_scheduled_messages.py

import time

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from notifications_scheduler.models import ScheduledMessage, ClientScheduledMessage
from notifications_scheduler.senders.whatsapp_sender import WhatsAppSeleniumSender
from notifications_scheduler.services import send_message_to_client

class Command(BaseCommand):
    help = "Send scheduled WhatsApp messages to clients"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.SocialNetworkSenderInterface_sender = WhatsAppSeleniumSender()

    def handle(self, *args, **kwargs):
        now = timezone.now()
        scheduled_messages = ScheduledMessage.objects.filter(status="active", start_datetime__lte=now)

        for scheduled in scheduled_messages:
            batch_size = scheduled.recipient_count if scheduled.recipient_count > 0 else 50
            has_more = True
            offset = 0

            while has_more:
                pending_messages = ClientScheduledMessage.objects.filter(
                    Q(response__status="pending") |
                    Q(response__status="failed", response__error_type__code__in=["NETWORK", "TIMEOUT", "WHATSAPP_DOWN"])
                )[offset:offset + batch_size]

                if not pending_messages.exists():
                    self.stdout.write(f"No pending messages for scheduled message '{scheduled.subject}'")
                    break

                self.stdout.write(f"Processing batch of {len(pending_messages)} messages for '{scheduled.subject}'")

                for client_msg in pending_messages:
                    send_message_to_client(client_msg, self.SocialNetworkSenderInterface_sender)

                offset += batch_size
                time.sleep(60)  # avoid ban / overload
