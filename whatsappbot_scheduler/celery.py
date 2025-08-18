from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsappbot_scheduler.settings')

app = Celery('whatsappbot_scheduler')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# 🔑 Este scheduler guarda las tareas en la base de datos en vez de en celerybeat-schedule
app.conf.beat_scheduler = 'django_celery_beat.schedulers:DatabaseScheduler'
