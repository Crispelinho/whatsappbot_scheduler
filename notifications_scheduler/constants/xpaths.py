# constants/xpaths.py

# Botón de adjuntar archivo (puede aparecer en español o inglés)
ATTACH_BUTTON = (
    "//button[contains(@aria-label,'Adjunt')]"
    " | //button[contains(@aria-label,'Attach')]"
    " | //span[@data-icon='plus-rounded']/ancestor::button"
)

# Opción de fotos y videos en el menú de adjuntar archivo
ATTACH_MEDIA = (
    "//li[@role='button']//span[normalize-space()='Fotos y videos']/ancestor::li"
    " | //li[@role='button']//span[normalize-space()='Photos & videos']/ancestor::li"
)

# FILE_INPUT = '//input[@type="file" and contains(@accept,"image")]'
# Input de archivos (imagen o video)
FILE_INPUT = '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]'

# FILE_INPUT = "//input[@type='file']"

# Botón de enviar archivo adjunto
SEND_BUTTON = '//div[@aria-label="Enviar"] | //div[@aria-label="Send"]'
