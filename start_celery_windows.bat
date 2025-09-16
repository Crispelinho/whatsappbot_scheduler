@echo off
REM Activar virtualenv
call C:\Users\HP\Documents\Proyectos\whatsappbot_scheduler\venv\Scripts\activate.bat

REM Arranca Celery Worker
start cmd /k "celery -A whatsappbot_scheduler worker --pool=solo --loglevel=info"

REM Arranca Celery Beat
start cmd /k "celery -A whatsappbot_scheduler beat --loglevel=info"

echo Celery worker y beat iniciados en ventanas separadas.
pause
