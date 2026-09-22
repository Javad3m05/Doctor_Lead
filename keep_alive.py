from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# لینک سایت استریم‌لیت خود را اینجا قرار دهید
URL = "https://doctorlead-2k7aauyvxs3hebnnwcxbox.streamlit.app/"

def visit_site():
    chrome_options = Options()
    chrome_options.add_argument("--headless") # اجرای مخفی مرورگر
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    try:
        print(f"در حال باز کردن {URL} ...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(URL)
        
        # ۱۰ ثانیه صبر برای لود شدن کامل کدهای جاوا اسکریپت استریم‌لیت
        time.sleep(10)
        
        print("✅ بازدید موفقیت‌آمیز بود و تایمر خواب استریم‌لیت صفر شد.")
        driver.quit()
    except Exception as e:
        print(f"❌ خطا در بازدید: {e}")

if __name__ == "__main__":
    visit_site()
