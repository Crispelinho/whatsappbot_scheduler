# constants/xpaths.py

# Botón de adjuntar archivo (puede aparecer en español o inglés)
ATTACH_BUTTON = (
    "//button[contains(@aria-label,'Adjunt')]"
    " | //button[contains(@aria-label,'Attach')]"
    " | //span[@data-icon='plus-rounded']/ancestor::button"
)


# Opción de fotos y videos en el menú de adjuntar archivo (soporta div y li, español e inglés)
ATTACH_MEDIA = (
    "//button[@role='menuitem' and (contains(@aria-label,'Fotos y videos') or contains(@aria-label,'Photos & videos'))]"
    " | //button[@role='menuitem' and (.//span[normalize-space()='Fotos y videos'] or .//span[normalize-space()='Photos & videos'])]"
)

# Input de archivos para imagen/video
# FILE_INPUT = (
#     "//input[@type='file' and contains(@accept,'image')]"
#     " | //input[@type='file' and contains(@accept,'video')]"
# )

# Input de archivos (imagen o video)
FILE_INPUT = '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]'

# FILE_INPUT = '//input[@type="file" and contains(@accept,"image")]'
# FILE_INPUT = "//input[@type='file']"

# Botón de enviar archivo adjunto
SEND_BUTTON = '//div[@aria-label="Enviar"] | //div[@aria-label="Send"]'
