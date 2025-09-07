def get_strategy_and_correction(phone, area):
    original = phone or ""
    cleaned = "".join(filter(str.isdigit, original))
    new_area = area or ""
    suggestion = ""
    corrected_phone = cleaned
    corrected_area = new_area
    if not original:
        suggestion = "Ingrese un número válido."
        corrected_phone = ""
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
        corrected_phone = ""
    elif any(c for c in original if not c.isdigit() and c not in ['+', ':' ,' ']):
        suggestion = "Elimine caracteres especiales, solo números."
        corrected_phone = cleaned if len(cleaned) == 10 else ""
    elif len(cleaned) > 10:
        corrected_area = cleaned[:len(cleaned)-10]
        corrected_phone = cleaned[-10:]
        suggestion = f"Recortado: área {corrected_area}, número {corrected_phone}"
    elif len(cleaned) < 10:
        suggestion = "Menos de 10 dígitos, se deja vacío."
        corrected_phone = ""
    else:
        suggestion = "Revise el número."
    return suggestion, corrected_area, corrected_phone
