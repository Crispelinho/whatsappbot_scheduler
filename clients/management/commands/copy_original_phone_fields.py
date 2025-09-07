from django.core.management.base import BaseCommand
from clients.models import PhoneNumberClient, Client

class Command(BaseCommand):
    help = 'Copia los valores actuales de phone_number y area_code a los campos originales en PhoneNumberClient y Client.'

    def handle(self, *args, **options):
        updated_phones = 0
        for phone in PhoneNumberClient.objects.all():
            changed = False
            if not phone.original_phone_number:
                phone.original_phone_number = phone.phone_number
                changed = True
            if not phone.original_area_code:
                phone.original_area_code = phone.area_code
                changed = True
            if changed:
                phone.save(update_fields=[
                    'original_phone_number', 'original_area_code'])
                updated_phones += 1
        self.stdout.write(self.style.SUCCESS(f'{updated_phones} teléfonos alternos actualizados.'))

        updated_clients = 0
        for client in Client.objects.all():
            changed = False
            if not client.original_phone_number:
                client.original_phone_number = client.phone_number
                changed = True
            if not client.original_area_code:
                client.original_area_code = client.area_code
                changed = True
            if changed:
                client.save(update_fields=[
                    'original_phone_number', 'original_area_code'])
                updated_clients += 1
        self.stdout.write(self.style.SUCCESS(f'{updated_clients} clientes actualizados.'))
