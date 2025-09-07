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

def get_strategy_and_correction(phone, area):
    original = phone or ""
    cleaned = "".join(filter(str.isdigit, original))
    corrected_area = area or ""
    corrected_phone = ""
    suggestion = ""
    if not original:
        suggestion = "Ingrese un número válido."
    elif original.startswith('+'):
        digits = cleaned
        if len(digits) > 10:
            corrected_area = digits[:len(digits)-10]
            corrected_phone = digits[-10:]
            suggestion = f"Separado: área {corrected_area}, número {corrected_phone}"
        else:
            suggestion = "Quite el símbolo '+', solo números."
    elif not cleaned.isdigit():
        suggestion = "No es numérico, se deja vacío."
    elif any(c for c in original if not c.isdigit() and c not in ['+', ':' ,' ']):
        suggestion = "Elimine caracteres especiales, solo números."
    elif len(cleaned) > 10:
        corrected_area = cleaned[:len(cleaned)-10]
        corrected_phone = cleaned[-10:]
        suggestion = f"Recortado: área {corrected_area}, número {corrected_phone}"
    elif len(cleaned) == 10:
        corrected_phone = cleaned
        suggestion = f"Número válido: {corrected_phone}"
    elif len(cleaned) < 10:
        suggestion = "Menos de 10 dígitos, se deja vacío."
    else:
        suggestion = "Revise el número."
    return suggestion, corrected_area, corrected_phone
