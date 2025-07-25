from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Client

class ClientResource(resources.ModelResource):
    class Meta:
        model = Client
        fields = (
            'id',
            'full_name',
            'phone_number',
            'email',
            'birthday',
            'first_visit_date',
            'created_at',
        )
        export_order = fields

@admin.register(Client)
class ClientAdmin(ImportExportModelAdmin):
    resource_class = ClientResource
    list_display = ('full_name', 'phone_number', 'email', 'birthday', 'first_visit_date', 'created_at')
    search_fields = ('full_name', 'phone_number', 'email')
