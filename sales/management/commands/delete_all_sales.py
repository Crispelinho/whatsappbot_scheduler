from django.core.management.base import BaseCommand
from sales.models import SaleRecord

class Command(BaseCommand):
    help = "Elimina todos los registros de ventas (SaleRecord) de la base de datos."

    def handle(self, *args, **options):
        count = SaleRecord.objects.count()
        confirm = input(f"¿Estás seguro que deseas eliminar {count} registros de ventas? (s/N): ")
        if confirm.lower() == 's':
            SaleRecord.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f"Se eliminaron {count} registros de ventas."))
        else:
            self.stdout.write(self.style.WARNING("Operación cancelada."))