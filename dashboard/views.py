from django.db.models import Q
from .forms import OperatorForm
from sales.models import Operator, SaleRecord, Service, ServiceType
from django.views import View
from django.shortcuts import render, redirect
from django.db.models import Count, Sum, Max, Q
from django.utils import timezone
from django.http import HttpResponse
from datetime import datetime
from notifications_scheduler.models import ScheduledMessage, MessageResponse, ClientScheduledMessage
from django.forms import ModelForm, DateTimeInput, Textarea, TextInput, Select, FileInput, ClearableFileInput

# Vista de detalle de todas las ventas con filtros avanzados
class SalesDetailView(View):
    template_name = "dashboard/sales_detail.html"

    def get(self, request):
        operator_id = request.GET.get("operator_id")
        service_type = request.GET.get("service_type")
        week = request.GET.get("week")
        month = request.GET.get("month")
        year = request.GET.get("year")

        filters = Q()
        if operator_id:
            filters &= Q(operator__id=operator_id)
        if service_type:
            filters &= Q(service__service_type__id=service_type)
        if week:
            filters &= Q(week=week)
        if month:
            filters &= Q(month=month)
        if year:
            filters &= Q(year=year)

        sales = SaleRecord.objects.select_related(
            "client", "service", "service__service_type", "operator"
        ).filter(filters).order_by("-date")

        operators_list = Operator.objects.all().order_by('name')
        service_types = ServiceType.objects.all().order_by('name')

        return render(request, self.template_name, {
            "sales": sales,
            "operators_list": operators_list,
            "service_types": service_types,
        })

# Vista de liquidador semanal de operarias
class OperatorLiquidatorView(View):
    template_name = "dashboard/operator_liquidator.html"

    def get(self, request):
        from sales.models import SaleRecord, ServiceType
        week = request.GET.get("week")
        month = request.GET.get("month")
        year = request.GET.get("year")
        service_type = request.GET.get("service_type")
        settled = request.GET.get("settled")
        operator_id = request.GET.get("operator_id")

        filters = {}
        if week:
            filters["week"] = week
        if month:
            filters["month"] = month
        if year:
            filters["year"] = year
        if settled in ("0", "1"):
            filters["settled"] = bool(int(settled))
        if service_type:
            filters["service__service_type__id"] = service_type
        if operator_id:
            filters["operator__id"] = operator_id

        qs = SaleRecord.objects.select_related("operator", "service", "service__service_type").filter(**filters)
        rows = (
            qs.values(
                "operator__id", "operator__name", "week", "month", "year", "service__service_type__name",
                "operator__commission_percentage", "settled"
            )
            .annotate(
                total_sales=Count("id"),
                total_paid=Sum("total_paid"),
                commission_percentage=Max("operator__commission_percentage"),
                amount_to_pay=Sum("amount_to_pay")
            )
            .order_by("-year", "-month", "-week", "operator__name")
        )
        # Formatear moneda
        def fmt_currency(val):
            try:
                if val is None:
                    return "$0.00"
                return f'$'+format(float(val), ',.2f')
            except (ValueError, TypeError):
                return "$0.00"
        for row in rows:
            row["total_paid"] = fmt_currency(row["total_paid"])
            row["amount_to_pay"] = fmt_currency(row["amount_to_pay"])

        # Si se filtra por operaria, mostrar desglose de servicios por semana
        operator_services = []
        operator_obj = None
        if operator_id:
            try:
                operator_obj = Operator.objects.get(id=operator_id)
            except Operator.DoesNotExist:
                operator_obj = None
            # Desglose por semana y servicio
            base_qs = SaleRecord.objects.filter(operator__id=operator_id)
            if week:
                base_qs = base_qs.filter(week=week)
            if month:
                base_qs = base_qs.filter(month=month)
            if year:
                base_qs = base_qs.filter(year=year)
            if service_type:
                base_qs = base_qs.filter(service__service_type__id=service_type)
            if settled in ("0", "1"):
                base_qs = base_qs.filter(settled=bool(int(settled)))
            operator_services = (
                base_qs.values("week", "year", "service__name", "service__service_type__name")
                .annotate(
                    total_servicios=Count("id"),
                    total_pagado=Sum("total_paid"),
                    monto_a_pagar=Sum("amount_to_pay")
                )
                .order_by("-year", "-week", "service__name")
            )
            for s in operator_services:
                s["total_pagado"] = fmt_currency(s["total_pagado"])
                s["monto_a_pagar"] = fmt_currency(s["monto_a_pagar"])

        service_types = ServiceType.objects.all()
        operators_list = Operator.objects.all().order_by('name')
        return render(request, self.template_name, {
            "rows": rows,
            "week": week,
            "month": month,
            "year": year,
            "service_type": service_type,
            "settled": settled,
            "service_types": service_types,
            "operator_id": operator_id,
            "operator_obj": operator_obj,
            "operator_services": operator_services,
            "operators_list": operators_list,
        })

