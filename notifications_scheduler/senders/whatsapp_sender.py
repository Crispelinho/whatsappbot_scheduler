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
from selenium.common.exceptions import TimeoutException
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

    def _wait_for_element(self, by, selector, timeout=20) -> tuple[bool, any]:
        """
        Espera a que un elemento esté presente y retornarlo.
        Retorna (success, element_or_error_message)
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return True, element
        except TimeoutException:
            return False, f"Timeout waiting for element: {selector}"

    def _attach_and_send_file(self, file_path: str) -> tuple[bool, MessageSendResult]:
        """Adjunta archivo (imagen o video) y lo envía."""
        success, attach_btn = self._wait_for_element(By.XPATH, "//button[@title='Adjuntar']", 20)
        if not success:
            return False, MessageSendResult(success=False, error_code=ErrorCode.TIMEOUT, message=attach_btn)

        attach_btn.click()
        time.sleep(1)

        try:
            input_file = self.driver.find_element(
                By.XPATH, '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]'
            )
            input_file.send_keys(file_path)
            time.sleep(3)
        except Exception as e:
            return False, MessageSendResult(success=False, error_code=ErrorCode.EXCEPTION, message=str(e))

        success, send_btn = self._wait_for_element(By.XPATH, '//div[@aria-label="Enviar"]', 10)
        if not success:
            return False, MessageSendResult(success=False, error_code=ErrorCode.TIMEOUT, message=send_btn)

        send_btn.click()
        time.sleep(5)
        return True, None


    def _is_invalid_number(self) -> bool:
        """Detecta si el número no está en WhatsApp."""
        try:
            self.driver.find_element(By.XPATH, '//div[contains(text(),"no está en WhatsApp")]')
            return True
        except:
            return False  
    
    def _write_message(self, message: str) -> bool:
        """Escribe y envía un mensaje en el chat. Retorna True si se pudo escribir."""
        boxes = self.driver.find_elements(By.XPATH, '//div[@contenteditable="true"]')
        if not boxes:
            return False

        box = boxes[-1]
        box.click()
        time.sleep(0.3)
        box.send_keys(Keys.CONTROL, 'v')
        box.send_keys(Keys.ENTER)
        return True
    
    def send_message(
        self,
        phone_number: str,
        message: str = None,
        image_path: str = None,
        video_path: str = None
    ) -> MessageSendResult:
        """
        Envía mensaje por WhatsApp Web.
        Retorna un MessageSendResult con estado, error y mensaje.
        """
        # Asegurarse de que el driver esté inicializado
        if not self.driver:
            self.driver = self._get_or_create_driver()
        
        # Validar número de teléfono
        if not phone_number:
            return MessageSendResult(
                success=False,
                error_code=ErrorCode.INVALID_NUMBER,
                message="Phone number is required"
            )
        
        # Verificar que el número comience con '+'
        # if not phone_number.startswith("+"):
        #     return MessageSendResult(
        #         success=False,
        #         error_code=ErrorCode.INVALID_NUMBER,
        #         message="Phone number must start with '+'"
        #     )
        
        # Verificar que WhatsApp Web esté cargado
        if not self.driver.current_url.startswith("https://web.whatsapp.com"):
            return MessageSendResult(
                success=False,
                error_code=ErrorCode.WHATSAPP_DOWN,
                message="WhatsApp Web is not reachable"
            )
        
        try:
            self.driver.get(f"https://web.whatsapp.com/send?phone={phone_number}")
            WebDriverWait(self.driver, 120).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"]'))
            )
            time.sleep(1.5)

            # Verificar número inválido
            if self._is_invalid_number():
                return MessageSendResult(
                    success=False,
                    error_code=ErrorCode.INVALID_NUMBER,
                    message="Number not on WhatsApp"
                )

            # Enviar mensaje si hay texto
            if message:
                pyperclip.copy(message)
                if not self._write_message(message):
                    return MessageSendResult(
                        success=False,
                        error_code=ErrorCode.NO_INPUT_BOX,
                        message="Input box not found"
                    )
            message_sucess_send_result = "Message sent successfully"
            # Adjuntar archivos si existen
            for file_path in [image_path, video_path]:
                if file_path:
                    success, message_send_result = self._attach_and_send_file(file_path)
                    if not success:
                        return message_send_result
                    message_sucess_send_result = message_sucess_send_result + f" and {file_path} sent successfully"

            return MessageSendResult(success=True, message=message_sucess_send_result)

        except TimeoutException:
            return MessageSendResult(
                success=False,
                error_code=ErrorCode.TIMEOUT,
                message="Timeout waiting for WhatsApp Web to load chat"
            )

        except Exception as e:
            return MessageSendResult(
                success=False,
                error_code=ErrorCode.EXCEPTION,
                message=str(e)
            )
