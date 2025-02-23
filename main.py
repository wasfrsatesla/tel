import telebot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
import os
import time
from functools import wraps

# إعدادات البوت
TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
WELCOME_IMAGE = os.getenv("WELCOME_IMAGE")
BOT_USERNAME = os.getenv("BOT_USERNAME")

# التحقق من تحميل المتغيرات
if not TOKEN or not ADMIN_ID:
    raise ValueError("❌ تأكد من ضبط جميع المتغيرات في Secrets!")

user_message_ids = {}

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
                        print(f"❌ تم تجاوز الحد الأقصى للطلبات. الانتظار لمدة {retry_after} ثانية.")
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

    def setup_commands(self):
        commands = [
            BotCommand("start", "يا هلا بيك"),
            BotCommand("help", "شتحتاج؟"),
            BotCommand("setcommands", "تحديث الأوامر (بس للمشرف)"),
        ]
        self.bot.set_my_commands(commands)

    def create_keyboard(self):
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        keyboard.add(
            KeyboardButton("🤝 منو آني؟"),
            KeyboardButton("📞 احجي وياي"),
            KeyboardButton("❓ المساعدة"),
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
        welcome_text = f"هَلا بيك {name}!\nيا هلا بيك بـ البوت مالتي. بالخدمة شتحتاج."
        return welcome_text

    def setup_handlers(self):
        @self.bot.message_handler(commands=['start'])
        @retry_on_rate_limit()
        def start(message):
            try:
                welcome_text = self.format_welcome_message(message.from_user)
                self.bot.send_photo(
                    message.chat.id,
                    photo=WELCOME_IMAGE,
                    caption=welcome_text,
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

            except Exception as e:
                print(f"Error in start handler: {e}")
                self.bot.reply_to(message, "عذرًا، صار خلل. حاول مرة لخ.")

        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            if call.data == "contact_me":
                contact_text = "دز رسالتك و ارد عليك بأقرب وقت."
                self.bot.answer_callback_query(call.id)
                self.bot.send_message(call.message.chat.id, contact_text)

        # هذا الـ handler الجديد يستقبل جميع أنواع الرسائل
        @self.bot.message_handler(content_types=['text', 'photo', 'audio', 'document', 'video', 'sticker', 'voice', 'location', 'contact'])
        def handle_all_messages(message):
            if message.from_user.id != ADMIN_ID:
                try:
                    # بناء نص الرسالة المرسلة إلى المسؤول بناءً على نوع الوسائط
                    forward_text = f"""
📩 رسالة جديدة من مستخدم:
👤 {message.from_user.first_name} {message.from_user.last_name or ''}
🆔 {message.from_user.id}
📱 @{message.from_user.username or 'ماكو'}

"""

                    # إضافة معلومات حول الوسائط المرسلة
                    if message.text:
                        forward_text += f"💬 الرسالة: {message.text}\n"
                    elif message.photo:
                        forward_text += "🖼️ صورة\n"
                    elif message.audio:
                        forward_text += "🎵 ملف صوتي\n"
                    elif message.document:
                        forward_text += f"📄 مستند: {message.document.file_name}\n"
                    elif message.video:
                        forward_text += "📹 فيديو\n"
                    elif message.sticker:
                        forward_text += "⭐ ملصق\n"
                    elif message.voice:
                        forward_text += "🎤 رسالة صوتية\n"
                    elif message.location:
                        forward_text += "📍 موقع\n"
                    elif message.contact:
                        forward_text += "👤 جهة اتصال\n"

                    # إرسال الرسالة إلى المسؤول
                    sent_message = self.bot.send_message(ADMIN_ID, forward_text)

                    # إذا كانت هناك صورة، أرسلها بشكل منفصل
                    if message.photo:
                        best_photo = max(message.photo, key=lambda p: p.file_size)
                        photo_file_id = best_photo.file_id
                        self.bot.send_photo(ADMIN_ID, photo_file_id)

                    # تخزين معلومات الرسالة لإمكانية الرد
                    user_message_ids[sent_message.message_id] = (message.chat.id, message.message_id)
                    self.bot.reply_to(message, "وصلت رسالتك و قريب ارد عليك!");

                except Exception as e:
                    print(f"Error forwarding message to admin: {e}")
                    self.bot.reply_to(message, "عذرًا، صار خلل. حاول ترسل الرسالة مرة لخ.");

            elif message.reply_to_message and message.from_user.id == ADMIN_ID:
                try:
                    reply_to_message_id = message.reply_to_message.message_id
                    if reply_to_message_id in user_message_ids:
                        user_chat_id, original_message_id = user_message_ids[reply_to_message_id]
                        reply_text = message.text
                        self.bot.send_message(user_chat_id, f"رد من المسؤول:\n{reply_text}", reply_to_message_id=original_message_id)
                        self.bot.reply_to(message, "تم إرسال الرد للمستخدم.");
                        del user_message_ids[reply_to_message_id]

                    else:
                        self.bot.reply_to(message, "ما لكيت الرسالة الأصلية.");

                except Exception as e:
                    print(f"Error sending reply to user: {e}")
                    self.bot.reply_to(message, "عذرًا، صار خلل. حاول ترسل الرد مرة لخ.");

        @self.bot.message_handler(func=lambda message: True)
        def handle_messages(message):
            if message.text == "🤝 منو آني؟":
                about_text = "آني بوت صممته علمود أخدمك بـ [مجال معين]."
                self.bot.reply_to(message, about_text)

            elif message.text == "📞 احجي وياي":
                contact_text = "دز رسالتك و ارد عليك."
                self.bot.reply_to(message, contact_text)

            elif message.text == "❓ المساعدة":
                help_text = "شلون اكدر اساعدك اليوم؟"
                self.bot.reply_to(message, help_text)

            elif message.text == "/setcommands" and message.from_user.id == ADMIN_ID:
                self.setup_commands()
                self.bot.reply_to(message, "تم تحديث قائمة الأوامر.")

    def run(self):
        print("✅ البوت يشتغل...")
        self.bot.remove_webhook()  # إزالة الويب هوك
        self.bot.infinity_polling(timeout=20, long_polling_timeout=5)  # تشغيل البوت في وضع polling

if __name__ == "__main__":
    bot = Bot() 
    bot.run() 
