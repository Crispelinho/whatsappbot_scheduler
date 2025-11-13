
# Create your views here.
from django.shortcuts import render
from django.views import View
from django.db.models import Count, Sum, Max
from notifications_scheduler.models import ScheduledMessage, MessageResponse, ClientScheduledMessage
from sales.models import SaleRecord, Service


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

        qs = SaleRecord.objects.select_related("client", "service", "service__service_type")
        if client_id:
            qs = qs.filter(client__id=client_id)

        # Ventas por mes (total_paid)
        monthly = qs.values("year", "month").annotate(total=Sum("total_paid")).order_by("year", "month")
        monthly_labels = [f"{m['year']}-{m['month']:02d}" for m in monthly]
        monthly_totals = [float(m["total"]) for m in monthly]

        # Servicios más realizados
        top_services_qs = Service.objects.annotate(count=Count("salerecord")).order_by("-count")[:10]
        top_service_labels = [s.name for s in top_services_qs]
        top_service_counts = [s.count for s in top_services_qs]

        # Clientes más frecuentes (solo si no filtramos uno)
        top_clients = []
        if not client_id:
            top_clients = (SaleRecord.objects.values("client__id", "client__full_name")
                           .annotate(visits=Count("id"), last_visit=Max("date"), total_paid=Sum("total_paid"))
                           .order_by("-visits")[:10])

        # Para cliente específico: servicios realizados por ese cliente
        client_services_labels = []
        client_services_counts = []
        if client_id:
            client_services = (qs.values("service__name")
                               .annotate(count=Count("id"))
                               .order_by("-count")[:10])
            client_services_labels = [c["service__name"] for c in client_services]
            client_services_counts = [c["count"] for c in client_services]

        return render(request, self.template_name, {
            "monthly_labels": monthly_labels,
            "monthly_totals": monthly_totals,
            "top_service_labels": top_service_labels,
            "top_service_counts": top_service_counts,
            "top_clients": top_clients,
            "client_id": client_id,
            "client_services_labels": client_services_labels,
            "client_services_counts": client_services_counts,
        })
