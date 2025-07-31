@echo off
REM Arranca Celery Worker en modo solo (Windows compatible)
start cmd /k "celery -A whatsappbot_scheduler worker --pool=solo --loglevel=info"

REM Arranca Celery Beat en otra ventana
start cmd /k "celery -A whatsappbot_scheduler beat --loglevel=info"

echo Celery worker y beat iniciados en ventanas separadas.
pause
