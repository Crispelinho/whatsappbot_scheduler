from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from clients.models import Client


class ScheduledMessage(models.Model):
    subject = models.CharField("Subject", max_length=255)
    message_text = models.TextField("Message Text")
    start_datetime = models.DateTimeField("Start Date and Time", default=timezone.now)
    send_frequency = models.CharField(
        "Send Frequency",
        max_length=20,
        choices=[
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("in_batches", "In Batches"),
        ],
        default="daily"
    )
    recipient_count = models.PositiveIntegerField("Number of Recipients", default=0)
    status = models.CharField(
        "Status",
        max_length=20,
        choices=[
            ("active", "Active"),
            ("paused", "Paused"),
            ("finished", "Finished"),
        ],
        default="active"
    )
    image = models.ImageField(
        "Optional Image",
        upload_to="scheduled_messages/images/",
        null=True,
        blank=True,
        help_text="Optional image to send with the message"
    )
    video = models.FileField(
        "Optional Video",
        upload_to="scheduled_messages/videos/",
        null=True,
        blank=True,
        help_text="Optional video to send with the message"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Scheduled Message"
        verbose_name_plural = "Scheduled Messages"

    def __str__(self):
        return f"{self.subject} ({self.status})"


class ErrorType(models.Model):
    """Error types (e.g., Network, WhatsApp Block, Invalid Client, etc.)"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)  # e.g. NETWORK, BLOCKED, INVALID_NUMBER
    description = models.TextField()
    retryable = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class MessageResponse(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True)
    error_type = models.ForeignKey(
        ErrorType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="responses"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Response {self.id} - {self.status}"

    def clean(self):
        if self.status == "failed" and not self.error_type:
            raise ValidationError("You must assign an error type if the status is 'failed'.")
        if self.status in ["pending", "sent"] and self.error_type:
            raise ValidationError("You cannot assign an error type if the status is not 'failed'.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class ClientScheduledMessage(models.Model):
    scheduled_message = models.ForeignKey(ScheduledMessage, on_delete=models.CASCADE, related_name="client_messages")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="scheduled_messages")
    sent_at = models.DateTimeField("Sent Date and Time", null=True, blank=True)
    response = models.OneToOneField(
        MessageResponse,
        on_delete=models.CASCADE,
        related_name="client_message"
    )
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    last_retry_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Client Message"
        verbose_name_plural = "Client Messages"
        constraints = [
            models.UniqueConstraint(
                fields=["scheduled_message", "client"],
                name="unique_scheduled_message_per_client"
            )
        ]

    def __str__(self):
        return f"Message to {self.client.full_name} - {self.response.status}"

    def can_retry(self):
            if not self.error_type:
                return False
            return self.error_type.code in ["NETWORK", "TIMEOUT", "RATE_LIMIT"] and self.retry_count < 5
