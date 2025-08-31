from django.db import models

# Create your models here.

class Client(models.Model):
    class ClientType(models.TextChoices):
        PROSPECT = "prospect", "Prospect"
        CONSOLIDATED = "consolidated", "Consolidated"
        INACTIVE = "inactive", "Inactiv"  # opcional, si quieres manejar clientes caídos
        VIP = "vip", "VIP"  # opcional, clientes especiales
    
    full_name = models.CharField(max_length=100)
    area_code = models.CharField(max_length=5, default="57")
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    first_visit_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    client_type = models.CharField(
        max_length=20,
        choices=ClientType.choices,
        default=ClientType.PROSPECT
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["area_code", "phone_number"], 
                name="unique_client_phone"
            )
        ]

    def __str__(self):
        return f"{self.full_name} (+{self.area_code} {self.phone_number})"
    
