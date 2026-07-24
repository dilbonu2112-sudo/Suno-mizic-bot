import sqlite3
from datetime import datetime, timedelta
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bot.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            joined_date TEXT,
            subscription_end TEXT,
            is_paid INTEGER DEFAULT 0,
            songs_generated INTEGER DEFAULT 0,
            total_payments INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            payment_id TEXT PRIMARY KEY,
            user_id INTEGER,
            amount INTEGER,
            currency TEXT,
            payment_date TEXT,
            status TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            song_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            prompt TEXT,
            song_url TEXT,
            created_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_user(user_id, username, first_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR IGNORE INTO users (user_id, username, first_name, joined_date) VALUES (?, ?, ?, ?)',
        (user_id, username, first_name, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def is_paid(user_id):
    user = get_user(user_id)
    if not user:
        return False
    subscription_end = user[4]
    if not subscription_end:
        return False
    end_date = datetime.fromisoformat(subscription_end)
    return datetime.now() < end_date

def add_subscription(user_id, months=1):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    user = get_user(user_id)
    current_end = user[4] if user else None
    
    if current_end and datetime.fromisoformat(current_end) > datetime.now():
        new_end = datetime.fromisoformat(current_end) + timedelta(days=30*months)
    else:
        new_end = datetime.now() + timedelta(days=30*months)
    
    cursor.execute(
        'UPDATE users SET subscription_end = ?, is_paid = 1 WHERE user_id = ?',
        (new_end.isoformat(), user_id)
    )
    conn.commit()
    conn.close()

def increment_songs(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE users SET songs_generated = songs_generated + 1 WHERE user_id = ?',
        (user_id,)
    )
    conn.commit()
    conn.close()

def add_payment(payment_id, user_id, amount, currency, status='completed'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO payments (payment_id, user_id, amount, currency, payment_date, status) VALUES (?, ?, ?, ?, ?, ?)',
        (payment_id, user_id, amount, currency, datetime.now().isoformat(), status)
    )
    cursor.execute(
        'UPDATE users SET total_payments = total_payments + ? WHERE user_id = ?',
        (amount, user_id)
    )
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_paid = 1')
    paid_users = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM songs')
    total_songs = cursor.fetchone()[0]
    cursor.execute('SELECT SUM(total_payments) FROM users')
    total_earnings = cursor.fetchone()[0] or 0
    conn.close()
    return {
        'total_users': total_users,
        'paid_users': paid_users,
        'total_songs': total_songs,
        'total_earnings': total_earnings
    }
