from django.db import models
from django.utils import timezone
from clients.models import Client  # Assuming your clients app is named 'clients'

class ScheduledMessage(models.Model):
    subject = models.CharField("Subject", max_length=255)
    message_text = models.TextField("Message Text")
    start_datetime = models.DateTimeField("Start Date and Time", default=timezone.now)
    send_frequency = models.CharField(
        "Send Frequency",
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('in_batches', 'In Batches'),
        ],
        default='daily'
    )
    recipient_count = models.PositiveIntegerField("Number of Recipients", default=0)
    status = models.CharField(
        "Status",
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('paused', 'Paused'),
            ('finished', 'Finished'),
        ],
        default='active'
    )
    image = models.ImageField(
        "Optional Image",
        upload_to="scheduled_messages/images/",
        null=True,
        blank=True,
        help_text="Optional image to send with the message"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Scheduled Message"
        verbose_name_plural = "Scheduled Messages"

    def __str__(self):
        return f"{self.subject} ({self.status})"


class ClientMessage(models.Model):
    scheduled_message = models.ForeignKey(ScheduledMessage, on_delete=models.CASCADE, related_name='client_messages')
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    sent_at = models.DateTimeField("Sent Date and Time", null=True, blank=True)
    send_status = models.CharField(
        "Send Status",
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('sent', 'Sent'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    response = models.TextField("Response / Result", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Client Message"
        verbose_name_plural = "Client Messages"
        unique_together = ('scheduled_message', 'client')

    def __str__(self):
        return f"Message to {self.client.full_name} - {self.send_status}"