class OperatorCreateView(View):
    template_name = "dashboard/operator_create.html"

    def get(self, request):
        form = OperatorForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = OperatorForm(request.POST)
        if form.is_valid():
            operator = form.save()
            return redirect("dashboard:operators_metrics")
        return render(request, self.template_name, {"form": form})

# Vista de detalle de operaria
class OperatorDetailView(View):
    template_name = "dashboard/operator_detail.html"

    def get(self, request, operator_id):
        from sales.models import Operator, SaleRecord
        from django.db.models import Count, Sum
        operator = Operator.objects.prefetch_related("service_types").get(id=operator_id)
        sales = SaleRecord.objects.filter(operator=operator)
        total_sales = sales.count()
        total_paid = sales.aggregate(total=Sum("total_paid"))['total'] or 0
        services_count = sales.values("service").distinct().count()
        clients_count = sales.values("client").distinct().count()
        # Servicios más realizados
        top_services = (sales.values("service__name")
                        .annotate(count=Count("id"))
                        .order_by("-count")[:10])
        # Clientes más atendidos
        top_clients = (sales.values("client__full_name")
                        .annotate(count=Count("id"))
                        .order_by("-count")[:10])
        def fmt_currency(val):
            try:
                return f'$'+format(float(val), ',.2f') if val is not None else "$0.00"
            except (ValueError, TypeError):
                return "$0.00"
        context = {
            "operator": operator,
            "total_sales": total_sales,
            "total_paid": fmt_currency(total_paid),
            "services_count": services_count,
            "clients_count": clients_count,
            "top_services": top_services,
            "top_clients": top_clients,
        }
        return render(request, self.template_name, context)

# Vista de listado de operarias con métricas
class OperatorsMetricsView(View):
    template_name = "dashboard/operators_metrics.html"

    def get(self, request):
        # Anotar ventas y total pagado por operaria
        operators = (
            Operator.objects.all()
            .prefetch_related("service_types")
            .annotate(
                total_sales=Count("salerecord"),
                total_paid=Sum("salerecord__total_paid")
            )
        )
        # Formatear moneda
        def fmt_currency(val):
            try:
                if val is None:
                    return "$0.00"
                return f'$'+format(float(val), ',.2f')
            except (ValueError, TypeError):
                return "$0.00"
        for op in operators:
            op.formatted_total_paid = fmt_currency(op.total_paid)
        return render(request, self.template_name, {"operators": operators})

class DashboardIndex(View):
    template_name = "dashboard/index.html"

    def get(self, request):
        total = ScheduledMessage.objects.count()
        messages = ClientScheduledMessage.objects.select_related(
            "scheduled_message", "client"
        ).prefetch_related("response")


        pending = MessageResponse.objects.filter(status='pending').count()
        sent = MessageResponse.objects.filter(status='sent').count()
        failed = MessageResponse.objects.filter(status='failed').count()

        # Datos para Chart.js
        chart_labels = ["Sent", "Pending", "Failed"]
        chart_data = [sent, pending, failed]

        return render(request, self.template_name, {
            "total": total,
            "pending": pending,
            "sent": sent,
            "failed": failed,
            "total_message_responses": messages,
            "chart_labels": chart_labels,
            "chart_data": chart_data,
        })


