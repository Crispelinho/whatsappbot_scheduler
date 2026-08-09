from django.urls import path
from .views import PhoneNumberErrorClientsView, PhoneNumberErrorPhonesView, client_pre_import, client_import, unique_clients, duplicated_clients, new_clients

app_name = 'clients'

urlpatterns = [
    path('pre_importar/', client_pre_import, name='client_pre_import'),
    path('importar/', client_import, name='client_import'),
    path('phone-number-errors/clients/', PhoneNumberErrorClientsView.as_view(), name='phone_number_errors_clients'),
    path('phone-number-errors/phones/', PhoneNumberErrorPhonesView.as_view(), name='phone_number_errors_phones'),
    path('unique-clients/', unique_clients, name='unique_clients'),
    path('duplicated-clients/', duplicated_clients, name='duplicated_clients'),
    path('new-clients/', new_clients, name='new_clients'),
]
