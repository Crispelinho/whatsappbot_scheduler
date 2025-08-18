

import os
from ssl import Options
import time

import pyperclip
from notifications_scheduler.senders.base import SocialNetworkSenderInterface
from sales.models import Service

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class WhatsAppSeleniumSender(SocialNetworkSenderInterface):
    _driver = None

    def __init__(self):
        self.driver = self._get_driver()

    def _get_driver(self):
        if WhatsAppSeleniumSender._driver is not None:
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
            raise Exception("Could not log in to SocialNetworkSenderInterface Web: " + str(e))
        WhatsAppSeleniumSender._driver = driver
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
                driver.find_element(By.XPATH, '//div[contains(text(),"no está en SocialNetworkSenderInterface")]')
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