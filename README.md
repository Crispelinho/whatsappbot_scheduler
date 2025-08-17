# 📲 whatsappbot-scheduler

**whatsappbot-scheduler** is a Django-based automation tool that allows you to schedule and send WhatsApp messages using Selenium and `pyperclip`.  
It is designed to automate communication with multiple clients while avoiding WhatsApp detection or rate limiting.

---

## 🚀 Features

- 🗓 Schedule messages to be sent in customizable batches.
- 👥 Manage clients and link them to messages easily via Django admin.
- 🧠 Avoids blocking by controlling sending frequency and batch sizes.
- 💬 Supports text and emojis using `pyperclip`.
- 📊 Tracks sending status and timestamps per message.
- 🔒 Runs using new Chrome profiles to isolate sessions.

---

## 📦 Tech Stack

- Python 3.11
- Django 5.x
- Selenium
- pyperclip
- ChromeDriver + Google Chrome

---

## 🛠️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-user/whatsappbot-scheduler.git
cd whatsappbot-scheduler
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run migrations and create a superuser

```bash
python manage.py migrate
python manage.py createsuperuser
```


### 5. Instala y ejecuta Redis (requerido para Celery)

Descarga e instala Redis para Windows desde https://github.com/tporadowski/redis/releases
Inicia el servicio de Redis antes de continuar.

### 6. Ejecuta el servidor de desarrollo

```bash
python manage.py runserver
```

### 7. Ejecuta Celery y Celery Beat (Windows)

Usa el archivo por lotes incluido para lanzar ambos procesos automáticamente:

```bat
.\start_celery_windows.bat
```

Esto abrirá dos ventanas: una para el worker y otra para el scheduler (beat).

Si prefieres hacerlo manualmente:

```powershell
celery -A whatsappbot_scheduler worker --pool=solo --loglevel=info
celery -A whatsappbot_scheduler beat --loglevel=info
```

---

## 💡 Example Usage


1. Ingresa al Django Admin.
2. Crea tus Clientes y Programaciones de Mensajes.
3. El envío se realizará automáticamente cada minuto gracias a Celery Beat.
4. Si quieres forzar el envío manualmente, ejecuta:

```bash
python manage.py send_scheduled_messages
python manage.py enqueue_scheduled_messages
```

---

## 📄 License
MIT

## 🤝 Contributing
Pull requests are welcome. Please open an issue first to discuss what you would like to change.
