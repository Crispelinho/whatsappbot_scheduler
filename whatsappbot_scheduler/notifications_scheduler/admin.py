from django.contrib import admin
from .models import ScheduledMessage, ClientMessage

@admin.register(ScheduledMessage)
class ScheduledMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'status', 'start_datetime', 'send_frequency', 'recipient_count', 'created_at')
    list_filter = ('status', 'send_frequency')
    search_fields = ('subject', 'message_text')

@admin.register(ClientMessage)
class ClientMessageAdmin(admin.ModelAdmin):
    list_display = ('scheduled_message', 'client', 'send_status', 'sent_at')
    list_filter = ('send_status',)
    search_fields = ('client__full_name', 'client__phone_number')
