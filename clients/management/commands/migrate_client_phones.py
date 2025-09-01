from django.core.management.base import BaseCommand
from clients.models import Client, PhoneNumberClient

class Command(BaseCommand):
    help = 'Migrate phone_number and area_code from Client to PhoneNumberClient'

    def handle(self, *args, **options):
        migrated = 0
        for client in Client.objects.all():
            if client.phone_number:
                PhoneNumberClient.objects.get_or_create(
                    client=client,
                    phone_number=client.phone_number,
                    area_code=client.area_code,
                    is_primary=True
                )
                migrated += 1
        self.stdout.write(self.style.SUCCESS(f'Migrated {migrated} phone numbers to PhoneNumberClient'))
