from django.urls import path
from .views import (
    DashboardIndex,
    ClientMetricsView,
    ClientDetailMetricsView,
    ScheduledMessagesView,
    OperatorsMetricsView,
    OperatorDetailView,
    OperatorCreateView,
    OperatorLiquidatorView,
    SalesDetailView,
)
from notifications_scheduler.views import ScheduledMessageDetailView, ResendClientMessageView

app_name = 'dashboard'
urlpatterns = [
    path('', DashboardIndex.as_view(), name='dashboard_index'),
    path('clients-metrics/', ClientMetricsView.as_view(), name='clients_metrics'),
    path('client/<int:client_id>/metrics/', ClientDetailMetricsView.as_view(), name='client_detail_metrics'),
    path('scheduled-messages/', ScheduledMessagesView.as_view(), name='scheduled_messages'),
    path('scheduled-messages/<int:pk>/', ScheduledMessageDetailView.as_view(), name='scheduled_message_detail'),
    path('scheduled-messages/<int:pk>/resend/<int:client_id>/', ResendClientMessageView.as_view(), name='scheduled_message_resend'),
    path('operators-metrics/', OperatorsMetricsView.as_view(), name='operators_metrics'),
    path('operator/<int:operator_id>/', OperatorDetailView.as_view(), name='operator_detail'),
    path('operator/add/', OperatorCreateView.as_view(), name='operator_add'),
    path('operator-liquidator/', OperatorLiquidatorView.as_view(), name='operator_liquidator'),
    path('sales-detail/', SalesDetailView.as_view(), name='sales_detail'),
]
