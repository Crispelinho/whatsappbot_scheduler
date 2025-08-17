from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import ScheduledMessage, ClientScheduledMessage, MessageResponse, ErrorType


@admin.register(ScheduledMessage)
class ScheduledMessageAdmin(ImportExportModelAdmin):
    list_display = ('id', 'subject', 'status', 'start_datetime', 'send_frequency', 'recipient_count', 'created_at')
    list_filter = ('status', 'send_frequency')
    search_fields = ('subject', 'message_text')


@admin.register(ClientScheduledMessage)
class ClientScheduledMessageAdmin(ImportExportModelAdmin):
    list_display = ('id', 'scheduled_message', 'client', 'get_status', 'sent_at')
    list_filter = ('response__status',)  # 👈 status está en MessageResponse
    search_fields = ('client__full_name', 'client__phone_number')

    def get_status(self, obj):
        return obj.response.status
    get_status.short_description = "Status"
    get_status.admin_order_field = 'response__status'


@admin.register(MessageResponse)
class MessageResponseAdmin(ImportExportModelAdmin):
    list_display = ('id', 'status', 'error_type', 'created_at')
    list_filter = ('status', 'error_type')
    search_fields = ('client_message__client__full_name', 'client_message__client__phone_number')


@admin.register(ErrorType)
class ErrorTypeAdmin(ImportExportModelAdmin):
    list_display = ('id', 'name', 'code', 'description')
    search_fields = ('name', 'code')
