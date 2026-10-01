from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

URL = "https://doctorlead-2k7aauyvxs3hebnnwcxbox.streamlit.app/"

def visit_site():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # اضافه کردن هویت مرورگر انسانی برای جلوگیری از تشخیص ربات
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    print(f"در حال باز کردن {URL} ...")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    driver.get(URL)
    
    # ۱۵ ثانیه مکث برای لود شدن کامل کدهای جاوا اسکریپت
    time.sleep(15)
    
    print("✅ صفحه با موفقیت لود شد و تایمر خواب صفر شد.")
    driver.quit()

if __name__ == "__main__":
    visit_site()
