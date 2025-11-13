from django.urls import path
from .views import DashboardIndex, ClientMetricsView

app_name = 'dashboard'
urlpatterns = [
    path('', DashboardIndex.as_view(), name='dashboard_index'),
    path('clients-metrics/', ClientMetricsView.as_view(), name='clients_metrics'),
]
