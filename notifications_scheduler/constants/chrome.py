# constants/chrome.py

# Configuraciones comunes para ChromeDriver
CHROME_PROFILE_DIR = "chrome_selenium_profile"
CHROME_PROFILE_NAME = "Default"
CHROME_COMMON_OPTIONS = [
    "--start-maximized",
    "--disable-gpu",
    "--no-sandbox",
    "--disable-dev-shm-usage"
]