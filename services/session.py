from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import pickle
import os
import time

LOGIN = "issfutoi@moex.com"
PASSWORD = "FORTS1!"
COOKIES_FILE = 'moex_cookies.pkl'

# Глобальная сессия
session = None

def init_session():
    """Инициализирует глобальную сессию (вызвать один раз при старте)"""
    global session
    
    if os.path.exists(COOKIES_FILE):
        try:
            session = requests.Session()
            with open(COOKIES_FILE, 'rb') as f:
                cookies = pickle.load(f)
                for cookie in cookies:
                    session.cookies.set(cookie["name"], cookie["value"])
            # Проверка
            test = session.get("https://iss.moex.com/iss/analyticalproducts/futoi/securities.csv")
            if test.status_code == 200:
                return
        except:
            pass
    
    # Создаём новую сессию через Selenium
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=options)
    driver.get("https://passport.moex.com/login")
    
    wait = WebDriverWait(driver, 20)
    login_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'], input[type='email']")))
    password_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']")))
    
    login_input.send_keys(LOGIN)
    password_input.send_keys(PASSWORD)
    password_input.send_keys(Keys.ENTER)
    time.sleep(5)
    
    cookies = driver.get_cookies()
    driver.quit()
    
    session = requests.Session()
    for cookie in cookies:
        session.cookies.set(cookie["name"], cookie["value"])
    
    with open(COOKIES_FILE, 'wb') as f:
        pickle.dump(cookies, f)

def get_session():
    """Возвращает глобальную сессию"""
    global session
    if session is None:
        init_session()
    return session