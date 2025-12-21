from sales.models import SaleRecord
from decimal import Decimal, InvalidOperation

decimal_fields = [
    'service_discount', 'service_price', 'adjustment', 'total_service',
    'salon_discount', 'total_paid', 'worker_percentage', 'settled_amount',
    'amount_to_pay', 'net_weekly_payment'
]

errores = []
for sale in SaleRecord.objects.all():
    for field in decimal_fields:
        value = getattr(sale, field)


