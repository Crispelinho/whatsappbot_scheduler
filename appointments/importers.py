import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from clients.models import Client
from sales.models import Service, Operator
from .models import Appointment, StatusAppointment

def get_gsheets_client() -> gspread.Client:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials/whatsappbot-scheduler-aecee105645d.json", scope)
    return gspread.authorize(creds)

def download_import_appointments_from_sheet() -> (list[dict], str | None):
    try:
        sheet = get_gsheets_client().open("Contabilidad").worksheet("Nueva Agenda de Citas")
    except gspread.exceptions.APIError as e:
        print("❌ Error de acceso a Google Sheets:", e)
        return None, str(e)
    except gspread.exceptions.SpreadsheetNotFound:
        print("❌ Hoja de cálculo 'Contabilidad' no encontrada.")
        return None, "Hoja de cálculo 'Contabilidad' no encontrada."
    valid_headers = [
        'Fecha', 'Día semana', 'Mes', 'Semana', 'Cliente', 'Hora', 'Hora M', 'Servicio', 'Tipo Servicio', 'Estado'
    ]
    rows = [
        {k: v for k, v in row.items() if k.strip() in valid_headers}
        for row in sheet.get_all_records(head=1)
        if str(row.get("Fecha", "")).strip() or str(row.get("Cliente", "")).strip()
    ]
    return rows, None

def import_create_appointment(row, counters: dict) -> (bool, str | None):
    try:
        fecha_raw = str(row.get("Fecha", "")).strip()
        if not fecha_raw:
            counters["fallos"] += 1
            return False, "Fecha vacía"
        date = datetime.strptime(fecha_raw, "%d/%m/%Y").date()
        client_name = row["Cliente"].strip()
        client, _ = Client.objects.get_or_create(full_name=client_name)
        service_name = row["Servicio"].strip()
        service, _ = Service.objects.get_or_create(name=service_name)
        operator = None
        scheduled_time = row["Hora M"].strip() or row["Hora"].strip()
        dt_str = f"{fecha_raw} {scheduled_time}"
        try:
            scheduled_datetime = datetime.strptime(dt_str, "%d/%m/%Y %H:%M")
        except Exception:
            scheduled_datetime = datetime.strptime(fecha_raw, "%d/%m/%Y")
        # Mapear estado en español a código interno
        status_map = {tag.value[1]: tag.value[0] for tag in StatusAppointment}
        estado_excel = row.get("Estado", "").strip()
        status_appointment = status_map.get(estado_excel, "SCHEDULED")
        # Validar que el status sea uno de los códigos válidos
        valid_statuses = set(status_map.values())
        if status_appointment not in valid_statuses:
            print(f"⚠️ Estado '{estado_excel}' no reconocido, usando 'SCHEDULED'.")
            status_appointment = "SCHEDULED"
        # Log para depuración
        print(f"Importando cita: cliente={client_name}, servicio={service_name}, fecha={fecha_raw}, status={status_appointment}")
        appointment, _ = Appointment.objects.update_or_create(
            client=client,
            service=service,
            scheduled_datetime=scheduled_datetime,
            defaults={
                'operator': operator,
                'duration_minutes': 60,
                'notes': '',
                'status': status_appointment,
            }
        )
        counters["exitos"] += 1
        return True, None
    except Exception as e:
        counters["fallos"] += 1
        error_message = f"❌ Error inesperado: {e} ({type(e).__name__}), datos: {row}"
        print(error_message)
        return False, error_message

def import_create_appointments_from_sheet():
    rows, error = download_import_appointments_from_sheet()
    if error:
        print(f"❌ No se pudo descargar la hoja: {error}")
        return
    counters = {"exitos": 0, "fallos": 0}
    for row in rows:
        import_create_appointment(row, counters)
    print(f"✅ Importación completada: {counters['exitos']} éxitos, {counters['fallos']} fallos")
