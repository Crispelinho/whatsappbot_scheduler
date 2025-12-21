import json

# Campos a validar y su longitud máxima (ajusta según tu modelo Client)
FIELDS_LIMITS = {
    "original_phone_number": 20,
    "phone_number": 100,
    "area_code": 20,
    # Agrega aquí otros campos CharField con límite 20 si es necesario
}

with open("data.json", encoding="utf-8") as f:
    data = json.load(f)

for obj in data:
    if obj["model"] == "clients.client":
        for field, maxlen in FIELDS_LIMITS.items():
            value = obj["fields"].get(field)
            if value and len(str(value)) > maxlen:
                print(f"Client pk={obj['pk']} campo '{field}' excede {maxlen} caracteres: '{value}' ({len(str(value))})")
