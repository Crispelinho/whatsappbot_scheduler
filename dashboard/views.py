
# Create your views here.
from django.shortcuts import render
from django.views import View
from notifications_scheduler.models import ScheduledMessage, MessageResponse, ClientScheduledMessage


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
