from import_export.results import RowResult
from import_export import resources
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import ClientScheduledMessageImportErrorLog, ScheduledMessage, ClientScheduledMessage, MessageResponse


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

class ClientScheduledMessageResource(resources.ModelResource):

    def import_row(self, row, instance_loader, **kwargs):
        try:
            return super().import_row(row, instance_loader, **kwargs)
        except Exception as e:
            ClientScheduledMessageImportErrorLog.objects.create(
                line_number=row.get('id', 0),  # puedes usar row_number si prefieres
                error_message=str(e)
            )

            # Devolver un RowResult de error para que salga en el admin
            result = RowResult()
            result.errors.append(str(e))
            result.import_type = RowResult.IMPORT_TYPE_ERROR
            return result

    def before_import_row(self, row, row_number=None, **kwargs):
        client_id = row.get("client")  # el nombre de la columna en tu archivo
        print("client_id:", client_id)
        if not client_id:
            # Puedes marcar esta fila como error
            raise Exception(f"Fila {row_number}: client_id es obligatorio", row, "client_id", row.get("client"))

    class Meta:
        model = ClientScheduledMessage
        import_id_fields = ('id',)  # usamos el id real
        fields = (
            "id",
            "scheduled_message",
            "client",
            "sent_at",
            "retry_count",
            "max_retries",
            "last_retry_at",
            "created_at",
            "updated_at",
        )
        export_order = fields


@admin.register(ClientScheduledMessage)
class ClientScheduledMessageAdmin(ImportExportModelAdmin):
    resource_class = ClientScheduledMessageResource
    list_display = ('id', 'scheduled_message', 'client', 'status_display', 'sent_at')
    list_filter = ('response__status', 'scheduled_message')
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
        if not obj.client:
            print("Error: No client assigned to ClientScheduledMessage", obj)
            raise ValueError("Debes seleccionar un cliente antes de guardar.")
        try:
            super().save_model(request, obj, form, change)
            if not hasattr(obj, 'response'):
                MessageResponse.objects.create(
                    client_message=obj,
                    status=MessageResponse.Status.PENDING
                )
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise

@admin.register(MessageResponse)
class MessageResponseAdmin(ImportExportModelAdmin):
    list_display = ('id', 'client_message__scheduled_message', 'client_message__client', 'status', 'response_code', 'description', 'created_at', 'updated_at')
    list_filter = ('status', 'response_code', 'client_message__scheduled_message')
    search_fields = (
        'client_message__scheduled_message__subject',
        'client_message__scheduled_message__message_text',
        'client_message__client__full_name',
        'client_message__client__phone_number'
    )
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('client_message__client')

    # def client_name(self, obj):
    #     return getattr(getattr(getattr(obj, 'client_message', None), 'client', None), 'full_name', None)
    # client_name.short_description = "Client"

@admin.register(ClientScheduledMessageImportErrorLog)
class ImportErrorLogAdmin(admin.ModelAdmin):
    list_display = ("line_number", "error_message", "created_at", "client_scheduled_message")
    ordering = ("-created_at",)
    search_fields = ("error_message",)