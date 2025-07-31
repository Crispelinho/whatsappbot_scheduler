from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Appointment

class AppointmentResource(resources.ModelResource):
    class Meta:
        model = Appointment
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('id',)

@admin.register(Appointment)
class AppointmentAdmin(ImportExportModelAdmin):
    resource_class = AppointmentResource
    list_display = ('client', 'service', 'operator', 'scheduled_datetime', 'status')
    list_filter = ('status', 'scheduled_datetime', 'operator')
    search_fields = ('client__name', 'service__name', 'operator__name')
