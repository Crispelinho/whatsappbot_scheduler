from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import Operator, ServiceType, Service, SaleRecord
from django.contrib.admin import SimpleListFilter



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

# @admin.register(SaleRecord)
# class SaleRecordAdmin(ImportExportModelAdmin):
#     resource_class = SaleRecordResource

#     def get_list_display(self, request):
#         return [field.name for field in self.model._meta.fields]

#     list_filter = ['date', 'operator', 'week', 'month', 'service__service_type']
#     search_fields = ['client__full_name', 'notes', 'errors']

def get_active_filters(request, exclude=None):
    exclude = exclude or []
    keys = ['month', 'week', 'operator', 'service__service_type']
    return {
        key: request.GET.get(key)
        for key in keys if key not in exclude and request.GET.get(key)
    }

class MonthDynamicFilter(SimpleListFilter):
    title = 'Mes'
    parameter_name = 'month'

    def lookups(self, request, model_admin):
        filters = get_active_filters(request, exclude=['month'])
        queryset = model_admin.model.objects.filter(**filters)
        meses = queryset.values_list('month', flat=True).distinct()
        return [(m, f"Mes {m}") for m in sorted(meses)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(month=self.value())
        return queryset

class WeekDynamicFilter(SimpleListFilter):
    title = 'Semana'
    parameter_name = 'week'

    def lookups(self, request, model_admin):
        filters = get_active_filters(request, exclude=['week'])
        queryset = model_admin.model.objects.filter(**filters)
        semanas = queryset.values_list('week', flat=True).distinct()
        return [(s, f"Semana {s}") for s in sorted(semanas)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(week=self.value())
        return queryset
    
class OperatorDynamicFilter(SimpleListFilter):
    title = 'Operaria'
    parameter_name = 'operator'

    def lookups(self, request, model_admin):
        filters = get_active_filters(request, exclude=['operator'])
        queryset = model_admin.model.objects.filter(**filters)
        operarias = queryset.values_list('operator__id', 'operator__name').distinct()
        return [(op_id, op_name) for op_id, op_name in operarias]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(operator__id=self.value())
        return queryset

class ServiceTypeDynamicFilter(SimpleListFilter):
    title = 'Tipo de Servicio'
    parameter_name = 'service__service_type'

    def lookups(self, request, model_admin):
        filters = get_active_filters(request, exclude=['service__service_type'])
        queryset = model_admin.model.objects.filter(**filters)
        tipos = queryset.values_list('service__service_type__id', 'service__service_type__name').distinct()
        return [(t_id, t_name) for t_id, t_name in tipos]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(service__service_type__id=self.value())
        return queryset

class ServiceDynamicFilter(SimpleListFilter):
    title = 'Servicio'
    parameter_name = 'service'

    def lookups(self, request, model_admin):
        filters = get_active_filters(request, exclude=['service'])
        queryset = model_admin.model.objects.filter(**filters)
        servicios = queryset.values_list('service__id', 'service__name').distinct()
        return [(s_id, s_name) for s_id, s_name in servicios]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(service__id=self.value())
        return queryset

@admin.register(SaleRecord)
class SaleRecordAdmin(ImportExportModelAdmin):
    resource_class = SaleRecordResource

    def get_list_display(self, request):
        return [field.name for field in self.model._meta.fields]

    list_filter = [
        MonthDynamicFilter,
        WeekDynamicFilter,
        OperatorDynamicFilter,
        ServiceTypeDynamicFilter,
        ServiceDynamicFilter,
    ]
    search_fields = ['client__full_name', 'notes', 'errors']
