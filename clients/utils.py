from abc import ABC, abstractmethod
import phonenumbers
import re
import pycountry
from phonenumbers.phonenumberutil import region_code_for_number

# --- STRATEGY PATTERN FOR PHONE CORRECTION ---
class PhoneCorrectionStrategy(ABC):
    @abstractmethod
    def applies(self, phone, area) -> bool:
        pass
    @abstractmethod
    def correct(self, phone, area) -> list[tuple[str, str, str]]:
        pass

class EmptyPhoneStrategy(PhoneCorrectionStrategy):
    def applies(self, phone, area)-> bool:
        return not (phone or "").strip()
    def correct(self, phone, area)-> list[tuple[str, str, str]]:
        return [("Ingrese un número válido.", '', '')]

class StartsPlusStrategy(PhoneCorrectionStrategy):
    def applies(self, phone, area) -> bool:
        return (phone or "").startswith('+')

    def correct(self, phone, area) -> list[tuple[str, str, str]]:
        digits = ''.join(filter(str.isdigit, phone or ""))

        # Si no es válido, delegar a estrategia de caracteres especiales
        if SpecialCharsStrategy().applies(phone, area):
            return SpecialCharsStrategy().correct(phone, area)

        return [("Quite el símbolo '+', solo números.", get_area_code_for_number(digits), digits)]

class NotNumericStrategy(PhoneCorrectionStrategy):
    def applies(self, phone, area)-> bool:
        return any(c.isalpha() for c in phone)
    def correct(self, phone, area)-> list[tuple[str, str, str]]:
        return [("No es numérico, se deja vacío.", '', '')]

class SpecialCharsStrategy(PhoneCorrectionStrategy):
    def applies(self, phone, area)-> bool:
        return any(c for c in (phone or "") if not c.isdigit() and c not in ['+', ':', ' '])
    def correct(self, phone, area)-> list[tuple[str, str, str]]:
        if len(phone) > 10:
            if TooLongStrategy().applies(phone, area):
                return TooLongStrategy().correct(phone, area)
        return [("Elimine caracteres especiales, solo números.", '', '')]

class InternacionalNumberStrategy(PhoneCorrectionStrategy):
    def applies(self, phone, area) -> bool:
        phone = phone.strip()
        if not phone or not phone.startswith('+'):
            phone = "+" + (phone or "")
        print(f"InternacionalNumberStrategy checking {phone}")
        try:
            number = phonenumbers.parse(phone)  # Asumiendo Colombia como país base
            print(number)
            return phonenumbers.is_valid_number(number)
        except phonenumbers.NumberParseException as e:
            print(f"Error parsing number: {e}")
            return False
    def correct(self, phone, area) -> list[tuple[str, str, str]]:
        phone = phone.strip()
        if not phone or not phone.startswith('+'):
            phone = "+" + (phone or "")
        print(f"InternacionalNumberStrategy correcting {phone}")
        try:
            number = phonenumbers.parse(phone)  # Asumiendo Colombia como país base
            if phonenumbers.is_valid_number(number):
                corrected_area = str(number.country_code)
                corrected_phone = str(number.national_number)
                region_code = region_code_for_number(number)
                country = pycountry.countries.get(alpha_2=region_code)

                return [(f"Número válido: área {corrected_area}, número {corrected_phone}, código de región {region_code}, país {country}", corrected_phone, corrected_area)]
        except phonenumbers.NumberParseException:
            pass
        return [("Número inválido.", '', '')]

