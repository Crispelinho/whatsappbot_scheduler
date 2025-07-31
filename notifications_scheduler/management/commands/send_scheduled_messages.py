# notifications_scheduler/management/commands/send_scheduled_messages.py


import os
import time
import pyperclip
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from django.core.management.base import BaseCommand
from django.utils import timezone
from notifications_scheduler.models import ScheduledMessage, ClientMessage


class WhatsAppSenderInterface:
    def send_message(self, phone_number: str, message: str, image_path: str) -> tuple[bool, str]:
        raise NotImplementedError


class SeleniumWhatsAppSender(WhatsAppSenderInterface):
    _driver = None

    def __init__(self):
        self.driver = self._get_driver()

    def _get_driver(self):
        if SeleniumWhatsAppSender._driver is not None:
            return SeleniumWhatsAppSender._driver
        chrome_user_data = os.path.join(os.getcwd(), "chrome_selenium_profile")
        os.makedirs(chrome_user_data, exist_ok=True)
        options = Options()
        options.add_argument(f"--user-data-dir={chrome_user_data}")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager(driver_version="138.0.7204.158").install()),
            options=options
        )
        driver.get("https://web.whatsapp.com")
        try:
            WebDriverWait(driver, 300).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='textbox']"))
            )
        except Exception as e:
            driver.quit()
            raise Exception("No se pudo iniciar sesión en WhatsApp Web: " + str(e))
        SeleniumWhatsAppSender._driver = driver
        return driver

    def send_message(self, phone_number: str, message: str, image_path: str) -> tuple[bool, str]:
        driver = self.driver
        pyperclip.copy(message)
        try:
            driver.get(f"https://web.whatsapp.com/send?phone={phone_number}")
            WebDriverWait(driver, 120).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"]'))
            )
            time.sleep(2)
            # Detectar si el número es inválido
            try:
                driver.find_element(By.XPATH, '//div[contains(text(),"no está en WhatsApp")]')
                return False, "El número no está en WhatsApp"
            except:
                pass
            cajas = driver.find_elements(By.XPATH, '//div[@contenteditable="true"]')
            caja = cajas[-1]
            caja.click()
            time.sleep(0.5)
            caja.send_keys(Keys.CONTROL, 'v')
            caja.send_keys(Keys.ENTER)
            time.sleep(2)
            if image_path:
            # Adjuntar imagen
                adjuntar_btn = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//button[@title='Adjuntar']"))
                )
                adjuntar_btn.click()
                time.sleep(1)
                input_file = driver.find_element(By.XPATH, '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]')
                input_file.send_keys(image_path)
                time.sleep(3)
                enviar_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Enviar"]'))
                )
                enviar_btn.click()
                time.sleep(5)
            return True, "Mensaje y/o imagen enviados correctamente"
        except Exception as e:
            return False, str(e)


class Command(BaseCommand):
    help = "Send scheduled WhatsApp messages to clients"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inyección de dependencia: puedes cambiar SeleniumWhatsAppSender por un mock para pruebas
        self.whatsapp_sender = SeleniumWhatsAppSender()

    def handle(self, *args, **kwargs):
        now = timezone.now()
        scheduled_messages = ScheduledMessage.objects.filter(status='active', start_datetime__lte=now)
        
        for scheduled in scheduled_messages:
            batch_size = scheduled.recipient_count if scheduled.recipient_count > 0 else 50  # Valor por defecto si es 0
            has_more = True
            offset = 0

            while has_more:
                pending_messages = ClientMessage.objects.filter(
                    scheduled_message=scheduled,
                    send_status='pending'
                )[offset:offset + batch_size]

                if not pending_messages.exists():
                    self.stdout.write(f"No pending messages for scheduled message '{scheduled.subject}'")
                    break

                self.stdout.write(f"Processing batch of {len(pending_messages)} messages for '{scheduled.subject}'")

                for client_msg in pending_messages:
                    phone = client_msg.client.phone_number
                    text = scheduled.message_text
                    image = scheduled.image.path if scheduled.image else None
                    try:
                        success, response = self.whatsapp_sender.send_message(phone, text, image)
                        if success:
                            client_msg.send_status = 'sent'
                            client_msg.send_datetime = timezone.now()
                            client_msg.response = response
                            client_msg.save()
                            self.stdout.write(f"Sent message to {phone}")
                        else:
                            client_msg.send_status = 'failed'
                            client_msg.response = response
                            client_msg.save()
                            self.stderr.write(f"Failed to send message to {phone}: {response}")
                    except Exception as e:
                        client_msg.send_status = 'failed'
                        client_msg.response = str(e)
                        client_msg.save()
                        self.stderr.write(f"Exception sending message to {phone}: {e}")

                offset += batch_size
                # Espera entre lotes para evitar bloqueos o saturación
                time.sleep(60)