import secrets
import string
from django.db import models

# Create your models here.

def generate_unknown_name(self, length: int = 10) -> str:
    chars = string.ascii_letters + string.digits
    random_part = "".join(secrets.choice(chars) for _ in range(length))
    return f"UNKNOWN_{random_part}"

class PhoneFormatError(models.TextChoices):
    VALID = "valid", "Válido"
    NOT_NUMERIC = "not_numeric", "No son números"
    TOO_LONG = "too_long", "Más de 10 dígitos"
    TOO_SHORT = "too_short", "Menos de 10 dígitos"
    STARTS_PLUS = "starts_plus", "Comienza por +"
    SPECIAL_CHARS = "special_chars", "Contiene caracteres especiales"
    EMPTY = "empty", "Vacío"

class Client(models.Model):
    class ClientType(models.TextChoices):
        PROSPECT = "prospect", "Prospect"
        CONSOLIDATED = "consolidated", "Consolidated"
        INACTIVE = "inactive", "Inactiv"  # opcional, si quieres manejar clientes caídos
        VIP = "vip", "VIP"  # opcional, clientes especiales
    
    full_name = models.CharField(max_length=100, default=generate_unknown_name)
    area_code = models.CharField(max_length=5, default="57")
    original_area_code = models.CharField(max_length=10, blank=True, null=True, help_text="Código de área original para histórico.")
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    original_phone_number = models.CharField(max_length=20, blank=True, null=True, help_text="Valor original del número para histórico.")
    second_area_code = models.CharField(max_length=5, blank=True, null=True)
    second_phone_number = models.CharField(max_length=20, blank=True, null=True)
    third_area_code = models.CharField(max_length=5, blank=True, null=True)
    third_phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    first_visit_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    client_type = models.CharField(
        max_length=20,
        choices=ClientType.choices,
        default=ClientType.PROSPECT
    )
    phone_format_error = models.CharField(max_length=20, choices=PhoneFormatError.choices, default=PhoneFormatError.VALID)
    primary_phone_match = models.BooleanField(default=True)

    # class Meta:
    #     constraints = [
    #         models.UniqueConstraint(
    #             fields=["area_code", "phone_number"], 
    #             name="unique_client_phone"
    #         )
    #     ]


    @staticmethod
    def validate_phone_format(phone_number):
        """
        Valida el formato y retorna el tipo de error (ENUM).
        """
        if not phone_number:
            return PhoneFormatError.EMPTY
        if phone_number.startswith('+'):
            return PhoneFormatError.STARTS_PLUS
        cleaned = "".join(filter(str.isdigit, phone_number))
        if not cleaned.isdigit():
            return PhoneFormatError.NOT_NUMERIC
        if any(c for c in phone_number if not c.isdigit() and c not in ['+', ' '] ):
            return PhoneFormatError.SPECIAL_CHARS
        if len(cleaned) > 10:
            return PhoneFormatError.TOO_LONG
        if len(cleaned) < 10:
            return PhoneFormatError.TOO_SHORT
        return PhoneFormatError.VALID

    def check_primary_phone_match(self):
        """
        Retorna True si el phone_number y area_code del Client coinciden con el PhoneNumberClient marcado como primario.
        """
        primary = self.phone_numbers.filter(is_primary=True).first()
        if not primary:
            return False
        cleaned = "".join(filter(str.isdigit, self.phone_number)) if self.phone_number else None
        return (
            cleaned == primary.phone_number and self.area_code == primary.area_code
        )

    def save(self, *args, **kwargs):
        """Validar phone_number principal y marcar consistencias"""
        format_error = self.validate_phone_format(self.phone_number)
        is_match = self.check_primary_phone_match()
        if format_error == PhoneFormatError.VALID and self.phone_number:
            self.phone_number = "".join(filter(str.isdigit, self.phone_number))
        self.phone_format_error = format_error
        self.primary_phone_match = is_match
        super().save(*args, **kwargs)

    def __str__(self):
        return f"({self.id}) {self.full_name} ({self.area_code} {self.phone_number})"

class PhoneNumberClient(models.Model):
    client = models.ForeignKey('Client', on_delete=models.CASCADE, related_name='phone_numbers')
    phone_number = models.CharField(max_length=20)
    original_phone_number = models.CharField(max_length=20, blank=True, null=True, help_text="Valor original del número para histórico.")
    area_code = models.CharField(max_length=10, blank=True, null=True)
    original_area_code = models.CharField(max_length=10, blank=True, null=True, help_text="Código de área original para histórico.")
    is_primary = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    phone_format_error = models.CharField(max_length=20, choices=PhoneFormatError.choices, default=PhoneFormatError.VALID)

    class Meta:
        unique_together = ('client', 'area_code' ,'phone_number')
        verbose_name = 'Client Phone Number'
        verbose_name_plural = 'Client Phone Numbers'

    @staticmethod
    def validate_phone_format(phone_number):
        """
        Valida el formato y retorna el tipo de error (ENUM).
        """
        if not phone_number:
            return PhoneFormatError.EMPTY
        if phone_number.startswith('+'):
            return PhoneFormatError.STARTS_PLUS
        cleaned = "".join(filter(str.isdigit, phone_number))
        if not cleaned.isdigit():
            return PhoneFormatError.NOT_NUMERIC
        if any(c for c in phone_number if not c.isdigit() and c not in ['+', ' '] ):
            return PhoneFormatError.SPECIAL_CHARS
        if len(cleaned) > 10:
            return PhoneFormatError.TOO_LONG
        if len(cleaned) < 10:
            return PhoneFormatError.TOO_SHORT
        return PhoneFormatError.VALID

    def check_primary_phone_match(self):
        """
        Retorna True si el phone_number y area_code coinciden con el Client principal.
        """
        client_main = self.client
        cleaned = "".join(filter(str.isdigit, self.phone_number)) if self.phone_number else None
        return (
            cleaned == client_main.phone_number and self.area_code == client_main.area_code
        )

    def save(self, *args, **kwargs):
        """Validar formato y coincidencia con el cliente principal"""
        format_error = self.validate_phone_format(self.phone_number)
        self.phone_format_error = format_error
        if format_error == PhoneFormatError.VALID and self.phone_number:
            self.phone_number = "".join(filter(str.isdigit, self.phone_number))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.client} - {self.phone_number}{' (primary)' if self.is_primary else ''}"

