import os
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

from utils.database import (
    init_db, add_user, get_user, is_paid, add_subscription,
    increment_songs, add_payment, get_stats
)
from utils.suno_api import generate_song, get_credits

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
SUBSCRIPTION_PRICE = int(os.getenv('SUBSCRIPTION_PRICE', '250'))

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_PROMPT = 1
WAITING_STYLE = 2
WAITING_TITLE = 3

# === START HANDLER ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username, user.first_name)

    keyboard = [
        [InlineKeyboardButton("🎵 Qo'shiq yaratish", callback_data='generate')],
        [InlineKeyboardButton("💳 Obuna sotib olish", callback_data='subscribe')],
        [InlineKeyboardButton("📊 Mening profilim", callback_data='profile')],
        [InlineKeyboardButton("❓ Yordam", callback_data='help')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"🎵 *Assalomu alaykum, {user.first_name}!*\n\n"
        "Men AI yordamida qo'shiq yaratuvchi botman.\n"
        f"📌 Oyiga *{SUBSCRIPTION_PRICE}* Telegram Stars\n"
        "🎶 Cheksiz qo'shiq yaratishingiz mumkin!\n\n"
        "Quyidagi tugmalardan birini tanlang:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# === GENERATE SONG HANDLER ===
async def generate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if not is_paid(user_id):
        keyboard = [[InlineKeyboardButton("💳 Obuna sotib olish", callback_data='subscribe')]]
        await query.edit_message_text(
            "❌ *Sizda faol obuna yo'q!*\n\n"
            "Qo'shiq yaratish uchun obuna sotib olishingiz kerak.\n"
            f"📌 Narxi: *{SUBSCRIPTION_PRICE}* Telegram Stars/oy",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return

    await query.edit_message_text(
        "🎵 *Qo'shiq yaratish*\n\n"
        "Qo'shiq matnini yuboring.\n"
        "Masalan: "Sevgi haqida uzbek pop qo'shiq, yomg'ir ostida"",
        parse_mode='Markdown'
    )
    return WAITING_PROMPT

async def receive_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text
    context.user_data['prompt'] = prompt

    keyboard = [
        [InlineKeyboardButton("🎤 Pop", callback_data='style_pop')],
        [InlineKeyboardButton("🎸 Rock", callback_data='style_rock')],
        [InlineKeyboardButton("🎹 Jazz", callback_data='style_jazz')],
        [InlineKeyboardButton("🎻 Klassik", callback_data='style_classical')],
        [InlineKeyboardButton("🎧 Hip-Hop", callback_data='style_hiphop')],
        [InlineKeyboardButton("🎶 Elektron", callback_data='style_electronic')],
        [InlineKeyboardButton("🇺🇿 Uzbek", callback_data='style_uzbek')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🎵 *Janrni tanlang:*",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return WAITING_STYLE

async def receive_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    style_map = {
        'style_pop': 'pop',
        'style_rock': 'rock',
        'style_jazz': 'jazz',
        'style_classical': 'classical',
        'style_hiphop': 'hip-hop',
        'style_electronic': 'electronic',
        'style_uzbek': 'uzbek pop'
    }

    style = style_map.get(query.data, 'pop')
    context.user_data['style'] = style

    await query.edit_message_text(
        "📝 *Qo'shiq nomini kiriting*\n\n"
        "Yoki "skip" deb yozing (avtomatik nom):",
        parse_mode='Markdown'
    )
    return WAITING_TITLE

async def receive_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text
    if title.lower() == 'skip':
        title = ""

    prompt = context.user_data.get('prompt', '')
    style = context.user_data.get('style', 'pop')
    user_id = update.effective_user.id

    msg = await update.message.reply_text("⏳ Qo'shiq yaratilmoqda... Bu 1-2 daqiqa vaqt olishi mumkin.")

    audio_url, error = generate_song(prompt, style, title)

    if error:
        await msg.edit_text(f"❌ *Xatolik:* {error}")
        return ConversationHandler.END

    if audio_url:
        await msg.edit_text("✅ Qo'shiq tayyor! Yuklanmoqda...")

        try:
            import requests
            audio_data = requests.get(audio_url, timeout=30).content

            # Vaqtinchalik fayl saqlash
            temp_file = f"/tmp/song_{user_id}_{datetime.now().timestamp()}.mp3"
            with open(temp_file, 'wb') as f:
                f.write(audio_data)

            await update.message.reply_audio(
                audio=open(temp_file, 'rb'),
                title=title if title else "AI Qo'shiq",
                performer="Suno AI",
                caption=f"🎵 Janr: {style}\n📝 Prompt: {prompt[:100]}..."
            )

            os.remove(temp_file)
            increment_songs(user_id)

        except Exception as e:
            await update.message.reply_text(f"❌ Yuklashda xatolik: {str(e)}")

    # Qayta boshlash
    keyboard = [
        [InlineKeyboardButton("🎵 Yana qo'shiq yaratish", callback_data='generate')],
        [InlineKeyboardButton("🏠 Bosh menyu", callback_data='menu')],
    ]
    await update.message.reply_text(
        "Nima yana qilishni xohlaysiz?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return ConversationHandler.END

# === SUBSCRIPTION HANDLER ===
async def subscribe_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("💳 1 oy - 250 Stars", callback_data='pay_1')],
        [InlineKeyboardButton("💳 3 oy - 650 Stars", callback_data='pay_3')],
        [InlineKeyboardButton("💳 6 oy - 1200 Stars", callback_data='pay_6')],
        [InlineKeyboardButton("🏠 Bosh menyu", callback_data='menu')],
    ]

    await query.edit_message_text(
        "💳 *Obuna narxlari*\n\n"
        "📌 1 oy - *250* Stars (~30,000 so'm)\n"
        "📌 3 oy - *650* Stars (~78,000 so'm)\n"
        "📌 6 oy - *1200* Stars (~144,000 so'm)\n\n"
        "Cheksiz qo'shiq yaratish imkoniyati!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    plan_map = {
        'pay_1': (250, 1),
        'pay_3': (650, 3),
        'pay_6': (1200, 6)
    }

    price, months = plan_map.get(query.data, (250, 1))
    context.user_data['payment_months'] = months

    # Telegram Stars to'lovi
    await context.bot.send_invoice(
        chat_id=update.effective_chat.id,
        title=f"Obuna - {months} oy",
        description=f"AI Qo'shiq Bot - {months} oylik obuna",
        payload=f"sub_{months}_{update.effective_user.id}",
        provider_token="",  # Stars uchun bo'sh
        currency="XTR",   # Telegram Stars
        prices=[LabeledPrice(label=f"{months} oy", amount=price)],
        start_parameter=f"sub{months}"
    )

# === PAYMENT SUCCESS ===
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    user_id = update.effective_user.id

    # Payloaddan oylik sonini olish
    payload = payment.invoice_payload
    months = int(payload.split('_')[1])

    # Obunani faollashtirish
    add_subscription(user_id, months)
    add_payment(payment.telegram_payment_charge_id, user_id, payment.total_amount, 'XTR')

    await update.message.reply_text(
        f"✅ *To'lov muvaffaqiyatli!*\n\n"
        f"📅 Obuna muddati: *{months} oy*\n"
        f"💰 To'langan: *{payment.total_amount}* Stars\n\n"
        "Endi qo'shiq yaratishingiz mumkin! 🎵",
        parse_mode='Markdown'
    )

# === PROFILE HANDLER ===
async def profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user = get_user(user_id)

    if not user:
        await query.edit_message_text("❌ Foydalanuvchi topilmadi.")
        return

    is_subscribed = is_paid(user_id)
    sub_end = user[4] if user[4] else "Faol emas"
    songs = user[6]

    status = "✅ Faol" if is_subscribed else "❌ Faol emas"

    await query.edit_message_text(
        f"👤 *Mening profilim*\n\n"
        f"🆔 ID: `{user_id}`\n"
        f"📛 Ism: {user[2]}\n"
        f"📅 Obuna holati: {status}\n"
        f"📆 Obuna tugashi: {sub_end}\n"
        f"🎵 Yaratilgan qo'shiqlar: {songs}\n"
        f"💰 Jami to'lovlar: {user[7]} Stars",
        parse_mode='Markdown'
    )

# === HELP HANDLER ===
async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "❓ *Yordam*\n\n"
        "🎵 *Qo'shiq yaratish:*\n"
        "1. Obuna sotib oling\n"
        "2. 'Qo'shiq yaratish' tugmasini bosing\n"
        "3. Qo'shiq matnini yozing\n"
        "4. Janrni tanlang\n"
        "5. Nom kiriting\n"
        "6. AI qo'shiq yaratadi!\n\n"
        "💳 *To'lov:* Telegram Stars orqali\n"
        "📞 @admin bilan bog'laning",
        parse_mode='Markdown'
    )

# === MENU HANDLER ===
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("🎵 Qo'shiq yaratish", callback_data='generate')],
        [InlineKeyboardButton("💳 Obuna sotib olish", callback_data='subscribe')],
        [InlineKeyboardButton("📊 Mening profilim", callback_data='profile')],
        [InlineKeyboardButton("❓ Yordam", callback_data='help')],
    ]

    await query.edit_message_text(
        "🏠 *Bosh menyu*\n\n"
        "Quyidagi tugmalardan birini tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# === ADMIN HANDLER ===
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return

    stats = get_stats()

    await update.message.reply_text(
        f"📊 *Bot statistikasi*\n\n"
        f"👥 Jami foydalanuvchilar: {stats['total_users']}\n"
        f"💳 Pullik obunalar: {stats['paid_users']}\n"
        f"🎵 Yaratilgan qo'shiqlar: {stats['total_songs']}\n"
        f"💰 Jami daromad: {stats['total_earnings']} Stars",
        parse_mode='Markdown'
    )

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return

    message = ' '.join(context.args)
    if not message:
        await update.message.reply_text("❌ Xabar matnini kiriting: /broadcast <xabar>")
        return

    # Barcha foydalanuvchilarga yuborish (soddalashtirilgan)
    await update.message.reply_text(f"📢 Xabar yuborildi: {message}")

# === MAIN ===
def main():
    init_db()

    application = Application.builder().token(BOT_TOKEN).build()

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(generate_callback, pattern='^generate$')],
        states={
            WAITING_PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_prompt)],
            WAITING_STYLE: [CallbackQueryHandler(receive_style, pattern='^style_')],
            WAITING_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_title)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: u.message.reply_text("Bekor qilindi."))],
    )

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", admin_stats))
    application.add_handler(CommandHandler("broadcast", admin_broadcast))
    application.add_handler(conv_handler)

    application.add_handler(CallbackQueryHandler(subscribe_callback, pattern='^subscribe$'))
    application.add_handler(CallbackQueryHandler(payment_callback, pattern='^pay_'))
    application.add_handler(CallbackQueryHandler(profile_callback, pattern='^profile$'))
    application.add_handler(CallbackQueryHandler(help_callback, pattern='^help$'))
    application.add_handler(CallbackQueryHandler(menu_callback, pattern='^menu$'))

    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    print("🤖 Bot ishga tushdi!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