class ClientMetricsView(View):
    template_name = "dashboard/clients_metrics.html"

    def get(self, request):
        client_id = request.GET.get("client_id")
        client_name = request.GET.get("client_name", "").strip()
        service_type_id = request.GET.get("service_type_id")
        granularity = request.GET.get("granularity", "month").lower()  # 'day' | 'week' | 'month'
        start_date_str = request.GET.get("start_date")
        end_date_str = request.GET.get("end_date")

        qs = SaleRecord.objects.select_related("client", "service", "service__service_type")
        if client_id:
            qs = qs.filter(client__id=client_id)
        if client_name:
            qs = qs.filter(client__full_name__icontains=client_name)
        if service_type_id:
            qs = qs.filter(service__service_type__id=service_type_id)
        # Date range filter
        def parse_date(d):
            try:
                return datetime.strptime(d, "%Y-%m-%d").date()
            except Exception:
                return None
        start_date = parse_date(start_date_str) if start_date_str else None
        end_date = parse_date(end_date_str) if end_date_str else None
        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)

        # Export CSV global metrics if requested early (avoid extra work)
        export = request.GET.get("export")

        # Ventas agregadas según granularidad
        chart_labels, chart_totals, chart_label = [], [], "Total Pagado"
        if granularity == "day":
            daily = qs.values("date").annotate(total=Sum("total_paid")).order_by("date")
            chart_labels = [str(d["date"]) for d in daily]
            chart_totals = [float(d["total"]) for d in daily]
        elif granularity == "week":
            weekly = qs.values("year", "week").annotate(total=Sum("total_paid")).order_by("year", "week")
            chart_labels = [f"{w['year']}-W{w['week']:02d}" for w in weekly]
            chart_totals = [float(w["total"]) for w in weekly]
        else:
            monthly = qs.values("year", "month").annotate(total=Sum("total_paid")).order_by("year", "month")
            chart_labels = [f"{m['year']}-{m['month']:02d}" for m in monthly]
            chart_totals = [float(m["total"]) for m in monthly]

        # Servicios más y menos realizados basados en ventas filtradas (qs)
        services_agg = (qs.values("service__name")
                          .annotate(count=Count("id"))
                          .order_by("-count"))
        top_services_qs = list(services_agg[:10])
        least_services_qs = list(qs.values("service__name")
                                   .annotate(count=Count("id"))
                                   .order_by("count")[:10])

        top_service_labels = [s["service__name"] for s in top_services_qs]
        top_service_counts = [s["count"] for s in top_services_qs]
        least_service_labels = [s["service__name"] for s in least_services_qs]
        least_service_counts = [s["count"] for s in least_services_qs]

        # Clientes más frecuentes y menos frecuentes (solo si no filtramos uno o por nombre específico)
        top_clients = []
        least_clients = []
        if not client_id and not client_name:
            # usar qs base filtrado por tipo de servicio si aplica
            base_clients_qs = qs.values("client__id", "client__full_name")
            annotated_clients = (base_clients_qs
                                  .annotate(visits=Count("id"), last_visit=Max("date"), total_paid=Sum("total_paid")))
            top_clients = annotated_clients.order_by("-visits")
            least_clients = annotated_clients.order_by("visits")

        # Para cliente específico: servicios realizados por ese cliente (usando qs ya filtrado)
        client_services_labels = []
        client_services_counts = []
        if client_id or client_name:
            client_services = (qs.values("service__name")
                               .annotate(count=Count("id"))
                               .order_by("-count")[:10])
            client_services_labels = [c["service__name"] for c in client_services]
            client_services_counts = [c["count"] for c in client_services]

        service_types = ServiceType.objects.all()

        # Operarias (top por total pagado y cantidad) respetando filtros
        operator_stats = (qs.values("operator__id", "operator__name")
                           .annotate(total_sales=Count("id"), total_paid=Sum("total_paid"))
                           .order_by("-total_paid"))

        # Formatear moneda en Python para evitar fallo de templatetag
        def fmt_currency(val):
            try:
                if val is None:
                    return "$0.00"
                return f"${float(val):,.2f}"  # separador miles y 2 decimales
            except (ValueError, TypeError):
                return "$0.00"

        formatted_top_clients = [
            {
                **c,
                "formatted_total_paid": fmt_currency(c.get("total_paid")),
            }
            for c in top_clients
        ]

        formatted_least_clients = [
            {
                **c,
                "formatted_total_paid": fmt_currency(c.get("total_paid")),
            }
            for c in least_clients
        ]

        formatted_operator_stats = [
            {
                **o,
                "formatted_total_paid": fmt_currency(o.get("total_paid")),
            }
            for o in operator_stats
        ]

        # Period comparison (only if date range selected)
        previous_period_total = None
        previous_period_change = None
        previous_period_pct = None
        current_period_total = qs.aggregate(total=Sum("total_paid"))['total'] or 0
        if start_date and end_date and start_date < end_date:
            period_days = (end_date - start_date).days + 1
            prev_start = start_date - timezone.timedelta(days=period_days)
            prev_end = start_date - timezone.timedelta(days=1)
            prev_qs = SaleRecord.objects.select_related("service").filter(date__gte=prev_start, date__lte=prev_end)
            if service_type_id:
                prev_qs = prev_qs.filter(service__service_type__id=service_type_id)
            previous_period_total = prev_qs.aggregate(total=Sum("total_paid"))["total"] or 0
            previous_period_change = current_period_total - previous_period_total
            previous_period_pct = (previous_period_change / previous_period_total * 100) if previous_period_total else None

        # Flags para template (no usar métodos en template)
        previous_period_change_negative = previous_period_change is not None and previous_period_change < 0
        previous_period_change_positive = previous_period_change is not None and previous_period_change > 0

        # Handle global CSV export
        if export == "csv":
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="global_metrics.csv"'
            # Write header
            response.write('section,name,count_or_amount\n')
            for lbl, cnt in zip(top_service_labels, top_service_counts):
                response.write(f"top_service,{lbl},{cnt}\n")
            for lbl, cnt in zip(least_service_labels, least_service_counts):
                response.write(f"least_service,{lbl},{cnt}\n")
            for c in formatted_top_clients:
                response.write(f"top_client,{c['client__full_name']},{c['visits']}\n")
            for o in formatted_operator_stats:
                response.write(f"operator,{o['operator__name']},{o['total_sales']}\n")
            return response

        return render(request, self.template_name, {
            "chart_labels": chart_labels,
            "chart_totals": chart_totals,
            "chart_label": chart_label,
            "granularity": granularity,
            "top_service_labels": top_service_labels,
            "top_service_counts": top_service_counts,
            "least_service_labels": least_service_labels,
            "least_service_counts": least_service_counts,
            "service_types": service_types,
            "service_type_id": service_type_id,
            "top_clients": formatted_top_clients,
            "least_clients": formatted_least_clients,
            "client_id": client_id,
            "client_name": client_name,
            "client_services_labels": client_services_labels,
            "client_services_counts": client_services_counts,
            "operator_stats": formatted_operator_stats,
            "start_date": start_date_str or "",
            "end_date": end_date_str or "",
            "previous_period_total": fmt_currency(previous_period_total) if previous_period_total is not None else None,
            "previous_period_change": fmt_currency(previous_period_change) if previous_period_change is not None else None,
            "previous_period_pct": previous_period_pct,
            "previous_period_label": f"{start_date - timezone.timedelta(days=(end_date - start_date).days + 1)} a {start_date - timezone.timedelta(days=1)}" if previous_period_total is not None else None,
            "current_period_total": fmt_currency(current_period_total),
            "previous_period_change_negative": previous_period_change_negative,
            "previous_period_change_positive": previous_period_change_positive,
        })


