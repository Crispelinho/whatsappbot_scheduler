from django.urls import path
from .views import DashboardIndex, ClientMetricsView, ClientDetailMetricsView, ScheduledMessagesView
from notifications_scheduler.views import ScheduledMessageDetailView, ResendClientMessageView

app_name = 'dashboard'
urlpatterns = [
    path('', DashboardIndex.as_view(), name='dashboard_index'),
    path('clients-metrics/', ClientMetricsView.as_view(), name='clients_metrics'),
    path('client/<int:client_id>/metrics/', ClientDetailMetricsView.as_view(), name='client_detail_metrics'),
    path('scheduled-messages/', ScheduledMessagesView.as_view(), name='scheduled_messages'),
    path('scheduled-messages/<int:pk>/', ScheduledMessageDetailView.as_view(), name='scheduled_message_detail'),
    path('scheduled-messages/<int:pk>/resend/<int:client_id>/', ResendClientMessageView.as_view(), name='scheduled_message_resend'),
]
