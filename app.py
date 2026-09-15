import streamlit as st
import subprocess
import sys

st.set_page_config(page_title="Dr. Lead Bot Dashboard", page_icon="🤖")
st.title("🤖 پنل مدیریت ربات تلگرام دکترلید")
st.info("وضعیت سرور: ربات به صورت ابری در حال اجراست! 🚀")

# این دستور جادویی باعث می‌شود تابع زیر فقط و فقط "یک بار" در کل سرور اجرا شود
# حتی اگر هزار بار صفحه سایت را رفرش کنید، ربات دومی ساخته نمی‌شود!
@st.cache_resource
def start_bot_process():
    # استفاده از Popen برای اجرای بی‌سروصدا در پس‌زمینه
    process = subprocess.Popen([sys.executable, "bot.py"])
    return process

# روشن کردن موتور ربات
start_bot_process()

st.success("موتور ربات با موفقیت روشن شد (محافظت شده در برابر اجرای چندگانه) ✅")
st.write("---")
st.write("شما می‌توانید این صفحه را ببندید؛ ربات در پس‌زمینه به کار خود ادامه می‌دهد.")
