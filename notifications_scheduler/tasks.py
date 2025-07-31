from celery import shared_task
from django.core.management import call_command

@shared_task
def send_scheduled_messages_task():
    print("Celery está ejecutando la tarea de envío programado")
    call_command('send_scheduled_messages')
