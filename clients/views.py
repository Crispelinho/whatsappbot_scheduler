from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.db import models
from .models import Client, PhoneNumberClient, PhoneFormatError

class PhoneNumberErrorFixView(View):
    template_name = 'clients/phone_number_errors.html'

    def get(self, request):
        # Filtros
        error_filter = request.GET.get('error')
        search = request.GET.get('search', '').strip()

        clients_qs = Client.objects.exclude(phone_format_error=PhoneFormatError.VALID)
        phones_qs = PhoneNumberClient.objects.exclude(phone_format_error=PhoneFormatError.VALID)

        if error_filter:
            clients_qs = clients_qs.filter(phone_format_error=error_filter)
            phones_qs = phones_qs.filter(phone_format_error=error_filter)
        if search:
            clients_qs = clients_qs.filter(
                models.Q(full_name__icontains=search) |
                models.Q(phone_number__icontains=search)
            )
            phones_qs = phones_qs.filter(
                models.Q(phone_number__icontains=search) |
                models.Q(client__full_name__icontains=search)
            )

        clients_with_errors = clients_qs
        phones_with_errors = phones_qs

        def get_strategy_and_correction(phone, area):
            original = phone or ""
            cleaned = "".join(filter(str.isdigit, original))
            new_area = area or ""
            suggestion = ""
            corrected_phone = cleaned
            corrected_area = new_area
            # Estrategias según error
            if not original:
                suggestion = "Ingrese un número válido."
                corrected_phone = ""
            elif original.startswith('+'):
                # Intentar extraer código de país y número
                digits = cleaned
                if len(digits) > 10:
                    corrected_area = digits[:len(digits)-10]
                    corrected_phone = digits[-10:]
                    suggestion = f"Separado: área {corrected_area}, número {corrected_phone}"
                else:
                    suggestion = "Quite el símbolo '+', solo números."
            elif not cleaned.isdigit():
                suggestion = "No es numérico, se deja vacío."
                corrected_phone = ""
            elif len(cleaned) > 10:
                # Si parece tener código de país
                corrected_area = cleaned[:len(cleaned)-10]
                corrected_phone = cleaned[-10:]
                suggestion = f"Recortado: área {corrected_area}, número {corrected_phone}"
            elif len(cleaned) < 10:
                suggestion = "Menos de 10 dígitos, se deja vacío."
                corrected_phone = ""
            elif any(c for c in original if not c.isdigit() and c not in ['+', ' '] ):
                suggestion = "Elimine caracteres especiales, solo números."
                # Intentar limpiar
                corrected_phone = cleaned if len(cleaned) == 10 else ""
            else:
                suggestion = "Revise el número."
            return suggestion, corrected_area, corrected_phone

        # Anotar estrategias y correcciones a cada objeto
        for c in clients_with_errors:
            suggestion, new_area, new_phone = get_strategy_and_correction(c.phone_number, c.area_code)
            c.suggested_strategy = suggestion
            c.suggested_area = new_area
            c.suggested_phone = new_phone
        for p in phones_with_errors:
            suggestion, new_area, new_phone = get_strategy_and_correction(p.phone_number, p.area_code)
            p.suggested_strategy = suggestion
            p.suggested_area = new_area
            p.suggested_phone = new_phone

        return render(request, self.template_name, {
            'clients': clients_with_errors,
            'phones': phones_with_errors,
            'error_filter': error_filter,
            'search': search,
            'error_choices': PhoneFormatError.choices,
        })

    def post(self, request):
        correction_type = request.POST.get('correction_type')
        updated = 0
        if correction_type == 'clients':
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
            messages.success(request, f'Correcciones aplicadas a {updated} clientes seleccionados.')
        elif correction_type == 'phones':
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
            messages.success(request, f'Correcciones aplicadas a {updated} teléfonos alternos seleccionados.')
        else:
            messages.warning(request, 'No se especificó el tipo de corrección.')
        return redirect('clients:phone_number_errors')
