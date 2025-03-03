import os
import telebot
from telebot import types

API_TOKEN = '7817440343:AAFEAXnRaRxv3STLGx5N9_8kBasy4fvvFLw'
OWNER_ID = 960173511  # بدّلها بمعرف التليجرام مالك

bot = telebot.TeleBot(API_TOKEN)

# تخزين رسائل المستخدمين اللي يحتاجون ردود
pending_messages = {}

# رسالة الترحيب بصورة
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = "مرحباً بيك في بوت التواصل! شلون أگدر أساعدك اليوم؟"
    bot.send_photo(message.chat.id, photo='https://telegra.ph/-01-26-17917', caption=welcome_text)

# التعامل مع أمر المساعدة
@bot.message_handler(commands=['help'])
def send_help(message):
    if message.from_user.id == OWNER_ID:
        help_text = """
        هاي هي الأوامر الي تقدر تستخدمها:
        /start - رسالة الترحيب
        /help - قائمة الأوامر
        /broadcast [رسالة] - نشر رسالة لكل المستخدمين

        كمالك للبوت تقدر تسوي هاي الأمور:
        1️⃣ ترد على أي رسالة محولة إليك
        2️⃣ ترد على الإشعار الي يظهر تحت الرسائل المحولة
        3️⃣ تستخدم الأمر /reply [معرف الرسالة] [النص]
        """
    else:
        help_text = """
        هاي هي الأوامر الي تقدر تستخدمها:
        /start - رسالة الترحيب
        /help - قائمة الأوامر
        
        رسالتك راح تنرسل للمسؤول حتى يرد عليك.
        """
    bot.send_message(message.chat.id, help_text)

# أمر للبث من قبل المسؤول
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "آسف، بس مالك حق تستخدم هذا الأمر.")
        return

    broadcast_text = message.text.replace('/broadcast ', '', 1)
    if not broadcast_text:
        bot.reply_to(message, "لازم تكتب رسالة للبث!")
        return

    # هاي الحالة تقدر تبث الرسالة لجميع المستخدمين لو كان عندك قاعدة بيانات
    bot.reply_to(message, f"تم إرسال رسالة البث: {broadcast_text}")

# أمر الرد على رسائل معينة من قبل المسؤول
@bot.message_handler(commands=['reply'])
def reply_command(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "آسف، بس مالك حق تستخدم هذا الأمر.")
        return

    try:
        # استخراج معرف الرسالة والنص المطلوب الرد عليه
        parts = message.text.split(' ', 2)
        if len(parts) < 3:
            bot.reply_to(message, "استخدام: /reply [معرف الرسالة] [النص]")
            return
        
        message_id = parts[1]
        reply_text = parts[2]
        
        if message_id in pending_messages:
            user_id = pending_messages[message_id]['user_id']
            original_msg_id = pending_messages[message_id]['message_id']
            
            # إرسال الرد للمستخدم كإجابة مباشرة على رسالته الأصلية
            bot.send_message(user_id, reply_text, reply_to_message_id=original_msg_id)
            bot.reply_to(message, "تم إرسال الرد بنجاح!")
        else:
            bot.reply_to(message, "معرف الرسالة غير موجود.")
    except Exception as e:
        bot.reply_to(message, f"خطأ في إرسال الرد: {str(e)}")

# التعامل مع الرسائل الواردة
@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker', 'animation'])
def handle_all_messages(message):
    # إذا كانت الرسالة رد من المالك
    if message.reply_to_message and message.from_user.id == OWNER_ID:
        # أولاً نتحقق إذا كانت الرسالة المحولة من مستخدم
        if hasattr(message.reply_to_message, 'forward_from') and message.reply_to_message.forward_from is not None:
            user_id = message.reply_to_message.forward_from.id
            # إعادة إرسال رد المالك للمستخدم
            try:
                original_msg_id = message.reply_to_message.forward_from_message_id

                if message.content_type == 'text':
                    bot.send_message(user_id, message.text, reply_to_message_id=original_msg_id)
                elif message.content_type == 'photo':
                    bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption, reply_to_message_id=original_msg_id)
                elif message.content_type == 'video':
                    bot.send_video(user_id, message.video.file_id, caption=message.caption, reply_to_message_id=original_msg_id)
                elif message.content_type == 'document':
                    bot.send_document(user_id, message.document.file_id, caption=message.caption, reply_to_message_id=original_msg_id)
                elif message.content_type == 'audio':
                    bot.send_audio(user_id, message.audio.file_id, caption=message.caption, reply_to_message_id=original_msg_id)
                elif message.content_type == 'voice':
                    bot.send_voice(user_id, message.voice.file_id, caption=message.caption, reply_to_message_id=original_msg_id)
                elif message.content_type == 'sticker':
                    bot.send_sticker(user_id, message.sticker.file_id, reply_to_message_id=original_msg_id)
                elif message.content_type == 'animation':
                    bot.send_animation(user_id, message.animation.file_id, caption=message.caption, reply_to_message_id=original_msg_id)

                bot.reply_to(message, "✅ تم إرسال الرد للمستخدم!")
                return
            except Exception as e:
                bot.reply_to(message, f"❌ خطأ في إرسال الرد: {str(e)}")
                return

    # إذا كانت الرسالة من مستخدم عادي أو مش رد
    if message.from_user.id != OWNER_ID:
        # توليد معرف فريد لهذه الرسالة
        unique_id = f"{message.chat.id}_{message.message_id}"
        
        # تخزين معلومات الرسالة للرد عليها لاحقاً
        pending_messages[unique_id] = {
            'user_id': message.chat.id,
            'message_id': message.message_id
        }

        try:
            # تحويل الرسالة للمسؤول
            forwarded = bot.forward_message(OWNER_ID, message.chat.id, message.message_id)

            # إنشاء إشعار منظم يوضح كيفية الرد المباشر
            user_name = message.from_user.first_name
            if message.from_user.last_name:
                user_name += f" {message.from_user.last_name}"
            if message.from_user.username:
                user_name += f" (@{message.from_user.username})"
            
            bot.reply_to(forwarded,
                f"معرف الرسالة: {unique_id}\n"
                f"من: {user_name}\n"
                f"💬 رد مباشرة على هذه الرسالة للرد على المستخدم"
            )

            # تأكيد للمستخدم
            bot.reply_to(message, "تم إرسال رسالتك للمسؤول. راح يرد عليك قريباً!")
        except Exception as e:
            bot.reply_to(message, f"خطأ في تحويل الرسالة: {str(e)}")
            print(f"خطأ في تحويل الرسالة: {e}")
    else:
        bot.reply_to(message, "مرحباً مالك البوت! استخدم /help لتشوف الأوامر المتاحة.")

# بدء الاستعلام عن الرسائل
bot.polling()