class ClientDetailMetricsView(View):
    template_name = "dashboard/client_detail_metrics.html"

    def get(self, request, client_id: int):
        start_date_str = request.GET.get("start_date")
        end_date_str = request.GET.get("end_date")
        export = request.GET.get("export")
        def parse_date(d):
            try:
                return datetime.strptime(d, "%Y-%m-%d").date()
            except Exception:
                return None
        start_date = parse_date(start_date_str) if start_date_str else None
        end_date = parse_date(end_date_str) if end_date_str else None

        client_records = (SaleRecord.objects.filter(client__id=client_id)
                           .select_related("client", "service", "service__service_type", "operator")
                           .order_by("date"))
        if start_date:
            client_records = client_records.filter(date__gte=start_date)
        if end_date:
            client_records = client_records.filter(date__lte=end_date)

        if export == "csv":
            # CSV export of filtered client records
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="client_{client_id}_records.csv"'
            headers = ["date", "service", "total_paid", "payment_method", "week", "month", "year"]
            response.write(','.join(headers) + '\n')
            for r in client_records:
                response.write(f"{r.date},{(r.service.name if r.service else '')},{r.total_paid},{r.payment_method},{r.week},{r.month},{r.year}\n")
            return response

        if not client_records.exists():
            return render(request, self.template_name, {"client_id": client_id, "no_data": True, "start_date": start_date_str or "", "end_date": end_date_str or ""})

        count = client_records.count()
        first_record = client_records.first()
        last_record = client_records.last()
        total_paid = client_records.aggregate(total=Sum("total_paid"))["total"] or 0
        avg_paid = (total_paid / count) if count else 0

        # Servicio más realizado
        top_service_data = (client_records.values("service__name")
                            .annotate(times=Count("id"))
                            .order_by("-times")[:1])
        top_service_name = top_service_data[0]["service__name"] if top_service_data else None
        top_service_times = top_service_data[0]["times"] if top_service_data else 0

        # Intervalos entre visitas (en días)
        visit_dates = list(client_records.values_list("date", flat=True))
        intervals = []
        for prev, nxt in zip(visit_dates, visit_dates[1:]):
            intervals.append((nxt - prev).days)
        avg_interval = (sum(intervals) / len(intervals)) if intervals else None

        # Días desde última visita
        days_since_last = (timezone.now().date() - last_record.date).days
        inactive_over_30 = days_since_last > 30

        def fmt_currency(val):
            try:
                return f"${float(val):,.2f}" if val is not None else "$0.00"
            except (ValueError, TypeError):
                return "$0.00"

        context = {
            "client": first_record.client,
            "client_id": client_id,
            "first_service": first_record.service,
            "first_service_date": first_record.date,
            "last_service": last_record.service,
            "last_service_date": last_record.date,
            "last_visit_paid": fmt_currency(last_record.total_paid),
            "total_paid": fmt_currency(total_paid),
            "avg_paid": fmt_currency(avg_paid),
            "top_service_name": top_service_name,
            "top_service_times": top_service_times,
            "avg_interval": avg_interval,
            "days_since_last": days_since_last,
            "inactive_over_30": inactive_over_30,
            "count_visits": count,
            "intervals": intervals,
            "start_date": start_date_str or "",
            "end_date": end_date_str or "",
            # Data for spending evolution chart
            "spending_dates": [str(d) for d in visit_dates],
            "spending_amounts": [float(cr.total_paid) for cr in client_records],
        }
        return render(request, self.template_name, context)


