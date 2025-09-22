# sales/views.py
from django.shortcuts import render
from sales.importers.google_sheets import download_import_sales_from_sheet, import_create


def sale_pre_import(request):
    # Renderiza primero una pantalla de carga
    if request.GET.get("loading") != "false":
        return render(request, "sales/loading.html")

    rows, error = download_import_sales_from_sheet()
    if error:
        return render(request, "sales/pre_importacion.html", {"error": error})
    return render(request, "sales/pre_importacion.html", {"rows": rows})

def sale_import(request):
    if request.method == "POST":
        rows, error = download_import_sales_from_sheet()
        if error:
            return render(request, "sales/resultado_importacion.html", {
                "rows": [],
                "errores": [{"error": error}],
            })

        errores_por_fila = []
        counters = {"exitos": 0, "fallos": 0, "invalid_operations": 0, "value_errors": 0}

        for i, row in enumerate(rows):
            ok, err = import_create(row, counters)  # procesar fila individual
            if not ok:
                row["Error"] = err
                errores_por_fila.append(row)
                counters["fallos"] += 1
            else:
                row["Error"] = ""
                counters["exitos"] += 1

        return render(request, "sales/resultado_importacion.html", {
            "rows": rows,
            "errores": errores_por_fila,
            "counters": counters,
        })

def dashboard_view(request):
    return render(request, 'sales/dashboard.html')  # ← esta plantilla extiende base.html
