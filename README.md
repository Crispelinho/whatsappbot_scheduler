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

### 5. Run the development server

```bash
python manage.py runserver
```

---

## 💡 Example Usage

1. Log in to the Django Admin.
2. Create your Clients and Message Schedules.
3. Run the bot script to start sending:

```bash
python send_whatsapp_messages.py
```

---

## 📄 License
MIT

## 🤝 Contributing
Pull requests are welcome. Please open an issue first to discuss what you would like to change.
