from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ScheduledMessage, ClientScheduledMessage, MessageResponse
from clients.models import Client
from django.db import transaction


def generate_or_update_client_scheduled_messages(scheduled_message):
    clients = Client.objects.filter(client_type=scheduled_message.client_type)
    for client in clients:
        csm, created = ClientScheduledMessage.objects.get_or_create(
            scheduled_message=scheduled_message,
            client=client
        )
        csm.scheduled_message = scheduled_message
        csm.save()
        # Asegurar que exista MessageResponse
        if not hasattr(csm, 'response'):
            MessageResponse.objects.create(client_message=csm, status=MessageResponse.Status.PENDING)
        else:
            # Si se solicita forzar a pending, actualizar el estado
            if csm.force_pending_on_update:
                resp = csm.response
                if resp.status != MessageResponse.Status.PENDING:
                    resp.status = MessageResponse.Status.PENDING
                    resp.response_code = None
                    resp.description = "Forzado a pendiente por actualización."
                    resp.save()

@receiver(post_save, sender=ScheduledMessage)
def scheduled_message_post_save(sender, instance, created, **kwargs):
    # Si el campo está activo, siempre ejecutar el flujo
    if instance.auto_generate_client_scheduled_messages:
        with transaction.atomic():
            generate_or_update_client_scheduled_messages(instance)
