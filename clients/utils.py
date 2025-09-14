from abc import ABC, abstractmethod

# --- STRATEGY PATTERN FOR PHONE CORRECTION ---
class PhoneCorrectionStrategy(ABC):
    @abstractmethod
    def applies(self, phone, area):
        pass
    @abstractmethod
    def correct(self, phone, area):
        pass

class EmptyPhoneStrategy(PhoneCorrectionStrategy):
    def applies(self, phone, area):
        return not (phone or "").strip()
    def correct(self, phone, area):
        return ("Ingrese un número válido.", area or "", "")

class StartsPlusStrategy(PhoneCorrectionStrategy):
    def applies(self, phone, area):
        return (phone or "").startswith('+')
    def correct(self, phone, area):
        digits = ''.join(filter(str.isdigit, phone or ""))
        if len(digits) > 10:
            corrected_area = digits[:len(digits)-10]
            corrected_phone = digits[-10:]
            return (f"Separado: área {corrected_area}, número {corrected_phone}", corrected_area, corrected_phone)
        else:
            return ("Quite el símbolo '+', solo números.", area or "", "")

class NotNumericStrategy(PhoneCorrectionStrategy):
    def applies(self, phone, area):
        cleaned = ''.join(filter(str.isdigit, phone or ""))
        return phone and not cleaned.isdigit()
    def correct(self, phone, area):
        return ("No es numérico, se deja vacío.", area or "", "")

class SpecialCharsStrategy(PhoneCorrectionStrategy):
    def applies(self, phone, area):
        return any(c for c in (phone or "") if not c.isdigit() and c not in ['+', ':', ' '])
    def correct(self, phone, area):
        return ("Elimine caracteres especiales, solo números.", area or "", "")

class TooLongStrategy(PhoneCorrectionStrategy):
    def applies(self, phone, area):
        cleaned = ''.join(filter(str.isdigit, phone or ""))
        return len(cleaned) > 10
    def correct(self, phone, area):
        cleaned = ''.join(filter(str.isdigit, phone or ""))
        corrected_area = cleaned[:len(cleaned)-10]
        corrected_phone = cleaned[-10:]
        return (f"Recortado: área {corrected_area}, número {corrected_phone}", corrected_area, corrected_phone)

class ValidPhoneStrategy(PhoneCorrectionStrategy):
    def applies(self, phone, area):
        cleaned = ''.join(filter(str.isdigit, phone or ""))
        return len(cleaned) == 10
    def correct(self, phone, area):
        cleaned = ''.join(filter(str.isdigit, phone or ""))
        return (f"Número válido: {cleaned}", area or "", cleaned)

class TooShortStrategy(PhoneCorrectionStrategy):
    def applies(self, phone, area):
        cleaned = ''.join(filter(str.isdigit, phone or ""))
        return len(cleaned) < 10 and len(cleaned) > 0
    def correct(self, phone, area):
        return ("Menos de 10 dígitos, se deja vacío.", area or "", "")

class FallbackStrategy(PhoneCorrectionStrategy):
    def applies(self, phone, area):
        return True
    def correct(self, phone, area):
        return ("Revise el número.", area or "", "")

# Estrategias en orden de prioridad
PHONE_STRATEGIES = [
    EmptyPhoneStrategy(),
    StartsPlusStrategy(),
    NotNumericStrategy(),
    SpecialCharsStrategy(),
    TooLongStrategy(),
    ValidPhoneStrategy(),
    TooShortStrategy(),
    FallbackStrategy(),
]

def get_strategy_and_correction(phone, area):
    for strategy in PHONE_STRATEGIES:
        if strategy.applies(phone, area):
            return strategy.correct(phone, area)

def get_area_code_for_number(phone):
    """
    Dado un número (string de dígitos), retorna el código de área (asume Colombia: 57 si 10 dígitos, o los dígitos extra si >10).
    """
    if not phone:
        return ''
    digits = ''.join(filter(str.isdigit, phone))
    if len(digits) > 10:
        return digits[:len(digits)-10]
    return '57' if len(digits) == 10 else ''
import re

def split_and_clean_phones(raw_value):
    """
    Separa un string de números usando :::, :, ;, |, o saltos de línea como separadores.
    Devuelve hasta tres números limpios (sin espacios extra).
    """
    if not raw_value:
        return None, None, None
    # Separadores posibles
    parts = re.split(r"\s*:::+\s*|\s*[:;|\n]+\s*", raw_value)
    # Limpiar y filtrar vacíos
    cleaned = [p.strip() for p in parts if p.strip()]
    # Devolver hasta tres
    return (
        cleaned[0] if len(cleaned) > 0 else None,
        cleaned[1] if len(cleaned) > 1 else None,
        cleaned[2] if len(cleaned) > 2 else None,
    )

