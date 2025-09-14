# constants/xpaths.py

# Botón de adjuntar archivo (puede aparecer en español o inglés)
ATTACH_BUTTON = "//div[@role='button' and contains(@aria-label, 'Adjunt')] | //div[@role='button' and contains(@aria-label, 'Attach')]"

# Input de archivos (imagen o video)
FILE_INPUT = '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]'

# Botón de enviar archivo adjunto
SEND_BUTTON = '//div[@aria-label="Enviar"] | //div[@aria-label="Send"]'
