# constants/xpaths.py

# Botón de adjuntar archivo (puede aparecer en español o inglés)
ATTACH_BUTTON = (
    "//button[contains(@aria-label,'Adjunt')]"
    " | //button[contains(@aria-label,'Attach')]"
    " | //span[@data-icon='plus-rounded']/ancestor::button"
)
# Input de archivos (imagen o video)
FILE_INPUT = '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]'

# Botón de enviar archivo adjunto
SEND_BUTTON = '//div[@aria-label="Enviar"] | //div[@aria-label="Send"]'
