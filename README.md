# 📲 whatsappbot-scheduler

**whatsappbot-scheduler** is a Django-based automation tool for scheduling and sending WhatsApp messages to clients using Selenium and Celery.

---

## 🚀 Features

- 🗓 Schedule messages to be sent in customizable batches.
- 👥 Manage clients and link them to messages via Django admin.
- 🔄 Automatic retry logic for failed messages (network, timeout, rate-limit) with configurable max retries.
- 🧠 Avoids blocking by controlling sending frequency and batch sizes.
- 💬 Supports text and emojis using `pyperclip`.
- 📊 Tracks sending status and timestamps per message.
- 🔒 Runs using new Chrome profiles to isolate sessions.
- 📥 Bulk import/export for appointments and messages (django-import-export).
- 🛠️ Service layer for message sending and error handling.
- 🏗️ SOLID-compliant sender interface for extensibility.

---

## 📦 Tech Stack

- Python 3.11
- Django 5.x
- Celery + Redis
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

## 💡 Usage & Testing

### Django Admin
- Create clients, appointments, and scheduled messages.
- Bulk import/export supported for appointments and messages.

### Message Sending: Manual, Enqueued, Automated & Retry

- **Manual test:**
  Send all pending scheduled messages immediately:
  ```bash
  python manage.py send_scheduled_messages
  ```
- **Enqueued test (asynchronous):**
  Enqueue messages for Celery workers:
  ```bash
  python manage.py enqueue_scheduled_messages
  ```
- **Automated periodic execution:**
  Celery Beat triggers enqueuing and sending tasks automatically based on schedule.
  Use the `.bat` file for easy startup on Windows:
  ```bat
  start_celery_windows.bat
  ```
- **Retry failed messages:**
  The system automatically retries failed messages (network, timeout, rate-limit) up to the configured max retries. You can also trigger retries manually:
  ```bash
  python manage.py retry_failed_messages
  ```

- Combine manual and automated commands for different testing levels.
- Check logs and admin for message status and errors.

---

## 📄 License
MIT

## 🤝 Contributing
Pull requests are welcome. Please open an issue first to discuss what you would like to change.
