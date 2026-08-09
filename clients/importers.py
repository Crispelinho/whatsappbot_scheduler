import gspread
from oauth2client.service_account import ServiceAccountCredentials
from clients.models import Client
from datetime import datetime

def get_gsheets_client() -> gspread.Client:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials/whatsappbot-scheduler-aecee105645d.json", scope)
    return gspread.authorize(creds)

def download_import_clients_from_sheet() -> (list[dict], str | None):
    try:
        sheet = get_gsheets_client().open("Contabilidad").worksheet("Clientes")
    except gspread.exceptions.APIError as e:
        print("❌ Error de acceso a Google Sheets:", e)
        return None, str(e)
    except gspread.exceptions.SpreadsheetNotFound:
        print("❌ Hoja de cálculo 'Contabilidad' no encontrada.")
        return None, "Hoja de cálculo 'Contabilidad' no encontrada."
    all_records = sheet.get_all_records(head=1)
    rows = [row for row in all_records if str(row.get("Nombre", "")).strip() or str(row.get("Teléfono", "")).strip()]
    return rows, None

def import_create_client(row, counters: dict) -> (bool, str | None):
    try:
        name = row.get("Nombres", "").strip()
        phone = row.get("Teléfono", "").strip()
        email = row.get("Email", "").strip()
        if not name and not phone:
            counters["fallos"] += 1
            return False, "Sin nombre ni teléfono"
        client, created = Client.objects.get_or_create(phone_number=phone, defaults={"full_name": name, "email": email})
        if not created:
            return False, "Ya existe"
        counters["exitos"] += 1
        return True, None
    except Exception as e:
        counters["fallos"] += 1
        return False, f"Error inesperado: {e}"