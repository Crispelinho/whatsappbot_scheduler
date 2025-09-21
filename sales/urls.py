from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('pre-importacion/', views.sale_pre_import, name='sale_pre_import'),
    path('importar/', views.sale_import, name='sale_import'),
]