class TooLongStrategy(PhoneCorrectionStrategy):
    def applies(self, phone, area) -> bool:
        cleaned = ''.join(filter(str.isdigit, phone or ""))
        return len(cleaned) > 10
    def correct(self, phone, area) -> list[tuple[str, str, str]]:
        cleaned = ''.join(filter(str.isdigit, phone or ""))
        corrected_area = cleaned[:len(cleaned)-10]
        corrected_phone = cleaned[-10:]
        print(f"TooLongStrategy: area {corrected_area}, phone {corrected_phone}")
        if len(corrected_phone) != 10 or len(corrected_area) > 3:
            print("Delegando a otra estrategia...")
            if MoreThanOneNumbers().applies(phone, area):
                return MoreThanOneNumbers().correct(phone, area)
            if InternacionalNumberStrategy().applies(phone, area):
                return InternacionalNumberStrategy().correct(phone, area) 

        # Deprecated: manejar más de un número en TooLongStrategy
        # if len(corrected_phone) > 10: 
        #     n1, n2, n3 = split_and_clean_phones(corrected_phone)
        #     corrected_n1 = create_results_corrected(n1) 
        #     corrected_n2 = create_results_corrected(n2)
        #     corrected_n3 = create_results_corrected(n3)
        #     results = [corrected_n1, corrected_n2, corrected_n3]
        #     return results
        return [(f"Recortado: área {corrected_area}, número {corrected_phone}", corrected_area, corrected_phone)]
class MoreThanOneNumbers(TooLongStrategy):
    _regular_ex = r"\s*:::+\s*|\s*[:;|\n]+\s*"
    def applies(self, phone, area) -> bool:
        phone = phone.strip()
        print(f"MoreThanOneNumbers checking {phone}")
        parts = re.split(self._regular_ex, phone or "")
        return len(parts) > 1
    def correct(self, phone, area) -> list[tuple[str, str, str]]:
        print(f"MoreThanOneNumbers correcting {phone}")
        parts = re.split(self._regular_ex, phone or "")
        parts_cleaned = [p.strip() for p in parts if p.strip()]
        results = []
        for part in parts_cleaned:
            part = part.strip().replace(' ', '')
            print(f"  Parte: {part}")
            corrected_area = get_area_code_for_number(part)
            corrected_phone = part[-10:] if len(part) > 10 else part
            results.append((f"Número separado: área {corrected_area}, número {corrected_phone}", corrected_phone, corrected_area))
        return results if results else [("No se encontraron números válidos.", '', '')]
class ValidPhoneStrategy(PhoneCorrectionStrategy):
    def applies(self, phone, area)-> bool:
        cleaned = ''.join(filter(str.isdigit, phone or ""))
        return len(cleaned) == 10
    def correct(self, phone, area) -> list[tuple[str, str, str]]:
        cleaned = ''.join(filter(str.isdigit, phone or ""))
        corrected_area = get_area_code_for_number(cleaned)
        return [(f"Número válido: {cleaned}", corrected_area, cleaned)]

class TooShortStrategy(PhoneCorrectionStrategy):
    def applies(self, phone, area)-> bool:
        cleaned = ''.join(filter(str.isdigit, phone or ""))
        return len(cleaned) < 10 and len(cleaned) > 0
    def correct(self, phone, area) -> list[tuple[str, str, str]]:
        return [("Menos de 10 dígitos, se deja vacío.", '', '')]

class FallbackStrategy(PhoneCorrectionStrategy):
    def applies(self, phone, area)-> bool:
        return True
    def correct(self, phone, area) -> list[tuple[str, str, str]]:
        return [("Revise el número.", area or "", "")]

# Estrategias en orden de prioridad
PHONE_STRATEGIES = [
    EmptyPhoneStrategy(),
    ValidPhoneStrategy(),
    StartsPlusStrategy(),
    NotNumericStrategy(),
    SpecialCharsStrategy(),
    MoreThanOneNumbers(),
    InternacionalNumberStrategy(),
    TooLongStrategy(),
    TooShortStrategy(),
    FallbackStrategy(),
]

def get_strategy_and_correction(phone, area) -> list[tuple[str, str, str]]:
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

# Lógica deprecada para separar hasta 3 números en un solo campo
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

# Lógica deprecada para crear resultados corregidos
def create_results_corrected(phone) -> tuple[str, str, str]:
    corrected_area = get_area_code_for_number(phone)
    return get_strategy_and_correction(phone, corrected_area)[0] 