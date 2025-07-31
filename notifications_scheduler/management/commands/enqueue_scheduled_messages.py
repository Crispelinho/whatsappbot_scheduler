from django.core.management.base import BaseCommand
from notifications_scheduler.tasks import send_scheduled_messages_task

class Command(BaseCommand):
    help = 'Enqueue the scheduled WhatsApp messages sending task using Celery.'

    def handle(self, *args, **options):
        send_scheduled_messages_task.delay()
        self.stdout.write(self.style.SUCCESS('Scheduled WhatsApp messages sending task has been enqueued.'))
