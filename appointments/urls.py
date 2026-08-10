from django.urls import path
from . import views

urlpatterns = [
    path('pre_importar/', views.appointment_pre_import, name='appointment_pre_import'),
    path('importar/', views.appointment_import, name='appointment_import'),
    path('', views.appointment_list, name='appointment_list'),
]
