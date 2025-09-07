from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.db import models

from .models import Client, PhoneNumberClient, PhoneFormatError
from .utils import get_strategy_and_correction


# Vista para errores de clientes
class PhoneNumberErrorClientsView(View):
    template_name = 'clients/phone_number_errors_clients.html'


    def get(self, request):
        client_error_filter = request.GET.get('client_error')
        client_search = request.GET.get('client_search', '').strip()
        clients_qs = Client.objects.exclude(phone_format_error=PhoneFormatError.VALID)
        if client_error_filter:
            clients_qs = clients_qs.filter(phone_format_error=client_error_filter)
        if client_search:
            clients_qs = clients_qs.filter(
                models.Q(full_name__icontains=client_search) |
                models.Q(phone_number__icontains=client_search)
            )
        for c in clients_qs:
            suggestion, new_area, new_phone = get_strategy_and_correction(c.phone_number, c.area_code)
            c.suggested_strategy = suggestion
            c.suggested_area = new_area
            c.suggested_phone = new_phone
        return render(request, self.template_name, {
            'clients': clients_qs,
            'client_error_filter': client_error_filter,
            'client_search': client_search,
            'error_choices': PhoneFormatError.choices,
            'total_clients': clients_qs.count(),
        })

    def post(self, request):
        updated = 0
        selected = request.POST.getlist('selected_clients')
        for client_id in selected:
            area_key = f'client_area_{client_id}'
            phone_key = f'client_phone_{client_id}'
            area_value = request.POST.get(area_key, "")
            phone_value = request.POST.get(phone_key, "")
            try:
                client = Client.objects.get(id=client_id)
                client.phone_number = phone_value
                client.area_code = area_value
                client.save()
                updated += 1
            except Client.DoesNotExist:
                pass
        if updated:
            messages.success(request, f'Correcciones aplicadas a {updated} clientes seleccionados.')
        else:
            messages.warning(request, 'No se seleccionó ningún cliente para corregir.')
        return redirect('clients:phone_number_errors_clients')

# Vista para errores de teléfonos alternos
class PhoneNumberErrorPhonesView(View):
    template_name = 'clients/phone_number_errors_phones.html'


    def get(self, request):
        phone_error_filter = request.GET.get('phone_error')
        phone_search = request.GET.get('phone_search', '').strip()
        phones_qs = PhoneNumberClient.objects.exclude(phone_format_error=PhoneFormatError.VALID)
        if phone_error_filter:
            phones_qs = phones_qs.filter(phone_format_error=phone_error_filter)
        if phone_search:
            phones_qs = phones_qs.filter(
                models.Q(phone_number__icontains=phone_search) |
                models.Q(client__full_name__icontains=phone_search)
            )
        for p in phones_qs:
            suggestion, new_area, new_phone = get_strategy_and_correction(p.phone_number, p.area_code)
            p.suggested_strategy = suggestion
            p.suggested_area = new_area
            p.suggested_phone = new_phone
        return render(request, self.template_name, {
            'phones': phones_qs,
            'phone_error_filter': phone_error_filter,
            'phone_search': phone_search,
            'error_choices': PhoneFormatError.choices,
            'total_phones': phones_qs.count(),
        })

    def post(self, request):
        updated = 0
        selected = request.POST.getlist('selected_phones')
        for phone_id in selected:
            area_key = f'phoneclient_area_{phone_id}'
            phone_key = f'phoneclient_phone_{phone_id}'
            area_value = request.POST.get(area_key, "")
            phone_value = request.POST.get(phone_key, "")
            try:
                phone = PhoneNumberClient.objects.get(id=phone_id)
                phone.phone_number = phone_value
                phone.area_code = area_value
                phone.save()
                updated += 1
            except PhoneNumberClient.DoesNotExist:
                pass
        if updated:
            messages.success(request, f'Correcciones aplicadas a {updated} teléfonos alternos seleccionados.')
        else:
            messages.warning(request, 'No se seleccionó ningún teléfono alterno para corregir.')
        return redirect('clients:phone_number_errors_phones')
