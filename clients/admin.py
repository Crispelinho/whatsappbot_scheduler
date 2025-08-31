import locale
import secrets
import string
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import fields, resources
from import_export.widgets import DateWidget
from datetime import datetime
from import_export.results import RowResult
from .models import Client

class CustomDateWidget(DateWidget):
    def clean(self, value, row=None, *args, **kwargs):
        if value:
            try:
                value = value.replace(" de ", " ")  # "24 de Febrero" -> "24 Febrero"
                # Guardar la configuración actual para restaurar luego
                current_locale = locale.getlocale(locale.LC_TIME)
                # Poner locale en español
                locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # O 'es_ES' en Windows o tu variante local
                dt = datetime.strptime(value, "%d %B").date()
                # Restaurar locale original
                locale.setlocale(locale.LC_TIME, current_locale)
                return dt
            except Exception:
                # Restaurar locale en caso de error
                locale.setlocale(locale.LC_TIME, current_locale)
                pass
        return super().clean(value, row, *args, **kwargs)

class ClientResource(resources.ModelResource):
    first_visit_date = fields.Field(
        column_name='first_visit_date',
        attribute='first_visit_date',
        widget=DateWidget(format='%d/%m/%Y')  # <-- aquí pones el formato de tu CSV
    )

    birthday = fields.Field(
        column_name='birthday',
        attribute='birthday',
        widget=CustomDateWidget(format='%d/%m/%Y')  # formato por defecto si no se parsea el texto
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Teléfonos que ya existen en la base de datos
        self.existing_phones = {
            client.phone_number: (client.id, client.full_name)
            for client in Client.objects.exclude(phone_number__isnull=True)
        }
        # Teléfonos encontrados en el archivo durante la importación
        self.imported_phones = {}

def generate_unknown_name(self, length: int = 10) -> str:
    # caracteres aleatorios seguros
    chars = string.ascii_letters + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(length))
    return f"Unknown_{random_part}"

def before_import_row(self, row, row_number=None, **kwargs):
    phone = (row.get('phone_number') or "").strip()
    
    # Si no viene nombre, generar uno aleatorio
    full_name = row.get('full_name')
    if full_name:
        full_name = full_name.strip()
    else:
        full_name = "UNKNOWN_" + self.generate_unknown_name().upper()

    client_id = row.get('id', 'sin id')

    # Permitir que se guarde como None si está vacío
    if phone == "":
        row['phone_number'] = None
        row['full_name'] = full_name  # asegurar que se guarde algo
        return

    # Verificar duplicado en BD
    if phone in self.existing_phones:
        db_id, db_name = self.existing_phones[phone]
        row_result: RowResult = kwargs.get("row_result")
        if row_result:
            row_result.warnings.append(
                f"🚫 Teléfono duplicado con base de datos: '{full_name}' con id {client_id} usa el número '{phone}', ya asignado a '{db_name}' con id {db_id}."
            )
        return

    # Verificar duplicado dentro del archivo
    if phone in self.imported_phones:
        prev_id, prev_name = self.imported_phones[phone]
        row_result: RowResult = kwargs.get("row_result")
        if row_result:
            row_result.warnings.append(
                f"⚠️ Teléfono duplicado en archivo: '{full_name}' con id {client_id} repite número '{phone}', ya usado por '{prev_name}' con id {prev_id}."
            )
        return

    # Registrar como visto
    self.imported_phones[phone] = (client_id, full_name)
    row['full_name'] = full_name  # asegurar que siempre tenga valor

    class Meta:
        model = Client
        import_id_fields = ('id',)
        fields = (
            'id',
            'full_name',
            'area_code',
            'phone_number',
            'email',
            'birthday',
            'first_visit_date',
            'client_type',
        )
        export_order = fields

@admin.register(Client)
class ClientAdmin(ImportExportModelAdmin):
    resource_class = ClientResource
    list_display = ('id', 'full_name', 'area_code', 'phone_number', 'email', 'birthday', 'first_visit_date', 'created_at', 'client_type')
    search_fields = ('full_name', 'phone_number', 'email', 'client_type')
    list_filter = ('client_type', 'created_at')
    ordering = ('-created_at',)
