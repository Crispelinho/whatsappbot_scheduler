from notifications_scheduler.exceptions.whatsapp import WhatsAppSessionException
from datetime import datetime
import os
import time
import traceback
import pyperclip

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.remote.webelement import WebElement


from notifications_scheduler.constants import chrome, times, xpaths, whatsapp
from notifications_scheduler.models import ResponseCode
from notifications_scheduler.senders.base import MessageSendResult, SocialNetworkSenderInterface


class WhatsAppSeleniumSender(SocialNetworkSenderInterface):
    """Sender que utiliza Selenium para enviar mensajes por WhatsApp Web."""
    
    _driver = None # Driver compartido entre instancias si use_shared_driver es True

    def __init__(self, use_shared_driver: bool = True):       
        """
        Inicializa el sender.
        :param use_shared_driver: Si True, reutiliza un driver global compartido.
                                  Si False, crea un driver propio (útil en tests o workers múltiples).
        """
        self.use_shared_driver = use_shared_driver
        self.driver = self._get_or_create_driver()

    def _get_or_create_driver(self)-> webdriver.Chrome:
        """Obtiene o inicializa el driver de Selenium con perfil persistente."""
        if self.use_shared_driver:
            if WhatsAppSeleniumSender._driver:
                return WhatsAppSeleniumSender._driver

        driver = self._create_driver_with_profile()
        self._open_whatsapp_and_wait(driver)

        if self.use_shared_driver:
            WhatsAppSeleniumSender._driver = driver
        return driver

    def _check_session(self):
        """Lanza WhatsAppSessionException si la sesión de Selenium no es válida."""
        try:
            # Esto lanza excepción si la sesión no es válida
            _ = self.driver.current_url
        except Exception as e:
            if 'invalid session id' in str(e).lower():
                raise WhatsAppSessionException("Sesión de Selenium/WhatsApp Web inválida o cerrada.") from e
            raise

    def _create_driver_with_profile(self) -> webdriver.Chrome:
        """Crea un ChromeDriver con perfil persistente."""
        chrome_user_data = os.path.join(os.getcwd(), chrome.CHROME_PROFILE_DIR)
        os.makedirs(chrome_user_data, exist_ok=True)

        return webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=self._build_chrome_options(chrome_user_data)
        )
    
    def _build_chrome_options(self, chrome_user_data: str, profile: str = chrome.CHROME_PROFILE_NAME) -> Options:
        """Construye las opciones de ChromeDriver con perfil persistente."""
        options = Options()
        options.add_argument(f"--user-data-dir={chrome_user_data}")
        options.add_argument(f"--profile-directory={profile}")
        
        for arg in chrome.CHROME_COMMON_OPTIONS:
            options.add_argument(arg)

        return options
    
    def _open_whatsapp_and_wait(self, driver: webdriver.Chrome, timeout: int = 300):
        """Abre WhatsApp Web y espera a que cargue la caja de texto."""
        driver.get(whatsapp.URL_WHATSAPP_WEB)
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='textbox']"))
            )
        except Exception as e:
            driver.quit()
            raise RuntimeError(f"Could not log in to WhatsApp Web: {e}")

    def _debug_log(self, context: str, error: Exception | None = None, selector: str = None) -> str:
        """
        Guarda HTML y screenshot en carpeta debug/ y retorna un log con rutas.
        context: Descripción breve del punto donde falló (ej: 'chat_load', 'file_upload')
        """
        os.makedirs("debug", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = f"debug/{context}_{timestamp}.html"
        img_path = f"debug/{context}_{timestamp}.png"

        try:
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            self.driver.save_screenshot(img_path)
        except Exception as e:
            return f"[DEBUG_LOG_ERROR] No se pudo guardar debug para {context}: {e}"


        msg = f"[DEBUG] Context: {context}"
        if selector:
            msg += f" | Selector: {selector}"
        msg += f" | HTML: {html_path} | Screenshot: {img_path}"
        if error:
            msg += f" | Exception: {repr(error)}\n{traceback.format_exc()}"
        return msg

    def _wait_for_element(self, by, selector, timeout=20) -> tuple[bool, WebElement, str| None]:
        """
        Espera a que un elemento esté presente y retornarlo.
        Retorna (success, element_or_error_message)
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return True, element, None
        except (TimeoutException, NoSuchElementException) as e:
            return False, None, self._debug_log("wait_for_element", e, selector)
        
    def _find_button_and_click(self, by, selector, timeout=20) -> tuple[bool, MessageSendResult]:
        """
        Encuentra un botón y hace click.
        Retorna (success, error_message_if_any)
        """
        success, element_btn, error_msg = self._wait_for_element(by, selector, timeout)
        if not success:
            return False, MessageSendResult(
                success=False,
                error_code=ResponseCode.TIMEOUT.value,
                message=error_msg
            )
        element_btn.click()
        return True, None
    
    def _upload_file(self, file_path: str) -> tuple[bool, MessageSendResult]:
        """Carga un archivo en el input de archivos, forzando visibilidad para evitar el diálogo del sistema."""
        try:
            input_file = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, xpaths.FILE_INPUT))
            )
            # Forzar visibilidad del input file con JS
            self.driver.execute_script("arguments[0].style.display = 'block'; arguments[0].style.visibility = 'visible';", input_file)
            input_file.send_keys(file_path)
            return True, None
        except Exception as e:
            return False, MessageSendResult(
                success=False,
                error_code=ResponseCode.UPLOAD_MEDIA_FAILED.value,
                message=self._debug_log("file_upload", e)
            )

    def _attach_and_send_file(self, file_path: str) -> tuple[bool, MessageSendResult]:
        """Adjunta un archivo (imagen o video) y lo envía."""
        
        # Paso 1: Buscar botón de adjuntar y hacer click
        success_btn_attach_click, msg_send_result = self._find_button_and_click(By.XPATH, xpaths.ATTACH_BUTTON, times.DEFAULT_TIMEOUT)
        if not success_btn_attach_click:
            return False, msg_send_result

        time.sleep(1)

        # Paso 1.5: Hacer click en botón de 'Fotos y videos'
        success_btn_fotos_click, msg_send_result = self._find_button_and_click(By.XPATH, xpaths.ATTACH_MEDIA, times.DEFAULT_TIMEOUT)
        if not success_btn_fotos_click:
            return False, msg_send_result

        time.sleep(1)

        # Paso 2: Cargar archivo en input de archivos
        success_file_upload, msg_send_result = self._upload_file(file_path)
        if not success_file_upload:
            return False, msg_send_result

        time.sleep(3)

        # Paso 3: Esperar botón de enviar y hacer click
        success_btn_send_click, msg_send_result = self._find_button_and_click(By.XPATH, xpaths.SEND_BUTTON, times.DEFAULT_TIMEOUT)
        if not success_btn_send_click:
            return False, msg_send_result
        
        time.sleep(3)

        return True, None

    def _check_invalid_number(self, timeout: int = 5) -> MessageSendResult | None:
        """Detecta si el número no está en WhatsApp o es inválido."""
        selectors = {
            ResponseCode.NOT_FOUND_IN_WHATSAPP: '//div[contains(text(),"no está en WhatsApp")]',
            ResponseCode.INVALID_NUMBER: '//div[contains(text(),"no es válido")]',
        }
        for code, xpath in selectors.items():
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                return MessageSendResult(
                        success=False,
                        error_code=code.value,
                        message=self._debug_log("invalid_number_check", Exception(element.text if element else None))
                    )
            except TimeoutException:
                continue
        return None

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
        # Verificar sesión válida antes de operar
        self._check_session()
        # Validar número de teléfono
        if not phone_number:
            return MessageSendResult(
                success=False,
                error_code=ResponseCode.INVALID_NUMBER.value,
                message=self._debug_log("empty_phone_number", Exception("Phone number is empty"))
            )
        
        # Verificar que el número comience con '+'
        # if not phone_number.startswith("+"):
        #     return MessageSendResult(
        #         success=False,
        #         error_code=ResponseCode.INVALID_NUMBER,
        #         message="Phone number must start with '+'"
        #     )
        
        # Verificar que WhatsApp Web esté cargado
        if not self.driver.current_url.startswith("https://web.whatsapp.com"):
            return MessageSendResult(
                success=False,
                error_code=ResponseCode.WHATSAPP_DOWN.value,
                message=self._debug_log("whatsapp_web_not_loaded", Exception("WhatsApp Web is not loaded"))
            )
        
        try:
            self.driver.get(f"https://web.whatsapp.com/send?phone={phone_number}")
            WebDriverWait(self.driver, 120).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"]'))
            )
            time.sleep(1.5)

            # Verificar número inválido o no registrado en WhatsApp
            message_send_result = self._check_invalid_number()
            if message_send_result != None:
                return message_send_result

            # Enviar mensaje si hay texto
            if message:
                pyperclip.copy(message)
                if not self._write_message(message):
                    return MessageSendResult(
                        success=False,
                        error_code=ResponseCode.NO_INPUT_BOX.value,
                        message=self._debug_log("no_input_box", Exception("Could not find input box"))
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
                error_code=ResponseCode.TIMEOUT.value,
                message=self._debug_log("send_message_chat_load", TimeoutException("Chat did not load in time"))
            )

        except Exception as e:
            return MessageSendResult(
                success=False,
                error_code=ResponseCode.EXCEPTION.value,
                message=self._debug_log("send_message_exception", e)
            )
