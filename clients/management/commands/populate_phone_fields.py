from django.core.management.base import BaseCommand
from clients.models import Client, PhoneNumberClient

class Command(BaseCommand):
    help = 'Pobla los campos phone_format_error y primary_phone_match para clientes y teléfonos alternos.'

    def handle(self, *args, **options):
        # Actualizar clientes
        updated_clients = 0
        for client in Client.objects.all():
            client.phone_format_error = Client.validate_phone_format(client.phone_number)
            client.primary_phone_match = client.check_primary_phone_match()
            client.save(update_fields=["phone_format_error", "primary_phone_match"])
            updated_clients += 1
        self.stdout.write(self.style.SUCCESS(f'Clientes actualizados: {updated_clients}'))

        # Actualizar teléfonos alternos
        updated_phones = 0
        for phone in PhoneNumberClient.objects.all():
            phone.phone_format_error = PhoneNumberClient.validate_phone_format(phone.phone_number)
            phone.save(update_fields=["phone_format_error"])
            updated_phones += 1
        self.stdout.write(self.style.SUCCESS(f'Teléfonos alternos actualizados: {updated_phones}'))
