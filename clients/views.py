from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.db import models

from .models import Client, PhoneNumberClient, PhoneFormatError
from .utils import get_strategy_and_correction, split_and_clean_phones, get_area_code_for_number


def enrich_client_with_corrections(client: Client):
    corrections = get_strategy_and_correction(client.phone_number, client.area_code) or []

    # Asegurar al menos 3 elementos
    while len(corrections) < 3:
        corrections.append(("Sin número", '', ''))

    # Corrección principal
    client.suggested_strategy = corrections[0][0]
    client.suggested_area = corrections[0][1]
    client.suggested_phone = corrections[0][2]

    # Correcciones individuales
    for i in range(3):
        setattr(client, f'suggested_strategy_{i+1}', corrections[i][0])
        setattr(client, f'suggested_phone_{i+1}', corrections[i][1] or '')
        setattr(client, f'suggested_area_{i+1}', corrections[i][2] or '')

    # Actualizar tipo de error desde estrategia aplicada
    # client.phone_format_error = Client.validate_phone_format(client.phone_number, client.area_code)

def enrich_phone_with_corrections(phone_obj: PhoneNumberClient):
    """
    Enriquecer un PhoneNumberClient con sugerencias de corrección,
    asegurando al menos 3 alternativas.
    """
    corrections = get_strategy_and_correction(phone_obj.phone_number, phone_obj.area_code) or []

    # Asegurar mínimo 3
    while len(corrections) < 3:
        corrections.append(("Sin número", "", ""))

    # Corrección principal
    phone_obj.suggested_strategy = corrections[0][0]
    phone_obj.suggested_area = corrections[0][1]
    phone_obj.suggested_phone = corrections[0][2]

    # Correcciones individuales
    for i in range(3):
        setattr(phone_obj, f'suggested_strategy_{i+1}', corrections[i][0])
        setattr(phone_obj, f'suggested_area_{i+1}', corrections[i][1] or "")
        setattr(phone_obj, f'suggested_phone_{i+1}', corrections[i][2] or "")

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
        for client in clients_qs:
            enrich_client_with_corrections(client)
            print("Sugerencia", client.suggested_strategy_1, "Phone 1", client.suggested_phone_1, "Area 1",client.suggested_area_1)

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
            # Leer todos los campos de área y teléfono
            area1 = request.POST.get(f'client_area_{client_id}', "")
            phone1 = request.POST.get(f'client_phone_{client_id}', "")
            area2 = request.POST.get(f'client_area2_{client_id}', "")
            phone2 = request.POST.get(f'client_phone2_{client_id}', "")
            area3 = request.POST.get(f'client_area3_{client_id}', "")
            phone3 = request.POST.get(f'client_phone3_{client_id}', "")
            try:
                client = Client.objects.get(id=client_id)
                client.phone_number = phone1
                client.area_code = area1
                client.second_phone_number = phone2
                client.second_area_code = area2
                client.third_phone_number = phone3
                client.third_area_code = area3
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
        for phone_obj in phones_qs:
            enrich_phone_with_corrections(phone_obj)
            
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
            # Obtener el registro original para saber el cliente
            try:
                phone_obj = PhoneNumberClient.objects.get(id=phone_id)
            except PhoneNumberClient.DoesNotExist:
                continue
            client = phone_obj.client
            # Leer todos los campos de área y teléfono
            area1 = request.POST.get(f'phoneclient_area_{phone_id}', "")
            phone1 = request.POST.get(f'phoneclient_phone_{phone_id}', "")
            area2 = request.POST.get(f'phoneclient_area2_{phone_id}', "")
            phone2 = request.POST.get(f'phoneclient_phone2_{phone_id}', "")
            area3 = request.POST.get(f'phoneclient_area3_{phone_id}', "")
            phone3 = request.POST.get(f'phoneclient_phone3_{phone_id}', "")
            # Guardar/actualizar hasta 3 registros para este cliente y estos valores
            values = [
                (area1, phone1),
                (area2, phone2),
                (area3, phone3),
            ]
            # Eliminar el registro original (si el número ya no está en la lista)
            original_numbers = {p for a, p in values if p}
            # Actualizar o crear los registros
            for idx, (area, phone) in enumerate(values):
                if phone:
                    _, _ = PhoneNumberClient.objects.update_or_create(
                        client=client,
                        phone_number=phone,
                        defaults={
                            'area_code': area,
                            'is_primary': idx == 0,
                        }
                    )
                    updated += 1
            # Eliminar registros antiguos que ya no están en la lista
            PhoneNumberClient.objects.filter(client=client).exclude(phone_number__in=original_numbers).delete()
        if updated:
            messages.success(request, f'Correcciones aplicadas a {updated} teléfonos alternos seleccionados.')
        else:
            messages.warning(request, 'No se seleccionó ningún teléfono alterno para corregir.')
        return redirect('clients:phone_number_errors_phones')
