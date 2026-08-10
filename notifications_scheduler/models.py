
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from clients.models import Client
from enum import Enum

class ResponseCode(Enum):
    """Response codes for message sending errors."""
    SUCCESS = "SUCCESS"
    NETWORK = "NETWORK"
    BLOCKED = "BLOCKED"
    INVALID_NUMBER = "INVALID_NUMBER"
    NOT_FOUND_IN_WHATSAPP = "NOT_FOUND_IN_WHATSAPP"
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT = "RATE_LIMIT"
    UNKNOWN = "UNKNOWN"
    NO_INPUT_BOX = "NO_INPUT_BOX"
    WHATSAPP_DOWN = "WHATSAPP_DOWN"
    WHATSAPP_SESSION_CRASHED = "WHATSAPP_SESSION_CRASHED"
    UPLOAD_MEDIA_FAILED = "UPLOAD_MEDIA_FAILED"
    EXCEPTION = "EXCEPTION"

class ScheduledMessageType(Enum):
    PROMOTIONAL = "PROMOTIONAL", "Promocional"
    REMINDER = "REMINDER", "Recordatorio"
    ALERT = "ALERT", "Alerta"
    FOLLOWUP = "FOLLOWUP", "Seguimiento"
    BIRTHDAY = "BIRTHDAY", "Cumpleaños"
    CUSTOM = "CUSTOM", "Personalizado"

class ScheduledMessage(models.Model):
    auto_generate_client_scheduled_messages = models.BooleanField(
        default=False,
        verbose_name="Auto generate client scheduled messages",
        help_text="Si está activo, al guardar se generarán/actualizarán ClientScheduledMessages para todos los clientes del tipo seleccionado y sus MessageResponses."
    )
    force_pending_on_update = models.BooleanField(
        default=False,
        verbose_name="Force MessageResponse to pending on update",
        help_text="¿Desea actualizar el estado del mensaje programado a pendiente?"
    )
    subject = models.CharField("Subject", max_length=255)
    message_text = models.TextField("Message Text")
    replace_text_message_variables = models.BooleanField(
        "Replace Text Message Variables",
        default=False,
        help_text="Si está activo, se reemplazarán las variables en el texto del mensaje antes de enviarlo."
    )
    scheduled_message_type = models.CharField(
        "Scheduled Message Type",
        max_length=20,
        choices=[(e.value[0], e.value[1]) for e in ScheduledMessageType],
        default=ScheduledMessageType.CUSTOM.value[0]
    )
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
    # image1 = models.ImageField(
    #     "Optional Image 1",
    #     upload_to="scheduled_messages/images/",
    #     null=True,
    #     blank=True,
    #     help_text="Optional image to send with the message"
    # )
    video = models.FileField(
        "Optional Video",
        upload_to="scheduled_messages/videos/",
        null=True,
        blank=True,
        help_text="Optional video to send with the message"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    client_type = models.CharField(
        max_length=20,
        choices=Client.ClientType.choices,
        default=Client.ClientType.CONSOLIDATED,
        blank=True,
        help_text="Tipo de cliente al momento de enviar la notificación."
    )

    class Meta:
        verbose_name = "Scheduled Message"
        verbose_name_plural = "Scheduled Messages"

    def __str__(self):
        return f"{self.subject} ({self.status})"
    
    def render_message(self, context: dict) -> str:
        """
        Renderiza el texto del mensaje usando las variables del contexto proporcionado.
        Si replace_text_message_variables está activo, reemplaza las variables en el texto.
        """
        if not self.replace_text_message_variables or not context:
            return self.message_text
        try:
            return self.message_text.format(**context)
        except Exception as e:
            # Si hay error de formato, regresa el texto original y opcionalmente loguea el error
            return self.message_text

class MessageResponse(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    client_message = models.OneToOneField(
        'ClientScheduledMessage',
        on_delete=models.CASCADE,
        related_name='response'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    response_code = models.CharField(max_length=50, blank=True, null=True, choices=[(e.value, e.name) for e in ResponseCode])
    description = models.TextField("Description", blank=True, null=True)
    retryable = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Response {self.id} - {self.status}"

    def clean(self):
        if self.status == MessageResponse.Status.FAILED and not self.response_code:
            raise ValidationError("You must assign a response_code if the status is 'failed'.")
        if self.status in [MessageResponse.Status.PENDING, MessageResponse.Status.SENT] and self.response_code and self.response_code != ResponseCode.SUCCESS.value:
            raise ValidationError("You cannot assign a non-success response_code if the status is not 'failed'.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class ClientScheduledMessage(models.Model):
    scheduled_message = models.ForeignKey(ScheduledMessage, on_delete=models.CASCADE, related_name="client_messages")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="scheduled_messages")
    sent_at = models.DateTimeField("Sent Date and Time", null=True, blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    last_retry_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Client Scheduled Message"
        verbose_name_plural = "Client Scheduled Messages"
        constraints = [
            models.UniqueConstraint(
                fields=["scheduled_message", "client"],
                name="unique_scheduled_message_per_client"
            )
        ]

    def __str__(self):
        status = self.response.status if hasattr(self, "response") else "no response"
        return f"Message to {self.client.full_name} - {status}"

    @property
    def can_retry(self):
        """Determina si se puede reintentar el envío según el response_code y cantidad de retries."""
        if not hasattr(self, "response") or not self.response.response_code:
            return False
        return (
            self.response.response_code in [
                ResponseCode.NETWORK.value,
                ResponseCode.TIMEOUT.value,
                ResponseCode.WHATSAPP_DOWN.value,
                ResponseCode.RATE_LIMIT.value
            ]
            and self.retry_count < self.max_retries
        )

class ImportErrorLog(models.Model):
    line_number = models.IntegerField()
    error_message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Error en línea {self.line_number}: {self.error_message[:50]}"
    
class ClientScheduledMessageImportErrorLog(ImportErrorLog):
    client_scheduled_message = models.ForeignKey(ClientScheduledMessage, on_delete=models.CASCADE, related_name="import_errors")
    
    def __str__(self):
        return f"Error en línea {self.line_number} para ClientScheduledMessage {self.client_scheduled_message.id}: {self.error_message[:50]}"
