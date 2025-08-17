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
from notifications_scheduler.models import ScheduledMessage, ClientScheduledMessage, MessageResponse, ErrorType


class WhatsAppSenderInterface:
    def send_message(self, phone_number: str, message: str, image_path: str, video_path: str) -> tuple[bool, str]:
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
            raise Exception("Could not log in to WhatsApp Web: " + str(e))
        SeleniumWhatsAppSender._driver = driver
        return driver

    def send_message(self, phone_number: str, message: str, image_path: str, video_path: str) -> tuple[bool, str]:
        driver = self.driver
        pyperclip.copy(message)
        try:
            driver.get(f"https://web.whatsapp.com/send?phone={phone_number}")
            WebDriverWait(driver, 120).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"]'))
            )
            time.sleep(2)

            # Detect invalid number
            try:
                driver.find_element(By.XPATH, '//div[contains(text(),"no está en WhatsApp")]')
                return False, "INVALID_NUMBER"
            except:
                pass

            boxes = driver.find_elements(By.XPATH, '//div[@contenteditable="true"]')
            box = boxes[-1]
            box.click()
            time.sleep(0.5)
            box.send_keys(Keys.CONTROL, 'v')
            box.send_keys(Keys.ENTER)
            time.sleep(2)

            if image_path:
                attach_btn = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//button[@title='Adjuntar']"))
                )
                attach_btn.click()
                time.sleep(1)
                input_file = driver.find_element(By.XPATH, '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]')
                input_file.send_keys(image_path)
                time.sleep(3)
                send_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Enviar"]'))
                )
                send_btn.click()
                time.sleep(5)

            if video_path:
                attach_btn = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//button[@title='Adjuntar']"))
                )
                attach_btn.click()
                time.sleep(1)
                input_file = driver.find_element(By.XPATH, '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]')
                input_file.send_keys(video_path)
                time.sleep(3)
                send_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Enviar"]'))
                )
                send_btn.click()
                time.sleep(5)

            return True, "SENT"
        except Exception as e:
            return False, str(e)


class Command(BaseCommand):
    help = "Send scheduled WhatsApp messages to clients"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.whatsapp_sender = SeleniumWhatsAppSender()

    def handle(self, *args, **kwargs):
        now = timezone.now()
        scheduled_messages = ScheduledMessage.objects.filter(status="active", start_datetime__lte=now)

        for scheduled in scheduled_messages:
            batch_size = scheduled.recipient_count if scheduled.recipient_count > 0 else 50
            has_more = True
            offset = 0

            while has_more:
                pending_messages = ClientScheduledMessage.objects.filter(
                    scheduled_message=scheduled,
                    response__status="pending"
                )[offset:offset + batch_size]

                if not pending_messages.exists():
                    self.stdout.write(f"No pending messages for scheduled message '{scheduled.subject}'")
                    break

                self.stdout.write(f"Processing batch of {len(pending_messages)} messages for '{scheduled.subject}'")

                for client_msg in pending_messages:
                    phone = client_msg.client.phone_number
                    text = scheduled.message_text
                    image = scheduled.image.path if scheduled.image else None
                    video = scheduled.video.path if scheduled.video else None

                    try:
                        success, response_code = self.whatsapp_sender.send_message(phone, text, image, video)

                        msg_response: MessageResponse = client_msg.response
                        if success:
                            msg_response.status = "sent"
                            msg_response.error_type = None
                            client_msg.sent_at = timezone.now()
                            self.stdout.write(f"Sent message to {phone}")
                        else:
                            msg_response.status = "failed"
                            error = ErrorType.objects.filter(code=response_code).first()
                            if not error and response_code not in ["SENT", "PENDING"]:
                                # Create unknown error dynamically if not registered
                                error = ErrorType.objects.get_or_create(
                                    code="UNKNOWN", defaults={"name": "Unknown Error", "description": response_code}
                                )[0]
                            msg_response.error_type = error
                            self.stderr.write(f"Failed to send message to {phone}: {response_code}")

                        msg_response.save()
                        client_msg.save()

                    except Exception as e:
                        msg_response: MessageResponse = client_msg.response
                        msg_response.status = "failed"
                        error = ErrorType.objects.get_or_create(
                            code="EXCEPTION", defaults={"name": "Unhandled Exception", "description": str(e)}
                        )[0]
                        msg_response.error_type = error
                        msg_response.save()
                        client_msg.save()
                        self.stderr.write(f"Exception sending message to {phone}: {e}")

                offset += batch_size
                time.sleep(60)  # avoid ban / overload
