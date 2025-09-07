from django.urls import path
from .views import PhoneNumberErrorClientsView, PhoneNumberErrorPhonesView

app_name = 'clients'

urlpatterns = [
    path('phone-number-errors/clients/', PhoneNumberErrorClientsView.as_view(), name='phone_number_errors_clients'),
    path('phone-number-errors/phones/', PhoneNumberErrorPhonesView.as_view(), name='phone_number_errors_phones'),
]
