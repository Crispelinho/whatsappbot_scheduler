# sales/importers/google_sheets.py

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from decimal import Decimal, InvalidOperation
from clients.models import Client
from sales.models import SaleRecord, Service, Operator, ServiceType

def get_gsheets_client() -> gspread.Client:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials/whatsappbot-scheduler-aecee105645d.json", scope)
    return gspread.authorize(creds)

def download_import_sales_from_sheet()-> (list[dict[str, int | float | str]] | None):
    try:
        sheet = get_gsheets_client().open("Contabilidad").worksheet("Ventas 2025")
    except gspread.exceptions.APIError as e:
        print("❌ Error de acceso a Google Sheets:", e)
        return None, str(e)
    except gspread.exceptions.SpreadsheetNotFound:
        print("❌ Hoja de cálculo 'Contabilidad' no encontrada.")
        return None, "Hoja de cálculo 'Contabilidad' no encontrada."
    # Detectar encabezados reales desde la fila 2
    print("Encabezados detectados:", sheet.row_values(2))

    # Filtrar solo los encabezados útiles para el modelo
    valid_headers = [
        "Item", "Fecha", "Mes", "Año", "Mes-Año", "Cliente", "Teléfono", "Semana",
        "Tipo de Servicio", "Servicio", "Cantidad", "Operaria", "Descuento Servicio",
        "Valor Servicio", "Ajuste", "Total Servicio", "Descuento Salón", "Total Pagado",
        "Pagado", "Método de pago", "Observación", "Errores", "% Para Operaria",
        "% Para Operaria 2", "Liquidado", "Valor liquidado", "Valor a pagar",
        "Valor neto a pagar semana"
    ]

    rows = [
        {k: v for k, v in row.items() if k.strip() in valid_headers}
        for row in sheet.get_all_records(head=2)
        if str(row.get("Item", "")).strip() or str(row.get("Fecha", "")).strip()
    ]

    return rows, None

def import_create(row, counters: dict) -> (bool, str | None):
    try:
        fecha_raw = str(row.get("Fecha", "")).strip()
        if not fecha_raw:
            counters["fallos"] += 1
            return False, "Fecha vacía"

        # Fecha
        fecha = datetime.strptime(fecha_raw, "%d/%m/%Y").date()
        mes = fecha.month
        año = fecha.year
        semana = int(row.get("Semana", 0) or 0)
        mes_año = row.get("Mes-Año", f"{mes:02d}-{año}")

        # Cliente
        nombre_cliente = row["Cliente"].strip()
        telefono = str(row.get("Teléfono", "")).strip()
        client, _ = Client.objects.get_or_create(
            full_name=nombre_cliente,
            phone_number=telefono,
            defaults={"client_type": Client.ClientType.IMPORTED},
        )

        # Operaria
        operaria_nombre = row.get("Operaria", "").strip()
        operator, _ = Operator.objects.get_or_create(name=operaria_nombre, commission_percentage=0.5)

        # Servicio
        tipo_servicio = row.get("Tipo de Servicio", "").strip()
        servicio_nombre = row.get("Servicio", "").strip()
        service_type, _ = ServiceType.objects.get_or_create(name=tipo_servicio, commission_percentage=0.5)
        service, _ = Service.objects.get_or_create(
            name=servicio_nombre,
            defaults={"service_type": service_type, "price": 0, "duration_minutes": 0}
        )

        # Valores
        def parse_money(val, column_name=""):
            try:
                return Decimal(str(val).replace("$", "").replace(".", "").replace(",", "").strip() or "0"), None
            except InvalidOperation as e:
                return Decimal("0"), f"❌ Error decimal en columna {column_name}: {val} ({type(e).__name__})"

        def safe_get_decimal(val, column_name):
            parsed, err = parse_money(val, column_name)
            if err:
                counters["invalid_operations"] += 1
                print(f"Fila {row.get('Item')}: {err}")
            return parsed

        sale, _ = SaleRecord.objects.get_or_create(
            date=fecha,
            month=mes,
            year=año,
            month_year=mes_año,
            week=semana,
            client=client,
            service=service,
            operator=operator,
            quantity=int(row.get("Cantidad", 1) or 1),
            service_discount=safe_get_decimal(row.get("Descuento Servicio"), "Descuento Servicio"),
            service_price=safe_get_decimal(row.get("Valor Servicio"), "Valor Servicio"),
            adjustment=safe_get_decimal(row.get("Ajuste"), "Ajuste"),
            total_service=safe_get_decimal(row.get("Total Servicio"), "Total Servicio"),
            salon_discount=safe_get_decimal(row.get("Descuento Salón"), "Descuento Salón"),
            total_paid=safe_get_decimal(row.get("Total Pagado"), "Total Pagado"),
            paid=row.get("Pagado", "").strip(),
            payment_method=row.get("Método de pago", "").strip(),
            notes=row.get("Observación", "").strip(),
            errors=row.get("Errores", "").strip(),
            worker_percentage=Decimal(str(row.get("% Para Operaria", "0")).replace("%", "").strip() or "0"),
            settled=row.get("Liquidado", "").strip().lower() == "si",
            settled_amount=safe_get_decimal(row.get("Valor liquidado"), "Valor liquidado"),
            amount_to_pay=safe_get_decimal(row.get("Valor a pagar"), "Valor a pagar"),
            net_weekly_payment=safe_get_decimal(row.get("Valor neto a pagar semana"), "Valor neto a pagar semana"),
        )

        counters["exitos"] += 1
        return True, None

    except ValueError as e:
        counters["fallos"] += 1
        counters["value_errors"] += 1
        error_message = f"❌ Error de valor en fila {row.get('Item')}: {e} ({type(e).__name__})"
        print(error_message)
        return False, error_message

    except Exception as e:
        counters["fallos"] += 1
        error_message = f"❌ Error inesperado en fila {row.get('Item')}: {e} ({type(e).__name__}), datos: {row}"
        print(error_message)
        return False, error_message


def import_create_from_sheet():
    rows, error = download_import_sales_from_sheet()
    if error:
        print(f"❌ No se pudo descargar la hoja: {error}")
        return

    counters = {"exitos": 0, "fallos": 0, "invalid_operations": 0, "value_errors": 0}

    for row in rows:
        import_create(row, counters)

    print(f"✅ Importación completada: {counters['exitos']} éxitos, {counters['fallos']} fallos "
          f"({counters['invalid_operations']} errores decimales, {counters['value_errors']} errores de valor).")