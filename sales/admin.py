from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import Operator, ServiceType, Service, SaleRecord


# Resources
class OperatorResource(resources.ModelResource):
    class Meta:
        model = Operator

class ServiceTypeResource(resources.ModelResource):
    class Meta:
        model = ServiceType

class ServiceResource(resources.ModelResource):
    class Meta:
        model = Service

class SaleRecordResource(resources.ModelResource):
    class Meta:
        model = SaleRecord


# Admins
@admin.register(Operator)
class OperatorAdmin(ImportExportModelAdmin):
    resource_class = OperatorResource
    list_display = ['name', 'phone_number', 'commission_percentage']
    search_fields = ['name', 'phone_number']

@admin.register(ServiceType)
class ServiceTypeAdmin(ImportExportModelAdmin):
    resource_class = ServiceTypeResource
    list_display = ['name', 'commission_percentage']
    search_fields = ['name']

@admin.register(Service)
class ServiceAdmin(ImportExportModelAdmin):
    resource_class = ServiceResource
    list_display = ['name', 'service_type', 'price', 'duration_minutes']
    search_fields = ['name']

@admin.register(SaleRecord)
class SaleRecordAdmin(ImportExportModelAdmin):
    resource_class = SaleRecordResource
    list_display = ['date', 'client', 'service', 'operator', 'total_paid', 'paid', 'payment_method']
    list_filter = ['date', 'operator', 'service']
    search_fields = ['client__name', 'notes', 'errors']
