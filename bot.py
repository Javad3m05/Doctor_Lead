import os
import asyncio
import psycopg2
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ایمپورت کتابخانه جدید گوگل
from google import genai
from google.genai import types

# خواندن اطلاعات محرمانه از گاوصندوق سرور
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")
DB_URL = os.environ.get("DATABASE_URL")

# روشن کردن موتور هوش مصنوعی با ساختار جدید
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)

# بارگذاری کل دیتای کانال‌ها در حافظه ربات
try:
    with open("knowledge.txt", "r", encoding="utf-8") as file:
        knowledge_base = file.read()
except FileNotFoundError:
    knowledge_base = "اطلاعات پایگاه دانش هنوز اضافه نشده است."

#اتصال به دیتابیس ابری
conn = psycopg2.connect(DB_URL)
conn.autocommit = True
cursor = conn.cursor()

# ساخت جداول در سرور آنلاین (اگر وجود نداشته باشند)
cursor.execute("""
CREATE TABLE IF NOT EXISTS branches (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    branch_id INTEGER REFERENCES branches(id),
    title TEXT,
    description TEXT,
    price TEXT,
    link TEXT
)
""")

# وارد کردن اتوماتیک شاخه‌های شما (فقط برای بار اول)
cursor.execute("SELECT COUNT(*) FROM branches")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO branches (id, name) VALUES (1, 'دنتالید'), (2, 'فارمالید'), (3, 'مدیکالید')")


# --- توابع جدید دیتابیس (کاملاً ایمن، با ذخیره قطعی و بدون قطعی) ---
def get_branches():
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM branches ORDER BY id")
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def get_branch(branch_id):
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM branches WHERE id = %s", (int(branch_id),))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if row:
        b_id = row[0]
        name = row[1]
        
        # تعیین آیدی کانال برای قفل جوین اجباری هر شاخه
        # (شما می‌توانید این آیدی‌ها را به کانال‌های واقعی خودتان تغییر دهید)
        if b_id == 1:
            channel_username = "@Denta_Lead"
        elif b_id == 2:
            channel_username = "@pharma_lead"  # اگر فارمالید کانال جدا دارد، اینجا تغییر دهید
        elif b_id == 3:
            channel_username = "@medica_lead"  # اگر مدیکالید کانال جدا دارد، اینجا تغییر دهید
        else:
            channel_username = None
            
        # حالا پایتون دقیقاً ۳ آیتم را برمی‌گرداند تا خطای branch[2] رفع شود
        return (b_id, name, channel_username)
        
    return None
        
def get_courses_by_branch(branch_id):
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    # در اینجا branch_id به زور به عدد (int) تبدیل می‌شود تا دیتابیس خطا نگیرد
    cursor.execute("SELECT id, title FROM courses WHERE branch_id = %s", (int(branch_id),))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def get_course(course_id):
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    # در اینجا course_id به زور به عدد (int) تبدیل می‌شود
    cursor.execute("SELECT title, description, price, link, branch_id FROM courses WHERE id = %s", (int(course_id),))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result
    
