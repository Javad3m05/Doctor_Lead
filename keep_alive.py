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
    
    try:
        print(f"در حال باز کردن {URL} ...")
        # استفاده از وب‌درایور منیجر برای نصب خودکار درایور در سرور ابری
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(URL)
        
        time.sleep(10)
        print("✅ بازدید موفقیت‌آمیز بود و تایمر خواب استریم‌لیت صفر شد.")
        driver.quit()
    except Exception as e:
        print(f"❌ خطا در بازدید: {e}")

if __name__ == "__main__":
    visit_site()
