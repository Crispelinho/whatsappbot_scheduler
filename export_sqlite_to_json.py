import os
import sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "whatsappbot_scheduler.settings")
import django
django.setup()
from django.core.management import call_command

if __name__ == "__main__":
    with open("data.json", "w", encoding="utf-8") as f:
        call_command(
            "dumpdata",
            exclude=["auth.permission", "contenttypes", "sessions.session"],
            indent=2,
            stdout=f
        )
    print("Exportación completada en data.json (UTF-8)")
