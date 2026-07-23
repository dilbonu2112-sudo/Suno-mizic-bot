# 🎵 AI Qo'shiq Yaratuvchi Telegram Bot

> Suno AI yordamida qo'shiq yaratuvchi, Telegram Stars orqali pullik obuna tizimi bilan ishlaydigan bot.

## 💰 Narxlari

| Reja | Narxi | Chegirma |
|------|-------|----------|
| 1 oy | 250 Stars (~30,000 so'm) | - |
| 3 oy | 650 Stars (~78,000 so'm) | 13% chegirma |
| 6 oy | 1200 Stars (~144,000 so'm) | 20% chegirma |

## 🚀 O'rnatish

### 1. Kerakli narsalar

- Python 3.10+
- Telegram Bot Token (@BotFather dan)
- Suno AI Cookie (suno.com dan)
- Telegram Stars qabul qilish (BotFather'da sozlash)

### 2. O'rnatish

```bash
# Repositoriyani klonlash
git clone <repo-url>
cd suno_music_bot

# Muhit yaratish
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Kutubxonalarni o'rnatish
pip install -r requirements.txt

# Sozlamalar
mv .env.example .env
# .env faylini tahrirlang
```

### 3. .env fayli

```env
BOT_TOKEN=your_bot_token_here
SUNO_COOKIE=your_suno_cookie_here
ADMIN_ID=123456789
SUBSCRIPTION_PRICE=250
```

### 4. Ishga tushirish

```bash
python main.py
```

## 🎵 Bot buyruqlari

| Buyruq | Tavsif |
|--------|--------|
| `/start` | Botni ishga tushirish |
| `/stats` | Admin statistikasi |
| `/broadcast` | Barchaga xabar yuborish |

## 🔄 Bot ish tartibi

1. Foydalanuvchi `/start` bosadi
2. Obuna sotib olish tugmasini bosadi
3. Telegram Stars orqali to'lov qiladi
4. "Qo'shiq yaratish" tugmasini bosadi
5. Qo'shiq matnini yuboradi
6. Janrni tanlaydi
7. Nom kiriting yoki skip
8. AI qo'shiq yaratadi va yuboradi

## 📁 Loyiha tuzilmasi

```
suno_music_bot/
├── main.py           # Asosiy bot kodi
├── requirements.txt  # Kutubxonalar
├── .env.example      # Muhit o'zgaruvchilari namunasi
├── bot.db            # SQLite ma'lumotlar bazasi
├── utils/
│   ├── database.py   # Ma'lumotlar bazasi moduli
│   └── suno_api.py   # Suno AI API moduli
└── README.md         # Qo'llanma
```

## ⚠️ Diqqat

- Suno AI cookie muddati tugashi mumkin - yangilab turish kerak
- Telegram Stars faqat ba'zi mamlakatlarda mavjud
- Serverda botni doimiy ishlash uchun systemd yoki Docker ishlating

## 📞 Bog'lanish

Admin: @your_username
