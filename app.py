import streamlit as st
import subprocess
import threading
import sys

# تنظیمات ظاهر صفحه وب استریم‌لیت
st.set_page_config(page_title="Dr. Lead Bot Dashboard", page_icon="🤖")

st.title("🤖 پنل مدیریت ربات تلگرام دکترلید")
st.info("وضعیت سرور: ربات شما به صورت ۲۴ ساعته و ابری در حال اجراست! 🚀")

# تابع اجرای ربات در پس‌زمینه با پایتونِ اصلی محیط استریم‌لیت
def start_bot():
    subprocess.run([sys.executable, "bot.py"])

# اجرای ربات در یک ترد جداگانه
if "started" not in st.session_state:
    st.session_state.started = True
    threading.Thread(target=start_bot, daemon=True).start()
    st.success("موتور ربات در فضای ابری استریم‌لیت با موفقیت روشن شد!")

st.write("---")
st.write("شما می‌توانید این صفحه را ببندید؛ ربات در پس‌زمینه به کار خود ادامه می‌دهد.")
