from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import ScheduledMessage, ClientScheduledMessage, MessageResponse, ErrorType


@admin.register(ScheduledMessage)
class ScheduledMessageAdmin(ImportExportModelAdmin):
    list_display = (
        'id', 'subject', 'status', 'start_datetime', 
        'send_frequency', 'recipient_count', 'created_at'
    )
    list_filter = ('status', 'send_frequency')
    search_fields = ('subject', 'message_text')
    ordering = ('-start_datetime',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ClientScheduledMessage)
class ClientScheduledMessageAdmin(ImportExportModelAdmin):
    list_display = ('id', 'scheduled_message', 'client_name', 'status_display', 'sent_at')
    list_filter = ('response__status',)
    search_fields = ('client__full_name', 'client__phone_number')
    ordering = ('-sent_at',)
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('response', 'client', 'scheduled_message')

    def status_display(self, obj):
        return getattr(getattr(obj, 'response', None), 'status', None)
    status_display.short_description = "Status"
    status_display.admin_order_field = 'response__status'

    def client_name(self, obj):
        return getattr(getattr(obj, 'client', None), 'full_name', None)
    client_name.short_description = "Client"

    def save_model(self, request, obj, form, change):
        # Guardar el ClientScheduledMessage
        super().save_model(request, obj, form, change)

        # Crear MessageResponse si no existe
        if not hasattr(obj, 'response'):
            MessageResponse.objects.create(
                client_message=obj,
                status=MessageResponse.Status.PENDING
            )

@admin.register(MessageResponse)
class MessageResponseAdmin(ImportExportModelAdmin):
    list_display = ('id', 'client_name', 'status', 'error_type', 'created_at')
    list_filter = ('status', 'error_type')
    search_fields = ('client_message__client__full_name', 'client_message__client__phone_number')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('client_message__client', 'error_type')

    def client_name(self, obj):
        return getattr(getattr(getattr(obj, 'client_message', None), 'client', None), 'full_name', None)
    client_name.short_description = "Client"


@admin.register(ErrorType)
class ErrorTypeAdmin(ImportExportModelAdmin):
    list_display = ('id', 'name', 'code', 'description')
    search_fields = ('name', 'code')
