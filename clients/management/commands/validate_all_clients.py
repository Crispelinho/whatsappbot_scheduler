from django.core.management.base import BaseCommand
from clients.models import Client, PhoneNumberClient

class Command(BaseCommand):
    help = 'Valida el formato y la coincidencia de números en Client y PhoneNumberClient, y reporta inconsistencias.'

    def handle(self, *args, **options):
        updated_clients = 0
        updated_phones = 0
        inconsistent_clients = []
        inconsistent_phones = []
        for client in Client.objects.all():
            format_error = Client.validate_phone_format(client.phone_number)
            is_match = client.check_primary_phone_match()
            client.phone_format_error = format_error
            client.primary_phone_match = is_match
            client.save(update_fields=['phone_format_error', 'primary_phone_match'])
            updated_clients += 1
            if format_error != 'valid' or not is_match:
                inconsistent_clients.append(client)
        for phone in PhoneNumberClient.objects.all():
            format_error = PhoneNumberClient.validate_phone_format(phone.phone_number)
            phone.phone_format_error = format_error
            phone.save(update_fields=['phone_format_error'])
            updated_phones += 1
            if format_error != 'valid':
                inconsistent_phones.append(phone)
        self.stdout.write(self.style.SUCCESS(f'Validados y actualizados {updated_clients} clientes y {updated_phones} teléfonos.'))
        if inconsistent_clients:
            self.stdout.write(self.style.WARNING('Clientes con inconsistencias:'))
            for c in inconsistent_clients:
                self.stdout.write(f'- {c.id}: {c.full_name} | Teléfono: {c.phone_number} | Error formato: {c.phone_format_error} | Coincide primario: {c.primary_phone_match}')
        if inconsistent_phones:
            self.stdout.write(self.style.WARNING('Teléfonos alternos con formato inválido:'))
            for p in inconsistent_phones:
                self.stdout.write(f'- {p.id}: {p.client.full_name} | Teléfono: {p.phone_number} | Error formato: {p.phone_format_error}')
