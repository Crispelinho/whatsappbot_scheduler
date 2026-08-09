# sales/management/commands/import_ventas2025.py

from django.core.management.base import BaseCommand
from sales.importers.google_sheets import import_sales_from_sheet

class Command(BaseCommand):
    help = "Importa registros de ventas desde la hoja de cálculo 'Ventas 2025' en Google Sheets"

    def handle(self, *args, **kwargs):
        self.stdout.write("📥 Iniciando importación desde Google Sheets...")
        import_sales_from_sheet()
        self.stdout.write(self.style.SUCCESS("✅ Importación completada."))