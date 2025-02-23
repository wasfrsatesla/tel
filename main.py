import telebot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand, InputMediaPhoto, InputMediaVideo
import os
import time
from functools import wraps
import logging

# إعدادات البوت
TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
WELCOME_IMAGE = os.getenv("WELCOME_IMAGE")
BOT_USERNAME = os.getenv("BOT_USERNAME")

# التحقق من تحميل المتغيرات
if not TOKEN or not ADMIN_ID:
    raise ValueError("❌ تأكد من ضبط جميع المتغيرات في Secrets!")

user_message_ids = {}
user_states = {}  # لتتبع حالة المستخدم (مثل إرسال رسالة جماعية)

# إعدادات تسجيل الأخطاء (Logging)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def retry_on_rate_limit(max_retries=3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except telebot.apihelper.ApiTelegramException as e:
                    if e.error_code == 429:
                        retry_after = int(str(e).split('retry after ')[1])
                        logging.warning(f"تم تجاوز الحد الأقصى للطلبات. الانتظار لمدة {retry_after} ثانية.")
                        time.sleep(retry_after)
                        retries += 1
                        continue
                    raise
            raise Exception("❌ فشلت العملية بعد عدة محاولات.")
        return wrapper
    return decorator

class Bot:
    def __init__(self):
        self.bot = telebot.TeleBot(TOKEN)
        self.setup_handlers()
        self.setup_commands()
        self.admin_keyboard = self.create_admin_keyboard()  # لوحة مفاتيح خاصة للإدارة

    def setup_commands(self):
        commands = [
            BotCommand("start", "يا هلا بيك"),
            BotCommand("help", "شتحتاج؟"),
            BotCommand("info", "معلومات عن البوت"),
        ]
        self.bot.set_my_commands(commands)

    def create_keyboard(self):
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        keyboard.add(
            KeyboardButton("📞 احجي وياي"),
            KeyboardButton("❓ المساعدة"),
        )
        return keyboard

    def create_admin_keyboard(self):
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        keyboard.add(
            KeyboardButton("📢 إرسال رسالة للكل"),  # زر لإرسال رسالة جماعية
        )
        return keyboard

    def create_welcome_inline_buttons(self):
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton("📢 قناتي", url="https://t.me/your_channel"),
            InlineKeyboardButton("🌍 موقعي", url="https://alihaidershaker.vercel.app/"),
            InlineKeyboardButton("✉️ راسلني", callback_data="contact_me"),
        )
        return keyboard

    def format_welcome_message(self, user):
        name = user.first_name
        welcome_text = f"هلو، اني زهرة. شلون اكدر اساعدك، {name}؟\nاترك رسالة واراح اساعدك بأقرب فرصة."
        return welcome_text

    def setup_handlers(self):
        @self.bot.message_handler(commands=['start'])
        @retry_on_rate_limit()
        def start(message):
            try:
                welcome_text = self.format_welcome_message(message.from_user)
                if WELCOME_IMAGE:
                    self.bot.send_photo(
                        message.chat.id,
                        photo=WELCOME_IMAGE,
                        caption=welcome_text,
                        reply_markup=self.create_welcome_inline_buttons(),
                        parse_mode='HTML'
                    )
                else:
                    self.bot.send_message(
                        message.chat.id,
                        welcome_text,
                        reply_markup=self.create_welcome_inline_buttons(),
                        parse_mode='HTML'
                    )
                self.bot.send_message(
                    message.chat.id,
                    "استخدم القائمة الجوة:",
                    reply_markup=self.create_keyboard()
                )

                if message.from_user.id != ADMIN_ID:
                    new_user_info = f"""
👤 مستخدم جديد طب للبوت:
• الاسم: {message.from_user.first_name} {message.from_user.last_name or ''}
• المعرف: @{message.from_user.username or 'ماكو'}
• الآيدي: {message.from_user.id}
                    """
                    self.bot.send_message(ADMIN_ID, new_user_info)
                    logging.info(f"New user: {message.from_user.id}")

            except Exception as e:
                logging.exception("Error in start handler:")
                self.bot.reply_to(message, "عذرًا، صار خلل. حاول مرة لخ.")

        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            if call.data == "contact_me":
                contact_text = "دز رسالتك و ارد عليك بأقرب وقت."
                self.bot.answer_callback_query(call.id)
                self.bot.send_message(call.message.chat.id, contact_text)

        @self.bot.message_handler(commands=['info'])
        def info(message):
            info_text = f"""
🤖 معلومات عن البوت:
- آني بوت صممته علمود أخدمك.
- صممتي: @{BOT_USERNAME}
- قناتي: [https://t.me/your_channel](https://t.me/your_channel)
            """
            self.bot.reply_to(message, info_text, parse_mode='Markdown')

        @self.bot.message_handler(commands=['help'])
        def help(message):
            help_text = """
🆘 المساعدة:
- /start: بدء استخدام البوت.
- /help: عرض رسالة المساعدة.
- /info: معلومات عن البوت.
            """
            self.bot.reply_to(message, help_text)

        @self.bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and message.text == "📢 إرسال رسالة للكل")
        def admin_broadcast_message_start(message):
            self.bot.reply_to(message, "دز الرسالة اللي تريد أرسلها للكل.")
            user_states[message.from_user.id] = "waiting_for_broadcast_message"

        @self.bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_for_broadcast_message", content_types=['text', 'photo', 'video', 'sticker', 'document'])
        def admin_broadcast_message_content(message):
            try:
                count = 0
                # لا توجد لدينا الآن قائمة مستخدمين، لذا يجب أن نعتمد على شيء آخر
                # على سبيل المثال، يمكنك تخزين IDs في قاعدة بيانات أو ملف مؤقت
                # هذا مثال تقريبي، يجب استبداله بمنطق حقيقي
                # في هذا المثال، سنرسل الرسالة فقط إلى المسؤول كإثبات للمفهوم
                user_id = ADMIN_ID
                try:
                    if message.content_type == 'text':
                        self.bot.send_message(user_id, message.text)
                    elif message.content_type == 'photo':
                        self.bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption)
                    elif message.content_type == 'video':
                        self.bot.send_video(user_id, message.video.file_id, caption=message.caption)
                    elif message.content_type == 'sticker':
                        self.bot.send_sticker(user_id, message.sticker.file_id)
                    elif message.content_type == 'document':
                        self.bot.send_document(user_id, message.document.file_id, caption=message.caption)
                    count += 1
                    time.sleep(0.05)  # تجنب تجاوز الحد الأقصى للطلبات
                except Exception as e:
                    logging.warning(f"Failed to send message to {user_id}: {e}")
                self.bot.reply_to(message, f"تم إرسال الرسالة إلى {count} مستخدم (مثال فقط).")
            except Exception as e:
                logging.exception("Error during broadcast:")
                self.bot.reply_to(message, "صار خلل أثناء إرسال الرسالة.")
            finally:
                user_states[message.from_user.id] = None  # reset state

        @self.bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'sticker', 'document'])
        def handle_messages(message):
            try:
                if message.text == "📞 احجي وياي":
                    contact_text = "دز رسالتك و ارد عليك."
                    self.bot.reply_to(message, contact_text)

                elif message.text == "❓ المساعدة":
                    help_text = "شلون اكدر اساعدك اليوم؟"
                    self.bot.reply_to(message, help_text)
                else:
                    # معالجة الرسائل العادية (إعادة توجيه إلى المسؤول أو الرد التلقائي)
                    self.bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
                    self.bot.reply_to(message, "وصلت رسالتك للمسؤول. شكراً لتواصلك.")

            except Exception as e:
                logging.exception("Error handling message:")
                self.bot.reply_to(message, "صار خلل. حاول مرة لخ.")

    def run(self):
        print("✅ البوت يشتغل...")
        self.bot.remove_webhook()  # إزالة الويب هوك
        self.bot.infinity_polling(timeout=20, long_polling_timeout=5)  # تشغيل البوت في وضع polling

if __name__ == "__main__":
    bot = Bot()
    bot.run()
