from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.http import JsonResponse
from trio import sleep
from notifications_scheduler.models import ScheduledMessage, ClientScheduledMessage, MessageResponse, ResponseCode

class ScheduledMessageDetailView(View):
	template_name = "dashboard/scheduled_message_detail.html"

	def get(self, request, pk):
		msg = get_object_or_404(ScheduledMessage, pk=pk)
		client_msgs = (
			ClientScheduledMessage.objects
			.filter(scheduled_message=msg)
			.select_related("client", "response")
			.order_by("-created_at")
		)
		rows = []
		for cm in client_msgs:
			resp = getattr(cm, "response", None)
			rows.append({
				"client": cm.client,
				"sent_at": cm.sent_at,
				"created_at": cm.created_at,
				"status": resp.status if resp else "pending",
				"response_code": resp.response_code if resp else None,
				"description": resp.description if resp else None,
			})
		return render(request, self.template_name, {"msg": msg, "rows": rows})

class ResendClientMessageView(View):
	def simulate_resend_status(self, cm):
		resp = getattr(cm, "response", None)
		# Si está en 'pending', pasa a 'sent'. Si está en 'sent' o 'failed', pasa a 'pending' y suma retry_count.
		if resp and resp.status == MessageResponse.Status.PENDING:
			status = MessageResponse.Status.SENT
			response_code = ResponseCode.SUCCESS.value
			description = "Mensaje reenviado correctamente (simulado)"
		else:
			status = MessageResponse.Status.PENDING
			response_code = None
			description = "Reenvío en proceso (simulado)"
			cm.retry_count = (cm.retry_count or 0) + 1
			cm.save(update_fields=["retry_count"])

		if resp:
			resp.status = status
			resp.response_code = response_code
			resp.description = description
			resp.save(update_fields=["status", "response_code", "description", "updated_at"])
		else:
			resp = MessageResponse.objects.create(
				client_message=cm,
				status=status,
				response_code=response_code,
				description=description
			)
		return resp

	def post(self, request, pk, client_id):
		from notifications_scheduler.models import ClientScheduledMessage
		cm = ClientScheduledMessage.objects.filter(scheduled_message_id=pk, client_id=client_id).select_related('response', 'client').first()
		if not cm:
			if request.headers.get('x-requested-with') == 'XMLHttpRequest':
				return JsonResponse({'success': False, 'error': 'No se encontró el mensaje para reenviar.'}, status=404)
			messages.error(request, "No se encontró el mensaje para reenviar.")
			return HttpResponseRedirect(reverse('dashboard:scheduled_message_detail', args=[pk]))

		resp = self.simulate_resend_status(cm)

		if request.headers.get('x-requested-with') == 'XMLHttpRequest':
			return JsonResponse({
				'success': True,
				'message': f'Reenvío solicitado para {cm.client.full_name}.',
				'status': resp.status,
				'response_code': resp.response_code,
				'description': resp.description,
				'retry_count': cm.retry_count,
			})
		messages.success(request, f"Reenvío solicitado para {cm.client.full_name}.")
		return HttpResponseRedirect(reverse('dashboard:scheduled_message_detail', args=[pk]))
