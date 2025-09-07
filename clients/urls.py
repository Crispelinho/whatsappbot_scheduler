from django.urls import path
from .views import PhoneNumberErrorFixView

app_name = 'clients'

urlpatterns = [
    path('phone-number-errors/', PhoneNumberErrorFixView.as_view(), name='phone_number_errors'),
]
