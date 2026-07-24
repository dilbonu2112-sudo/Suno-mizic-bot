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

WAITING_PROMPT = 1
WAITING_STYLE = 2
WAITING_TITLE = 3


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
        'Masalan: "Sevgi haqida uzbek pop qoshiq, yomgir ostida"',
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
