import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.common.by import By


def prox1(url):
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    # chrome_options.add_argument('--proxy-server=https://tka4enko_D:SdgvE7SR5J@185.128.215.5:49155')  # Set your proxy

    # Set up the Chrome driver
    # service = Service('/path/to/chromedriver')  # Specify the correct path to your chromedriver
    driver = webdriver.Chrome(options=chrome_options)

    # Navigate to the URL
    driver.get(url)
    print('Successfully connected with proxy')

    return driver


def get_meet(name):
    url = 'https://jazz.sber.ru/create'
    driver = prox1(url)

    while True:
        try:
            input_field = driver.find_elements(By.NAME, "title")[-1]
            input_field.clear()
            input_field.send_keys(name)
            break
        except:
            print('No button')

    while True:
        try:
            input_field = driver.find_elements(By.NAME, "name")[-1]
            input_field.clear()
            input_field.send_keys("Видеовстреча")
            break
        except:
            print('No button')

    button = driver.find_element(By.CSS_SELECTOR, "button[data-testid='createConf']")
    button.click()
    time.sleep(1)

    current_url = driver.current_url
    driver.quit()

    return current_url