class ScheduledMessageForm(ModelForm):
    class Meta:
        model = ScheduledMessage
        fields = [
            "subject",
            "message_text",
            "start_datetime",
            "send_frequency",
            "client_type",
            "image",
            "video",
        ]
        widgets = {
            "subject": TextInput(attrs={"class": "form-control", "placeholder": "Asunto del mensaje"}),
            "message_text": Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Contenido del mensaje"}),
            "start_datetime": DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "send_frequency": Select(attrs={"class": "form-control"}),
            "client_type": Select(attrs={"class": "form-control"}),
            "image": ClearableFileInput(attrs={"class": "form-control"}),
            "video": ClearableFileInput(attrs={"class": "form-control"}),
        }


class ScheduledMessagesView(View):
    template_name = "dashboard/scheduled_messages.html"

    def get(self, request):
        form = ScheduledMessageForm()
        messages_qs = (
            ScheduledMessage.objects
            .annotate(
                total_msgs=Count("client_messages", distinct=True),
                sent_count=Count("client_messages__response", filter=Q(client_messages__response__status='sent'), distinct=True),
                pending_count=Count("client_messages__response", filter=Q(client_messages__response__status='pending'), distinct=True),
                failed_count=Count("client_messages__response", filter=Q(client_messages__response__status='failed'), distinct=True),
            )
            .order_by("-start_datetime")
        )
        return render(request, self.template_name, {"form": form, "scheduled_messages": messages_qs})

    def post(self, request):
        form = ScheduledMessageForm(request.POST, request.FILES)
        if form.is_valid():
            sm = form.save(commit=False)
            # recipient_count se actualizará luego según asignación real
            sm.recipient_count = 0
            sm.save()
            return redirect("dashboard:scheduled_messages")
        # Re-listar con errores
        messages_qs = (
            ScheduledMessage.objects
            .annotate(
                total_msgs=Count("client_messages", distinct=True),
                sent_count=Count("client_messages__response", filter=Q(client_messages__response__status='sent'), distinct=True),
                pending_count=Count("client_messages__response", filter=Q(client_messages__response__status='pending'), distinct=True),
                failed_count=Count("client_messages__response", filter=Q(client_messages__response__status='failed'), distinct=True),
            )
            .order_by("-start_datetime")
        )
        return render(request, self.template_name, {"form": form, "scheduled_messages": messages_qs})