def update_course(course_id, title, description, price, link):
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE courses 
        SET title=%s, description=%s, price=%s, link=%s 
        WHERE id=%s
    """, (title, description, price, link, course_id))
    conn.commit()  # ذخیره نهایی تغییرات
    cursor.close()
    conn.close()

def add_course(branch_id, title, description, price, link):
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    # اضافه کردن RETURNING id برای دریافت شناسه جدید
    cursor.execute("""
        INSERT INTO courses (branch_id, title, description, price, link)
        VALUES (%s, %s, %s, %s, %s) RETURNING id
    """, (branch_id, title, description, price, link))
    
    new_id = cursor.fetchone()[0] # گرفتن شناسه‌ای که دیتابیس ساخته
    conn.commit()  # ذخیره نهایی در سرور ابری
    
    cursor.close()
    conn.close()
    
    return new_id  # برگرداندن شناسه به ربات تلگرام# ---------------------------------------------------------
# کدهای تلگرام شما (async def) از اینجا به پایین دست‌نخورده باقی می‌مانند

# ---------- بررسی عضویت در کانال ----------
async def is_member(update: Update, context: ContextTypes.DEFAULT_TYPE, channel_username: str) -> bool:
    user_id = update.effective_user.id
    
  
        
    print(f"\n--- در حال بررسی عضویت ---")
    print(f"آیدی عددی کاربر: {user_id}")
    print(f"آیدی کانالی که ربات میگردد: {channel_username}")
    
    try:
        member = await context.bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        print(f"وضعیت یافت شده کاربر در کانال: {member.status}")
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"خطای تلگرام در پیدا کردن کانال: {e}")
        return False
# ---------- منوی اصلی ----------
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    branches = get_branches()
    keyboard = []
    for branch_id, name in branches:
        keyboard.append([InlineKeyboardButton(name, callback_data=f"branch_{branch_id}")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            "🎓 به ربات دکترلید خوش آمدید!\n"
            "لطفاً زیرشاخه مورد نظر خود را انتخاب کنید:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "🎓 به ربات دکترلید خوش آمدید!\n"
            "لطفاً زیرشاخه مورد نظر خود را انتخاب کنید:",
            reply_markup=reply_markup
        )

# ---------- نمایش دوره‌های یک شاخه ----------
async def show_courses(update: Update, context: ContextTypes.DEFAULT_TYPE, branch_id: int):
    # این خط اضافه می‌شود تا ربات شاخه فعلی را در حافظه کاربر ذخیره کند
    context.user_data['current_branch'] = branch_id
    branch = get_branch(branch_id)
    if not branch:
        await update.callback_query.answer("خطا: شاخه یافت نشد.")
        return

    courses = get_courses_by_branch(branch_id)
    keyboard = []
    for course_id, title in courses:
        keyboard.append([InlineKeyboardButton(title, callback_data=f"course_{course_id}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        f"📚 دوره‌های {branch[1]}:\n"
        "برای مشاهده اطلاعات هر دوره روی آن کلیک کنید:",
        reply_markup=reply_markup
    )

# نمایش اطلاعات یک دوره (از طریق ارسال پیام آماده کانال)
# نمایش اطلاعات یک دوره (از طریق ارسال پیام آماده کانال)
async def show_course_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    course_id = int(query.data.split("_")[1])
    course = get_course(course_id)
    
    if not course:
        await query.answer("خطا: دوره یافت نشد.", show_alert=True)
        return
        
    title, description, price, link, branch_id = course
    
    try:
        # لینک مستقیماً از دیتابیس خوانده و فاصله‌های اضافیش حذف می‌شود
        db_link = str(link).strip() 
        
        # استخراج اتوماتیک یوزرنیم کانال و شماره پیام از لینک
        parts = db_link.split("/")
        extracted_message_id = int(parts[-1])  # عدد آخر لینک
        extracted_channel = f"@{parts[-2]}"    # یوزرنیم کانال
        
        await context.bot.copy_message(
            chat_id=update.effective_chat.id,
            from_chat_id=extracted_channel,
            message_id=extracted_message_id
        )
        
# ارسال دکمه‌های بازگشت و پشتیبانی در یک پیام کوچک زیر پیام اصلی
# ارسال دکمه بازگشت و پشتیبانی در یک پیام کوچک زیر پیام اصلی
        keyboard = [
            [InlineKeyboardButton("💬 ارسال پیام به پشتیبانی", callback_data="ai_support_click")],
            [InlineKeyboardButton("بازگشت به دوره‌ها", callback_data=f"back_courses_{branch_id}")],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
# پیام راهنما به همراه دکمه‌های شیشه‌ای
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                "📞 برای مشاوره، ارسال رسید پرداخت و اعلام نظرات، با پشتیبانی در ارتباط باشید.\n\n"
                "👇 برای بازگشت به منو یا انتخاب دوره‌های دیگر، از دکمه‌های زیر استفاده کنید:"
            ),
            reply_markup=reply_markup
        )
        
    except Exception as e:
        print(f"Error in show_course_info: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ متأسفانه در نمایش اطلاعات این دوره مشکلی پیش آمد. (لینک پیام نامعتبر است)"
        )


# ---------- مدیریت انتخاب شاخه و بررسی عضویت ----------
async def branch_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    branch_id = int(query.data.split("_")[1])
    branch = get_branch(branch_id)

    if not branch:
        await query.edit_message_text("خطا: شاخه نامعتبر است.")
        return

    channel_username = branch[2]
    
    # اگر کاربر عضو بود دوره‌ها را نشان بده، وگرنه دکمه‌های عضویت را بفرست
    if await is_member(update, context, channel_username):
        await show_courses(update, context, branch_id)
    else:
        keyboard = [
            [InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{channel_username.lstrip('@')}")],
            [InlineKeyboardButton("✅ بررسی عضویت", callback_data=f"check_member_{branch_id}")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"⚠️ برای مشاهده دوره‌های {branch[1]}، ابتدا باید در کانال زیر عضو شوید:\n"
            f"{channel_username}\n\n"
            "پس از عضویت، دکمه «بررسی عضویت» را بزنید.",
            reply_markup=reply_markup
        )

# ---------- بررسی مجدد عضویت ----------
async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # در اینجا دستور اضافه await query.answer() حذف شد
    
    branch_id = int(query.data.split("_")[2])
    branch = get_branch(branch_id)
    
    if not branch:
        await query.answer("خطا: شاخه نامعتبر است.", show_alert=True)
        return
        
    channel_username = branch[2]
    
    if await is_member(update, context, channel_username):
        await query.answer("✅ عضویت شما تأیید شد", show_alert=False)
        await show_courses(update, context, branch_id)
    else:
        await query.answer("❌ هنوز عضو نشده اید. ابتدا عضو شوید.", show_alert=True)# ---------- بازگشت به منوی اصلی / دوره‌ها ----------
async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await show_main_menu(update, context)

async def back_to_courses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    branch_id = int(query.data.split("_")[2])
    await show_courses(update, context, branch_id)

# ---------- هندلر دستور /start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update, context)

# ---------- دستورات ادمین (افزودن شاخه و دوره) ----------
# ادمین می‌تواند با این دستورات، شاخه یا دوره جدید اضافه کند
async def admin_add_branch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # قالب: /addbranch نام شاخه | نام کاربری کانال
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("استفاده: /addbranch نام شاخه | @channel_username")
        return
    try:
        args_text = " ".join(context.args)
        name, channel = args_text.split("|")
        name = name.strip()
        channel = channel.strip().lstrip("@")
        branch_id = add_branch(name, channel)
        await update.message.reply_text(f"✅ شاخه «{name}» با شناسه {branch_id} اضافه شد.")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

async def admin_add_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # قالب: /addcourse شناسه شاخه | عنوان | توضیحات | قیمت | لینک
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("استفاده: /addcourse branch_id | عنوان | توضیحات | قیمت | لینک")
        return
    try:
        args_text = " ".join(context.args)
        parts = args_text.split("|")
        if len(parts) < 5:
            await update.message.reply_text("لطفاً همه فیلدها را با | جدا کنید.")
            return
        branch_id = int(parts[0].strip())
        title = parts[1].strip()
        description = parts[2].strip()
        price = parts[3].strip()
        link = parts[4].strip()
        course_id = add_course(branch_id, title, description, price, link)
        await update.message.reply_text(f"✅ دوره «{title}» با شناسه {course_id} اضافه شد.")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

async def admin_edit_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # قالب: /editcourse شناسه_دوره | عنوان | توضیحات | قیمت | لینک
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("استفاده: /editcourse شناسه_دوره | عنوان | توضیحات | قیمت | لینک")
        return
    try:
        args_text = " ".join(context.args)
        parts = args_text.split("|")
        if len(parts) < 5:
            await update.message.reply_text("لطفاً همه فیلدها را با | جدا کنید.")
            return
            
        course_id = int(parts[0].strip())
        title = parts[1].strip()
        description = parts[2].strip()
        price = parts[3].strip()
        link = parts[4].strip()
        
        update_course(course_id, title, description, price, link)
        await update.message.reply_text(f"✅ دوره شماره {course_id} با موفقیت ویرایش شد.")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")
#-------------------هوش مصنوعی-----------------------------
#-------------------هوش مصنوعی-----------------------------
#-------------------هوش مصنوعی-----------------------------
#-------------------هوش مصنوعی-----------------------------
#-------------------هوش مصنوعی-----------------------------
#-------------------هوش مصنوعی-----------------------------
#-------------------هوش مصنوعی-----------------------------
async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    user_msg = update.message.text
    user_id = update.message.chat_id
    
    branch_id = context.user_data.get('current_branch', 1)
    
    wait_msg = await update.message.reply_text("🤖 در حال بررسی پیام شما...")

    if 'client' not in globals():
        await wait_msg.edit_text("❌ خطا: کلید جمنای لود نشده است.")
        return

    try:
        prompt = f"""
        شما دستیار هوشمند و پشتیبانِ خطِ اولِ پلتفرم آموزشی «دکترلید» هستید.
        مخاطبان شما دندانپزشکان، داروسازان، پزشکان و دانشجویان علوم پزشکی هستند.

        لحن و نحوه برخورد (قانون طلایی):
        شما باید همواره و در تمامی پاسخ‌ها، مخاطب را با عنوان «دکتر» خطاب کنید. لحن شما باید حرفه‌ای و محترمانه باشد.

        اطلاعات پایگاه دانش:
        {knowledge_base}

        قوانین پاسخگویی (بسیار مهم):
        ۱. فقط از اطلاعات پایگاه دانش استفاده کن.
        ۲. اگر پیام کاربر شامل کلمات مالی، شماره کارت، رسید بانکی، سوال تخصصی کلینیکال بیمار یا مشکل فنی بود، فقط کلمه TRANSFER_TO_ADMIN را برگردان.

        متن پیام کاربر: {user_msg}
        """
        
        response = await client.aio.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt
        )
        
        try:
            final_text = response.text.strip()
        except ValueError:
            final_text = "خطا: محتوای پیام توسط فیلترهای امنیتی مسدود شد."
            
        # دکمه‌های استاندارد برای پاسخ‌های معمولی هوش مصنوعی
        standard_keyboard = [
            [InlineKeyboardButton("📚 بازگشت به دوره‌ها", callback_data=f"back_courses_{branch_id}")],
            [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")]
        ]
            
        if "TRANSFER_TO_ADMIN" in final_text:
            # کیبورد اختصاصی زمان ارجاع به ادمین (شامل لینک مستقیم پی‌وی)
            admin_keyboard = [
                [InlineKeyboardButton("💬 چت مستقیم با پشتیبانی", url="https://t.me/pharmalead_support")],
                [InlineKeyboardButton("📚 بازگشت به دوره‌ها", callback_data=f"back_courses_{branch_id}")],
                [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")]
            ]
            
            await wait_msg.edit_text(
                "⏳ درخواست شما نیاز به بررسی ادمین دارد. پیام شما برای پشتیبانی ارسال شد.\n\n"
                "👇 همچنین می‌توانید از طریق دکمه زیر مستقیماً با ادمین در ارتباط باشید:",
                reply_markup=InlineKeyboardMarkup(admin_keyboard)
            )
            
            # فوروارد پیام اصلی کاربر
            await context.bot.forward_message(
                chat_id=ADMIN_CHAT_ID, 
                from_chat_id=user_id, 
                message_id=update.message.message_id
            )
            
            # ایجاد لینک مستقیم ارتباط با کاربر
            user = update.message.from_user
            user_name = user.first_name if user.first_name else "کاربر"
            
            if user.username:
                contact_link = f"@{user.username}"
            else:
                contact_link = f"<a href='tg://user?id={user_id}'>{user_name}</a>"
                
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"👆 کاربر بالا منتظر پاسخ شماست.\n🔗 برای چت با کاربر کلیک کنید: {contact_link}",
                parse_mode="HTML"
            )
        else:
            await wait_msg.edit_text(final_text, reply_markup=InlineKeyboardMarkup(standard_keyboard))
            
    except Exception as e:
        print(f"AI Error: {e}")
        error_keyboard = [
            [InlineKeyboardButton("📚 بازگشت به دوره‌ها", callback_data=f"back_courses_{branch_id}")],
            [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")]
        ]
        await wait_msg.edit_text(f"❌ خطای سرور گوگل:\n{str(e)}", reply_markup=InlineKeyboardMarkup(error_keyboard))
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
# ==========================================
# ۲. کد جدید (هندلر دکمه) را دقیقاً اینجا بگذارید:
async def support_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() 
    
    await query.message.reply_text(
        "👇 لطفاً سوال، درخواست یا مشکل خود را همینجا تایپ کنید.\n"
        "دستیار هوشمند ما در کمتر از چند ثانیه پاسخ خواهد داد:"
    )
#----------------------------
#-------------------دریافت عکس-----------------------------
#-------------------دریافت عکس و پردازش بینایی-----------------------------
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    user = update.message.from_user
    user_name = user.first_name if user.first_name else "کاربر"
    branch_id = context.user_data.get('current_branch', 1)
    
    wait_msg = await update.message.reply_text("🤖 در حال اسکن و پردازش تصویر...")

    if 'client' not in globals():
        await wait_msg.edit_text("❌ خطا: کلید جمنای لود نشده است.")
        return

    try:
        # ۱. دانلود عکس در حافظه موقت (گرفتن بالاترین کیفیت عکس ارسالی)
        photo_file = await context.bot.get_file(update.message.photo[-1].file_id)
        photo_bytes = await photo_file.download_as_bytearray()
        
        # ۲. دستورات بینایی ماشین به جمنای
        prompt = f"""
        شما دستیار هوشمند «دکترلید» هستید. یک تصویر از کاربر دریافت کرده‌اید.
        مخاطبان شما دندانپزشکان، داروسازان و پزشکان هستند (همیشه آنها را "دکتر" خطاب کنید).

        قوانین پردازش تصویر:
        ۱. فیش بانکی: اگر تصویر فیش واریزی، رسید بانکی، عکس کارت به کارت یا صفحه پرداخت است، فقط و فقط کلمه RECEIPT را برگردان.
        ۲. تصویر علمی/پزشکی: اگر تصویر نسخه پزشکی، جواب آزمایش، سوال دارویی یا یک کیس کلینیکال است، با دقت آن را تحلیل کن و به صورت علمی بر اساس پایگاه دانش پاسخ بده. 
        ۳. ارجاع تخصصی: اگر سوال پزشکی در تصویر خارج از دانش شماست یا نیاز به مداخله قطعی ادمین دارد، فقط کلمه TRANSFER_TO_ADMIN را برگردان.
        ۴. تصاویر بی‌ربط: اگر تصویر کاملاً بی‌ربط به فضای پزشکی و آموزشی است (مثلا عکس طبیعت یا خودرو)، محترمانه با کمی طنز توضیح بده که شما فقط برای پشتیبانی آموزشی و پزشکی طراحی شده‌اید.

        اطلاعات پایگاه دانش:
        {knowledge_base}
        """
        
        # ۳. ارسال همزمان عکس و دستورات به سرور گوگل
        response = await client.aio.models.generate_content(
            model='gemini-3.6-flash',
            contents=[
                prompt,
                types.Part.from_bytes(data=bytes(photo_bytes), mime_type='image/jpeg')
            ]
        )
        
        final_text = response.text.strip()
        
        # ۴. تصمیم‌گیری بر اساس جواب هوش مصنوعی
        if "RECEIPT" in final_text or "TRANSFER_TO_ADMIN" in final_text:
            
            if "RECEIPT" in final_text:
                user_reply = "✅ فیش واریزی شما با موفقیت اسکن و برای تایید به ادمین ارسال شد.\nلطفاً تا زمان بررسی شکیبا باشید."
            else:
                user_reply = "⏳ تصویر شما نیاز به بررسی تخصصی ادمین دارد و برای پشتیبانی ارسال شد."
                
            admin_keyboard = [
                [InlineKeyboardButton("💬 چت مستقیم با پشتیبانی", url="https://t.me/pharmalead_support")],
                [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")]
            ]
            
            await wait_msg.edit_text(user_reply, reply_markup=InlineKeyboardMarkup(admin_keyboard))
            
            # فوروارد عکس برای ادمین
            await context.bot.forward_message(
                chat_id=ADMIN_CHAT_ID, 
                from_chat_id=user_id, 
                message_id=update.message.message_id
            )
            
            # ساخت لینک مستقیم ارتباط با کاربر
            if user.username:
                contact_link = f"@{user.username}"
            else:
                contact_link = f"<a href='tg://user?id={user_id}'>{user_name}</a>"
                
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"👆 تصویر بالا از طرف کاربر ارسال شد.\n🔗 برای چت با کاربر کلیک کنید: {contact_link}",
                parse_mode="HTML"
            )
            
        else:
            # پاسخگویی مستقیم هوش مصنوعی به تصاویر علمی یا نامربوط
            standard_keyboard = [
                [InlineKeyboardButton("📚 بازگشت به دوره‌ها", callback_data=f"back_courses_{branch_id}")],
                [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")]
            ]
            await wait_msg.edit_text(final_text, reply_markup=InlineKeyboardMarkup(standard_keyboard))
            
    except Exception as e:
        print(f"AI Vision Error: {e}")
        error_keyboard = [[InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")]]
        await wait_msg.edit_text("❌ خطایی در اسکن تصویر رخ داد. لطفاً دوباره تلاش کنید.", reply_markup=InlineKeyboardMarkup(error_keyboard))
#-------------------------------------------------
#-------------------------------------------------
# ---------- اجرای ربات ----------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # هندلرها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addbranch", admin_add_branch))
    app.add_handler(CommandHandler("addcourse", admin_add_course))
    app.add_handler(CommandHandler("editcourse", admin_edit_course))

    app.add_handler(CallbackQueryHandler(branch_selected, pattern="^branch_"))
    app.add_handler(CallbackQueryHandler(check_membership, pattern="^check_member_"))
    app.add_handler(CallbackQueryHandler(show_course_info, pattern="^course_"))
    app.add_handler(CallbackQueryHandler(back_to_courses, pattern="^back_courses_"))
    app.add_handler(CallbackQueryHandler(back_to_main, pattern="^main_menu$"))
    
    # 👈 هندلر دکمه جدید پشتیبانی (این خط اضافه شد)
    app.add_handler(CallbackQueryHandler(support_button_click, pattern="^ai_support_click$"))

#----------------------------------هوش مصنوعی------------------------------------------------
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("🤖 ربات دکترلید در حال اجرا...")
    app.run_polling()

if __name__ == "__main__":
    main()
