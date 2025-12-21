
from clients.models import Client
from sales.models import Service, Operator
from django.utils.dateparse import parse_datetime
from django.shortcuts import redirect

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import Appointment
from .importers import download_import_appointments_from_sheet, import_create_appointment


def appointment_pre_import(request):
    # Mostrar pantalla de carga si no se ha pasado loading=false
    if request.GET.get("loading") != "false":
        return render(request, "appointments/loading.html")

    rows, error = download_import_appointments_from_sheet()
    if error:
        return render(request, "appointments/pre_importacion.html", {"error": error})
    return render(request, "appointments/pre_importacion.html", {"rows": rows})

@csrf_exempt
def appointment_import(request):
    if request.method == "POST":
        rows, error = download_import_appointments_from_sheet()
        if error:
            return render(request, "appointments/resultado_importacion.html", {
                "rows": [],
                "errores": [{"error": error}],
            })

        errores_por_fila = []
        counters = {"exitos": 0, "fallos": 0}

        for i, row in enumerate(rows):
            ok, err = import_create_appointment(row, counters)
            if not ok:
                row["Error"] = err
                errores_por_fila.append(row)
                counters["fallos"] += 1
            else:
                row["Error"] = ""
                counters["exitos"] += 1

        return render(request, "appointments/resultado_importacion.html", {
            "rows": rows,
            "errores": errores_por_fila,
            "counters": counters,
        })
    else:
        return render(request, "appointments/resultado_importacion.html", {"rows": [], "errores": [], "counters": {}})

def appointment_list(request):
    if request.method == "POST":
        client_name = request.POST.get("client", "").strip()
        service_name = request.POST.get("service", "").strip()
        operator_name = request.POST.get("operator", "").strip()
        scheduled_datetime = request.POST.get("scheduled_datetime")
        duration_minutes = request.POST.get("duration_minutes", 60)
        notes = request.POST.get("notes", "")
        status = request.POST.get("status", "scheduled")

        client, _ = Client.objects.get_or_create(full_name=client_name)
        service, _ = Service.objects.get_or_create(name=service_name)
        operator = None
        if operator_name:
            operator, _ = Operator.objects.get_or_create(name=operator_name)
        # scheduled_datetime viene en formato 'YYYY-MM-DDTHH:MM'
        dt = parse_datetime(scheduled_datetime.replace('T', ' '))
        Appointment.objects.create(
            client=client,
            service=service,
            operator=operator,
            scheduled_datetime=dt,
            duration_minutes=duration_minutes,
            notes=notes,
            status=status
        )
        return redirect('appointment_list')

    appointments = Appointment.objects.all()
    return render(request, 'appointments/appointment_list.html', {'appointments': appointments})
