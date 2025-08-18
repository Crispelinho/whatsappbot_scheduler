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

from notifications_scheduler.models import ErrorCode
from notifications_scheduler.senders.base import MessageSendResult, SocialNetworkSenderInterface


class WhatsAppSeleniumSender(SocialNetworkSenderInterface):
    """Sender que utiliza Selenium para enviar mensajes por WhatsApp Web."""
    
    _driver = None

    def __init__(self):
        self.driver = self._get_or_create_driver()

    def _get_or_create_driver(self):
        """Obtiene o inicializa el driver de Selenium con perfil persistente."""
        if WhatsAppSeleniumSender._driver:
            return WhatsAppSeleniumSender._driver

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
            raise RuntimeError(f"Could not log in to WhatsApp Web: {e}")

        WhatsAppSeleniumSender._driver = driver
        return driver

    def _attach_and_send_file(self, file_path: str):
        """Adjunta archivo (imagen o video) y lo envía."""
        attach_btn = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//button[@title='Adjuntar']"))
        )
        attach_btn.click()
        time.sleep(1)

        input_file = self.driver.find_element(
            By.XPATH, '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]'
        )
        input_file.send_keys(file_path)
        time.sleep(3)

        send_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Enviar"]'))
        )
        send_btn.click()
        time.sleep(5)

    def send_message(self, phone_number: str, message: str, image_path: str = None, video_path: str = None) -> dict:
        """
        Envía mensaje por WhatsApp Web.
        Retorna un dict con estado, error y código de respuesta.
        """
        driver = self.driver
        pyperclip.copy(message)

        try:
            driver.get(f"https://web.whatsapp.com/send?phone={phone_number}")
            WebDriverWait(driver, 120).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"]'))
            )
            time.sleep(2)

            # Detectar número inválido
            try:
                driver.find_element(By.XPATH, '//div[contains(text(),"no está en WhatsApp")]')
                return MessageSendResult(success=False, error_code=ErrorCode.INVALID_NUMBER, message="Number not on WhatsApp")
            except:
                pass

            # Escribir mensaje
            boxes = driver.find_elements(By.XPATH, '//div[@contenteditable="true"]')
            if not boxes:
                return MessageSendResult(success=False, error_code=ErrorCode.NO_INPUT_BOX, message="Input box not found")

            box = boxes[-1]
            box.click()
            time.sleep(0.5)
            box.send_keys(Keys.CONTROL, 'v')
            box.send_keys(Keys.ENTER)
            time.sleep(2)

            # Adjuntar archivos si existen
            if image_path:
                self._attach_and_send_file(image_path)
            if video_path:
                self._attach_and_send_file(video_path)

            return MessageSendResult(success=True, message="Message sent successfully")

        except Exception as e:
            return MessageSendResult(success=False, error_code=ErrorCode.EXCEPTION, message=str(e))
