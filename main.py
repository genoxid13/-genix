import asyncio
import logging
import random
import re
import os
import sqlite3
import time
import string
from datetime import datetime

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BufferedInputFile

# ==========================================================
# 1. ТОКЕНЫ
# ==========================================================
BOT_TOKEN = "8898824168:AAE6xJm-636BSaZBzecynzLBFGUk7bPN9DA"
ADMIN_BOT_TOKEN = "8099293642:AAHZvzUMVG-b_E2sxmFbhD7KOCYSlihRWD8"

# ==========================================================
# 2. ГЛАВНЫЙ АДМИН
# ==========================================================
OWNER_ID = 7733553137

# ==========================================================
# 3. КАНАЛ
# ==========================================================
CHANNEL_LINK = "https://t.me/+N6e8idLRiqJjZGQy"
CHANNEL_ID = -1003718500868

# ==========================================================
# 4. ФОТО И ССЫЛКИ
# ==========================================================
MAIN_MENU_PHOTO = "https://i.ibb.co/vvQbqP5P/IMG-3963.jpg"
RULES_LINK = "https://teletype.in/@yuopoma/AY1cOPn5Lt1"

# ==========================================================
# 5. КУЛДАУНЫ (+50%)
# ==========================================================
COOLDOWN_BOT = int(10 * 60 * 1.5)          # 15 мин
COOLDOWN_REPORT = int(15 * 60 * 1.5)       # 22 мин 30 сек
COOLDOWN_FREEZE = int(12 * 60 * 60 * 1.5)  # 18 часов
COOLDOWN_AU = int(60 * 60 * 1.5)           # 90 мин
COOLDOWN_PROMO = 60 * 60                    # 1 час
COOLDOWN_DSA = int(30 * 60 * 1.5)          # 45 мин
COOLDOWN_STRESS = int(30 * 60 * 1.5)       # 45 мин
COOLDOWN_WEB = int(30 * 60 * 1.5)          # 45 мин

# ==========================================================
# 6. ПРОМОКОД
# ==========================================================
PROMO_DURATION = 24 * 60 * 60

# ==========================================================
# 7. РЕФЕРАЛЬНАЯ СИСТЕМА
# ==========================================================
REFERRALS_NEEDED = 5
REFERRAL_REWARD_SECONDS = 24 * 60 * 60

# ==========================================================
# 8. БАЗА ДАННЫХ
# ==========================================================
DB_PATH = os.getenv("DB_PATH", "bot_database.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)""")
    c.execute("""CREATE TABLE IF NOT EXISTS basic_subs (user_id INTEGER PRIMARY KEY)""")
    c.execute("""CREATE TABLE IF NOT EXISTS vip_subs (user_id INTEGER PRIMARY KEY)""")
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        date TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS mirrors (
        token TEXT PRIMARY KEY,
        username TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS cooldowns (
        user_id INTEGER,
        action TEXT,
        last_time REAL,
        PRIMARY KEY (user_id, action)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS promocodes (
        code TEXT PRIMARY KEY,
        created_by INTEGER,
        used_by INTEGER,
        expires_at REAL,
        created_at REAL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS temp_subs (
        user_id INTEGER PRIMARY KEY,
        expires_at REAL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS referral_codes (
        user_id INTEGER PRIMARY KEY,
        code TEXT UNIQUE
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS referrals (
        referrer_id INTEGER,
        referred_id INTEGER PRIMARY KEY,
        date REAL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS referral_rewards (
        user_id INTEGER PRIMARY KEY,
        total_referrals INTEGER DEFAULT 0,
        reward_count INTEGER DEFAULT 0
    )""")

    c.execute("SELECT COUNT(*) FROM admins")
    if c.fetchone()[0] == 0:
        c.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (OWNER_ID,))

    c.execute("SELECT COUNT(*) FROM basic_subs")
    if c.fetchone()[0] == 0:
        for uid in [8325273558, 7971767894]:
            c.execute("INSERT OR IGNORE INTO basic_subs (user_id) VALUES (?)", (uid,))

    c.execute("SELECT COUNT(*) FROM vip_subs")
    if c.fetchone()[0] == 0:
        for uid in [7747358607]:
            c.execute("INSERT OR IGNORE INTO vip_subs (user_id) VALUES (?)", (uid,))

    conn.commit()
    conn.close()

def db_get_admins():
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT user_id FROM admins"); r = [x[0] for x in c.fetchall()]
    conn.close(); return r

def db_add_admin(uid):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (uid,))
    conn.commit(); conn.close()

def db_remove_admin(uid):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("DELETE FROM admins WHERE user_id=?", (uid,))
    conn.commit(); conn.close()

def db_get_basic():
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT user_id FROM basic_subs"); r = [x[0] for x in c.fetchall()]
    conn.close(); return r

def db_add_basic(uid):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("DELETE FROM vip_subs WHERE user_id=?", (uid,))
    c.execute("INSERT OR IGNORE INTO basic_subs (user_id) VALUES (?)", (uid,))
    conn.commit(); conn.close()

def db_remove_basic(uid):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("DELETE FROM basic_subs WHERE user_id=?", (uid,))
    conn.commit(); conn.close()

def db_get_vip():
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT user_id FROM vip_subs"); r = [x[0] for x in c.fetchall()]
    conn.close(); return r

def db_add_vip(uid):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("DELETE FROM basic_subs WHERE user_id=?", (uid,))
    c.execute("INSERT OR IGNORE INTO vip_subs (user_id) VALUES (?)", (uid,))
    conn.commit(); conn.close()

def db_remove_vip(uid):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("DELETE FROM vip_subs WHERE user_id=?", (uid,))
    conn.commit(); conn.close()

def db_get_users():
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT user_id, username, first_name, date FROM users"); r = c.fetchall()
    conn.close(); return r

def db_add_user(uid, username, first_name, date):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, first_name, date) VALUES (?, ?, ?, ?)",
              (uid, username, first_name, date))
    conn.commit(); conn.close()

def db_get_mirrors():
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT token, username FROM mirrors"); r = c.fetchall()
    conn.close(); return r

def db_add_mirror(token, username):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO mirrors (token, username) VALUES (?, ?)", (token, username))
    conn.commit(); conn.close()

def cd_get_last(user_id, action):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT last_time FROM cooldowns WHERE user_id=? AND action=?", (user_id, action))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def cd_set_last(user_id, action):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO cooldowns (user_id, action, last_time) VALUES (?, ?, ?)",
              (user_id, action, time.time()))
    conn.commit(); conn.close()

def cd_check(user_id, action, cooldown_seconds):
    last = cd_get_last(user_id, action)
    if last == 0:
        return True, 0
    elapsed = time.time() - last
    if elapsed >= cooldown_seconds:
        return True, 0
    return False, int(cooldown_seconds - elapsed)

def cd_format(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    parts = []
    if h: parts.append(f"{h} ч.")
    if m: parts.append(f"{m} мин.")
    if s or not parts: parts.append(f"{s} сек.")
    return " ".join(parts)

def gen_promo_code(length=10):
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))

def db_create_promo(created_by):
    code = gen_promo_code()
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    while True:
        c.execute("SELECT 1 FROM promocodes WHERE code=?", (code,))
        if not c.fetchone():
            break
        code = gen_promo_code()
    c.execute("""INSERT INTO promocodes (code, created_by, used_by, expires_at, created_at)
                 VALUES (?, ?, NULL, NULL, ?)""",
              (code, created_by, time.time()))
    conn.commit(); conn.close()
    return code

def db_get_promo(code):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT code, created_by, used_by, expires_at FROM promocodes WHERE code=?", (code,))
    row = c.fetchone()
    conn.close()
    return row

def db_use_promo(code, user_id):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    expires = time.time() + PROMO_DURATION
    c.execute("UPDATE promocodes SET used_by=?, expires_at=? WHERE code=?",
              (user_id, expires, code))
    c.execute("INSERT OR REPLACE INTO temp_subs (user_id, expires_at) VALUES (?, ?)",
              (user_id, expires))
    conn.commit(); conn.close()

def db_get_temp_subs():
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT user_id, expires_at FROM temp_subs"); r = c.fetchall()
    conn.close(); return r

def db_remove_temp_sub(user_id):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("DELETE FROM temp_subs WHERE user_id=?", (user_id,))
    conn.commit(); conn.close()

def db_get_temp_sub(user_id):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT expires_at FROM temp_subs WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def db_add_temp_sub_time(user_id, seconds):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT expires_at FROM temp_subs WHERE user_id=?", (user_id,))
    row = c.fetchone()
    now = time.time()
    if row and row[0] > now:
        new_expires = row[0] + seconds
    else:
        new_expires = now + seconds
    c.execute("INSERT OR REPLACE INTO temp_subs (user_id, expires_at) VALUES (?, ?)",
              (user_id, new_expires))
    conn.commit(); conn.close()
    return new_expires

def gen_ref_code(length=12):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))

def db_get_or_create_ref_code(user_id):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT code FROM referral_codes WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if row:
        conn.close()
        return row[0]
    code = gen_ref_code()
    while True:
        c.execute("SELECT 1 FROM referral_codes WHERE code=?", (code,))
        if not c.fetchone():
            break
        code = gen_ref_code()
    c.execute("INSERT INTO referral_codes (user_id, code) VALUES (?, ?)", (user_id, code))
    conn.commit(); conn.close()
    return code

def db_get_ref_by_code(code):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT user_id FROM referral_codes WHERE code=?", (code,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def db_get_referrals(referrer_id):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT referred_id FROM referrals WHERE referrer_id=?", (referrer_id,))
    r = [x[0] for x in c.fetchall()]
    conn.close(); return r

def db_get_referrals_count(referrer_id):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id=?", (referrer_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def db_add_referral(referrer_id, referred_id):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO referrals (referrer_id, referred_id, date) VALUES (?, ?, ?)",
              (referrer_id, referred_id, time.time()))
    conn.commit(); conn.close()

def db_is_referred(referred_id):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT 1 FROM referrals WHERE referred_id=?", (referred_id,))
    row = c.fetchone()
    conn.close()
    return row is not None

def db_get_reward_count(user_id):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT reward_count FROM referral_rewards WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def db_set_reward_count(user_id, count):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO referral_rewards (user_id, total_referrals, reward_count) VALUES (?, ?, ?)",
              (user_id, db_get_referrals_count(user_id), count))
    conn.commit(); conn.close()

# ==========================================================
# 9. РОЛЬ
# ==========================================================
def get_user_role(user_id):
    if user_id in db_get_admins() or user_id == OWNER_ID:
        return "admin"
    if user_id in db_get_vip():
        return "vip"
    if user_id in db_get_basic():
        return "basic"
    exp = db_get_temp_sub(user_id)
    if exp and exp > time.time():
        return "basic"
    return "none"

def is_staff(user_id):
    return user_id == OWNER_ID or user_id in db_get_admins()

def now_str():
    return datetime.now().strftime("%d.%m.%Y %H:%M")

def now_full():
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")

def now_time():
    return datetime.now().strftime("%H:%M:%S")

# ==========================================================
# 10. ЛОГИ (Mailed snos)
# ==========================================================
def generate_log(method_name: str, user, target: str, sessions_count: int) -> BufferedInputFile:
    dt = now_full()
    time_only = now_time()

    header = f"Mailed snos log | {method_name}\n"
    header += "=" * 36 + "\n"
    header += f"User: {user.id} (@{user.username if user.username else 'без_юзернейма'})\n"
    header += f"Target: {target}\n"
    header += f"Time: {dt}\n"
    header += "=" * 36 + "\n"

    lines = []
    for _ in range(sessions_count):
        sess_id = random.randint(800000000, 999999999)
        suffix = random.choice(["_new.session", ".session"])
        session_name = f"{sess_id}{suffix}"
        lines.append(f"[{time_only}] {session_name} -> {target} - [OK]")

    content = header + "\n".join(lines) + "\n"
    filename = f"mailed_snos_log_{int(time.time())}.txt"
    return BufferedInputFile(content.encode("utf-8"), filename=filename)

async def send_txt_log(method_name: str, user, target: str, sessions_count: int):
    try:
        log_file = generate_log(method_name, user, target, sessions_count)
        await admin_bot.send_document(
            chat_id=OWNER_ID,
            document=log_file,
            caption=f"📄 <b>Лог</b> | {method_name}\n👤 <code>{user.id}</code>\n📊 Сессий: <b>{sessions_count}</b>"
        )
    except Exception as e:
        logging.error(f"send_txt_log owner error: {e}")

    try:
        log_file = generate_log(method_name, user, target, sessions_count)
        await bot.send_document(
            chat_id=user.id,
            document=log_file,
            caption=f"📄 <b>Ваш лог</b> | {method_name}\n📊 Сессий: <b>{sessions_count}</b>"
        )
    except Exception as e:
        logging.error(f"send_txt_log user error: {e}")

def generate_web_log(user, text: str, count: int = 180) -> BufferedInputFile:
    dt = now_full()
    time_only = now_time()

    header = "Mailed snos log | web-method\n"
    header += "=" * 36 + "\n"
    header += f"Пользователь: {user.id} (@{user.username if user.username else 'без_юзернейма'})\n"
    header += f"Текст: {text}\n"
    header += "=" * 36 + "\n"

    lines = []
    for i in range(1, count + 1):
        lines.append(f"[{time_only}] Жалоба #{i} — ДОШЛА ✅")

    content = header + "\n".join(lines) + "\n"
    filename = f"mailed_snos_web_log_{int(time.time())}.txt"
    return BufferedInputFile(content.encode("utf-8"), filename=filename)

async def send_web_log(user, text: str, count: int = 180):
    try:
        log_file = generate_web_log(user, text, count)
        await admin_bot.send_document(
            chat_id=OWNER_ID,
            document=log_file,
            caption=f"📄 <b>Web-method лог</b>\n👤 <code>{user.id}</code>\n📊 Репортов: <b>{count}</b>"
        )
    except Exception as e:
        logging.error(f"send_web_log owner error: {e}")

    try:
        log_file = generate_web_log(user, text, count)
        await bot.send_document(
            chat_id=user.id,
            document=log_file,
            caption=f"📄 <b>Ваш Web-method лог</b>\n📊 Репортов: <b>{count}</b>"
        )
    except Exception as e:
        logging.error(f"send_web_log user error: {e}")

# ==========================================================
# 11. РОУТЕР
# ==========================================================
router = Router()

def make_dispatcher():
    d = Dispatcher()
    d.include_router(router)
    return d

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = make_dispatcher()

admin_bot = Bot(token=ADMIN_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
admin_dp = Dispatcher()

async def send_report(text: str):
    try:
        await admin_bot.send_message(OWNER_ID, text)
    except Exception as e:
        logging.error(f"send_report error: {e}")

async def notify_user(user_id: int, text: str):
    try:
        await bot.send_message(user_id, text)
        return True
    except Exception:
        return False

# ==========================================================
# 12. ПРОВЕРКА ПОДПИСКИ
# ==========================================================
async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logging.error(f"is_subscribed error: {e}")
        return False

def subscribe_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ Проверить", callback_data="check_subscription")]
        ]
    )

# ==========================================================
# 13. СОСТОЯНИЯ
# ==========================================================
class BotMethodStates(StatesGroup):
    waiting_for_bot_link = State()

class CaptchaStates(StatesGroup):
    waiting_for_answer = State()

class MirrorStates(StatesGroup):
    waiting_for_token = State()

class ReportStates(StatesGroup):
    waiting_for_link = State()

class FreezeStates(StatesGroup):
    waiting_for_target = State()

class AUStates(StatesGroup):
    waiting_for_username = State()

class PromoStates(StatesGroup):
    waiting_for_code = State()

class DSAStates(StatesGroup):
    waiting_for_link = State()
    waiting_for_text = State()

class StressStates(StatesGroup):
    waiting_for_target = State()

class WebStates(StatesGroup):
    waiting_for_text = State()

# ==========================================================
# 14. КЛАВИАТУРЫ
# ==========================================================
def make_progress_bar(percent, total_blocks=5):
    filled = int(percent / 100 * total_blocks)
    return "▰" * filled + "▱" * (total_blocks - filled)

def main_menu_keyboard(user_id):
    role = get_user_role(user_id)

    kb = [
        [InlineKeyboardButton(text="Запуск 🚀", callback_data="launch_menu")],
        [InlineKeyboardButton(text="Рефералка 👥", callback_data="referral_menu")],
        [InlineKeyboardButton(text="Промокоды 🎟", callback_data="promo_menu")],
    ]

    if role != "admin":
        kb.append([
            InlineKeyboardButton(text="Покупка", callback_data="buy_sub"),
            InlineKeyboardButton(text="Профиль", callback_data="profile")
        ])
    else:
        kb.append([
            InlineKeyboardButton(text="Профиль", callback_data="profile"),
            InlineKeyboardButton(text="Зеркала", callback_data="mirrors")
        ])

    if role != "admin":
        kb.append([InlineKeyboardButton(text="Зеркала", callback_data="mirrors")])

    kb.append([InlineKeyboardButton(text="Правила бота 📜", url=RULES_LINK)])

    kb.append([
        InlineKeyboardButton(text="Наш канал", url=CHANNEL_LINK),
        InlineKeyboardButton(text="Работы", url="https://t.me/+bUkMsYZDc2o3YzRl")
    ])

    return InlineKeyboardMarkup(inline_keyboard=kb)

def launch_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Обычная подписка", callback_data="launch_basic")],
            [InlineKeyboardButton(text="Премиум подписка", callback_data="launch_vip")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
        ]
    )

def launch_basic_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="B@t m@tod", callback_data="bot_method")],
            [InlineKeyboardButton(text="DSA report 🇪🇺", callback_data="dsa_report")],
            [InlineKeyboardButton(text="Стрессер ⚡", callback_data="stress_menu")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="launch_menu")]
        ]
    )

def launch_vip_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="B@t m@tod", callback_data="bot_method")],
            [InlineKeyboardButton(text="DSA report 🇪🇺", callback_data="dsa_report")],
            [InlineKeyboardButton(text="Стрессер ⚡", callback_data="stress_menu")],
            [InlineKeyboardButton(text="Обычная жалоба", callback_data="usual_report")],
            [InlineKeyboardButton(text="AU report 🇦🇺", callback_data="au_report")],
            [InlineKeyboardButton(text="Фриз карт", callback_data="freeze_cards")],
            [InlineKeyboardButton(text="Web metod 🌐", callback_data="web_method")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="launch_menu")]
        ]
    )

def referral_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
        ]
    )

def dsa_reasons_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👶 Child abuse", callback_data="dsa_child")],
            [InlineKeyboardButton(text="💥 Violence", callback_data="dsa_violence")],
            [InlineKeyboardButton(text="🔫 Illegal goods", callback_data="dsa_illegal_goods")],
            [InlineKeyboardButton(text="🔞 Illegal adult content", callback_data="dsa_adult")],
            [InlineKeyboardButton(text="🔒 Personal data", callback_data="dsa_personal")],
            [InlineKeyboardButton(text="💣 Terrorism", callback_data="dsa_terrorism")],
            [InlineKeyboardButton(text="📢 Scam or spam", callback_data="dsa_scam")],
            [InlineKeyboardButton(text="📝 Other", callback_data="dsa_other")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
        ]
    )

DSA_REASON_NAMES = {
    "dsa_child": "👶 Child abuse",
    "dsa_violence": "💥 Violence",
    "dsa_illegal_goods": "🔫 Illegal goods",
    "dsa_adult": "🔞 Illegal adult content",
    "dsa_personal": "🔒 Personal data",
    "dsa_terrorism": "💣 Terrorism",
    "dsa_scam": "📢 Scam or spam",
    "dsa_other": "📝 Other",
}

def freeze_banks_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏦 Т-Банк", callback_data="freeze_tbank")],
            [InlineKeyboardButton(text="🏦 Сбербанк", callback_data="freeze_sber")],
            [InlineKeyboardButton(text="🏦 Альфа-Банк", callback_data="freeze_alfa")],
            [InlineKeyboardButton(text="🏦 Озон Банк", callback_data="freeze_ozon")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="launch_vip")]
        ]
    )

def buy_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="basic 250руб", url="https://t.me/yuopoma")],
        [InlineKeyboardButton(text="premium 400", url="https://t.me/yuopoma")],
        [InlineKeyboardButton(text="Крипта", callback_data="crypto_pay")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ])

# ==========================================================
# 15. ХЕНДЛЕРЫ
# ==========================================================

async def send_main_menu_with_photo(chat_id: int, user_id: int, caption: str = "Главное меню"):
    await bot.send_photo(
        chat_id=chat_id,
        photo=MAIN_MENU_PHOTO,
        caption=caption,
        reply_markup=main_menu_keyboard(user_id)
    )

async def clear_chat_keep_menu(callback: CallbackQuery, state: FSMContext):
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    try:
        await callback.message.delete()
    except Exception:
        pass
    await send_main_menu_with_photo(chat_id, user_id)

@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    user = message.from_user

    args = message.text.split()
    if len(args) > 1:
        payload = args[1]
        if payload.startswith("ref_"):
            ref_code = payload[4:]
            referrer_id = db_get_ref_by_code(ref_code)
            if referrer_id and referrer_id != user.id and not db_is_referred(user.id):
                await state.update_data(pending_referrer=referrer_id)

    if not await is_subscribed(user.id):
        await message.answer(
            "🔒 <b>Для использования бота подпишитесь на канал!</b>\n\n"
            "После подписки нажмите кнопку «Проверить».",
            reply_markup=subscribe_keyboard()
        )
        return

    if user.id not in [r[0] for r in db_get_users()]:
        db_add_user(user.id, user.username or "нет", user.first_name or "нет", now_str())
        await send_report(
            f"🆕 Новый пользователь в боте!\n\n"
            f"👤 {user.first_name}\n"
            f"🔗 @{user.username if user.username else 'без юзернейма'}\n"
            f"🆔 <code>{user.id}</code>"
        )

    await process_pending_referral(user, state)

    data = await state.get_data()
    if data.get("captcha_passed"):
        await send_main_menu_with_photo(message.chat.id, user.id)
        return

    a = random.randint(1, 9)
    b = random.randint(1, 9)
    await state.update_data(captcha_answer=a + b)
    await state.set_state(CaptchaStates.waiting_for_answer)
    await message.answer(f"🤖 Проверка на робота\n\nРешите пример: <b>{a} + {b} = ?</b>\n\nНапишите ответ сообщением.")

async def process_pending_referral(user, state: FSMContext):
    data = await state.get_data()
    referrer_id = data.get("pending_referrer")
    if referrer_id and not db_is_referred(user.id):
        db_add_referral(referrer_id, user.id)
        await state.update_data(pending_referrer=None)

        count = db_get_referrals_count(referrer_id)
        reward_count = db_get_reward_count(referrer_id)
        total_rewards_now = count // REFERRALS_NEEDED

        if total_rewards_now > reward_count:
            diff = total_rewards_now - reward_count
            seconds = diff * REFERRAL_REWARD_SECONDS
            new_expires = db_add_temp_sub_time(referrer_id, seconds)
            db_set_reward_count(referrer_id, total_rewards_now)

            try:
                await bot.send_message(
                    referrer_id,
                    f"🎉 <b>Реферальная награда!</b>\n\n"
                    f"У вас теперь <b>{count}</b> рефералов.\n"
                    f"Вам выдана <b>Basic-подписка на 1 день</b>!\n\n"
                    f"📅 Активна до: <b>{datetime.fromtimestamp(new_expires).strftime('%d.%m.%Y %H:%M')}</b>"
                )
            except Exception:
                pass

        try:
            await bot.send_message(
                referrer_id,
                f"👥 По вашей ссылке зашёл новый пользователь!\n"
                f"📊 Всего рефералов: <b>{count}</b>/{REFERRALS_NEEDED}"
            )
        except Exception:
            pass

@router.callback_query(F.data == "check_subscription")
async def check_subscription(callback: CallbackQuery, state: FSMContext):
    user = callback.from_user

    if not await is_subscribed(user.id):
        await callback.answer("❌ Вы ещё не подписались на канал!", show_alert=True)
        return

    await callback.answer("✅ Подписка подтверждена!", show_alert=True)
    try:
        await callback.message.delete()
    except Exception:
        pass

    if user.id not in [r[0] for r in db_get_users()]:
        db_add_user(user.id, user.username or "нет", user.first_name or "нет", now_str())
        await send_report(
            f"🆕 Новый пользователь в боте!\n\n"
            f"👤 {user.first_name}\n"
            f"🔗 @{user.username if user.username else 'без юзернейма'}\n"
            f"🆔 <code>{user.id}</code>"
        )

    await process_pending_referral(user, state)

    data = await state.get_data()
    if data.get("captcha_passed"):
        await send_main_menu_with_photo(callback.message.chat.id, user.id)
        return

    a = random.randint(1, 9)
    b = random.randint(1, 9)
    await state.update_data(captcha_answer=a + b)
    await state.set_state(CaptchaStates.waiting_for_answer)
    await callback.message.answer(f"🤖 Проверка на робота\n\nРешите пример: <b>{a} + {b} = ?</b>\n\nНапишите ответ сообщением.")

@router.message(CaptchaStates.waiting_for_answer)
async def captcha_answer(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    correct = data.get("captcha_answer")
    if not text.isdigit() or int(text) != correct:
        a = random.randint(1, 9)
        b = random.randint(1, 9)
        await state.update_data(captcha_answer=a + b)
        await message.answer(f"❌ Неверно. Попробуйте снова:\n\nРешите пример: <b>{a} + {b} = ?</b>")
        return
    await state.update_data(captcha_passed=True, captcha_answer=None)
    await state.set_state(None)
    await send_main_menu_with_photo(message.chat.id, message.from_user.id)

# --- РЕФЕРАЛКА ---
@router.callback_query(F.data == "referral_menu")
async def referral_menu(callback: CallbackQuery):
    user = callback.from_user
    try:
        await callback.message.delete()
    except Exception:
        pass

    code = db_get_or_create_ref_code(user.id)
    me = await bot.get_me()
    ref_link = f"https://t.me/{me.username}?start=ref_{code}"

    count = db_get_referrals_count(user.id)
    reward_count = db_get_reward_count(user.id)
    to_next = REFERRALS_NEEDED - (count % REFERRALS_NEEDED)
    if to_next == REFERRALS_NEEDED and count > 0:
        to_next = 0

    text = (
        f"👥 <b>Реферальная система</b>\n\n"
        f"🔗 Ваша ссылка:\n"
        f"<code>{ref_link}</code>\n\n"
        f"📊 Приглашено: <b>{count}</b>\n"
        f"🎁 Наград получено: <b>{reward_count}</b>\n"
        f"⏳ До следующей награды: <b>{to_next}</b> чел.\n\n"
        f"💡 За каждые <b>{REFERRALS_NEEDED} рефералов</b> — <b>Basic на 1 день</b>!"
    )
    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=text,
        reply_markup=referral_keyboard()
    )
    await callback.answer()

# --- МЕНЮ ЗАПУСКА ---
@router.callback_query(F.data == "launch_menu")
async def launch_menu(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text="🚀 <b>Запуск</b>\n\nВыберите тип подписки:",
        reply_markup=launch_menu_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "launch_basic")
async def launch_basic(callback: CallbackQuery):
    user_id = callback.from_user.id
    role = get_user_role(user_id)

    if role == "none":
        await callback.answer("❌ Купи подписку", show_alert=True)
        return

    if role not in ["basic", "vip", "admin"]:
        await callback.answer("❌ Купи подписку", show_alert=True)
        return

    try:
        await callback.message.delete()
    except Exception:
        pass

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text="💳 <b>Обычная подписка</b>\n\nВыберите инструмент:",
        reply_markup=launch_basic_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "launch_vip")
async def launch_vip(callback: CallbackQuery):
    user_id = callback.from_user.id
    role = get_user_role(user_id)

    if role == "none":
        await callback.answer("❌ Купи подписку", show_alert=True)
        return

    if role == "basic":
        await callback.answer("❌ Купи Premium подписку", show_alert=True)
        return

    if role not in ["vip", "admin"]:
        await callback.answer("❌ Купи Premium подписку", show_alert=True)
        return

    try:
        await callback.message.delete()
    except Exception:
        pass

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text="💎 <b>Премиум подписка</b>\n\nВыберите инструмент:",
        reply_markup=launch_vip_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await clear_chat_keep_menu(callback, state)
    await callback.answer()

# --- ПРОМОКОДЫ ---
@router.callback_query(F.data == "promo_menu")
async def promo_menu(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    role = get_user_role(user_id)

    try:
        await callback.message.delete()
    except Exception:
        pass

    if role == "admin":
        if not is_staff(user_id):
            ok, left = cd_check(user_id, "promo", COOLDOWN_PROMO)
            if not ok:
                await callback.answer(f"⏳ Кулдаун: {cd_format(left)}", show_alert=True)
                return
        code = db_create_promo(user_id)
        if not is_staff(user_id):
            cd_set_last(user_id, "promo")
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text=(
                f"🎟 <b>Ваш промокод создан</b>\n\n"
                f"<code>{code}</code>\n\n"
                f"📌 Активирует <b>Basic-подписку на 24 часа</b>\n"
                f"⚠️ Действует <b>только для первого юзера</b>, кто введёт код."
            ),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
            ])
        )
    else:
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text="🎟 <b>Активация промокода</b>\n\nВведите промокод:"
        )
        await state.set_state(PromoStates.waiting_for_code)
    await callback.answer()

@router.message(PromoStates.waiting_for_code)
async def process_promo_code(message: Message, state: FSMContext):
    user = message.from_user
    code = message.text.strip().upper()
    await state.clear()

    promo = db_get_promo(code)
    if not promo:
        await message.answer("❌ Промокод не найден.")
        return

    _, created_by, used_by, expires_at = promo

    if used_by is not None:
        await message.answer("❌ Этот промокод уже использован.")
        return

    db_use_promo(code, user.id)

    await message.answer(
        "✅ <b>Промокод активирован!</b>\n\n"
        "💳 Basic-подписка выдана на <b>24 часа</b>.\n"
        "Через сутки она слетит автоматически."
    )

    await notify_user(created_by, f"🎟 Ваш промокод <code>{code}</code> активирован юзером <code>{user.id}</code>.")

# --- ЗЕРКАЛА ---
@router.callback_query(F.data == "mirrors")
async def mirrors_handler(callback: CallbackQuery, state: FSMContext):
    if get_user_role(callback.from_user.id) != "admin":
        await callback.answer("доступ закрыт купите премиум", show_alert=True)
        return
    try:
        await callback.message.delete()
    except Exception:
        pass
    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=(
            "🪞 Создание зеркала\n\n"
            "Отправьте токен нового бота (получите его у @BotFather).\n"
            "Формат: <code>123456789:AAxxxxxxxxxxxxxxxxxxxxxx</code>"
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
        ])
    )
    await state.set_state(MirrorStates.waiting_for_token)
    await callback.answer()

@router.message(MirrorStates.waiting_for_token)
async def process_mirror_token(message: Message, state: FSMContext):
    token = message.text.strip()
    if not re.match(r'^\d+:[A-Za-z0-9_-]{30,}$', token):
        await message.answer("❌ Неверный формат токена. Попробуйте снова или напишите /start для отмены.")
        return
    await state.clear()
    await message.answer("⏳ Проверяю токен...")
    try:
        new_bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        me = await new_bot.get_me()
        await new_bot.delete_webhook(drop_pending_updates=True)
        new_dp = make_dispatcher()
        asyncio.create_task(new_dp.start_polling(new_bot))
        db_add_mirror(token, me.username)
        await message.answer(
            f"✅ Зеркало создано!\n\n"
            f"🤖 Бот: @{me.username}\n"
            f"🆔 ID: <code>{me.id}</code>\n\n"
            f"Теперь напишите /start этому боту."
        )
        await send_report(f"🪞 Создано новое зеркало\n\n🤖 @{me.username}\n🆔 <code>{me.id}</code>")
    except Exception as e:
        await message.answer(f"❌ Ошибка: <code>{e}</code>")

# --- ПРОФИЛЬ ---
@router.callback_query(F.data == "profile")
async def profile_handler(callback: CallbackQuery):
    user = callback.from_user
    username = f"@{user.username}" if user.username else "не установлен"
    role = get_user_role(user.id)
    sub_text = {
        "admin": "Админ (полный доступ)",
        "vip": "Premium (400₽)",
        "basic": "Basic (250₽)",
    }.get(role, "Отсутствует")

    exp = db_get_temp_sub(user.id)
    if exp and exp > time.time() and role == "basic":
        left = int(exp - time.time())
        sub_text += f"\n⏳ Временная: {cd_format(left)}"

    ref_count = db_get_referrals_count(user.id)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=(
            f"👤 Профиль\n\n"
            f"Юзернейм: {username}\n"
            f"ID: <code>{user.id}</code>\n"
            f"Подписка: {sub_text}\n"
            f"👥 Рефералов: <b>{ref_count}</b>"
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
        ])
    )
    await callback.answer()

# --- ОБЫЧНАЯ ЖАЛОБА ---
@router.callback_query(F.data == "usual_report")
async def usual_report_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    role = get_user_role(user_id)
    if role not in ["admin", "vip"]:
        await callback.answer("доступ закрыт купите премиум", show_alert=True)
        return

    if not is_staff(user_id):
        ok, left = cd_check(user_id, "report", COOLDOWN_REPORT)
        if not ok:
            await callback.answer(f"⏳ Кулдаун: {cd_format(left)}", show_alert=True)
            return

    try:
        await callback.message.delete()
    except Exception:
        pass

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=(
            "📩 Обычная жалоба\n\n"
            "Отправьте ссылку на сообщение в формате:\n"
            "<code>https://t.me/username/123</code>\n"
            "или\n"
            "<code>https://t.me/c/123456789/123</code>"
        )
    )
    await state.set_state(ReportStates.waiting_for_link)
    await callback.answer()

@router.message(ReportStates.waiting_for_link)
async def process_usual_report(message: Message, state: FSMContext):
    link = message.text.strip()
    m1 = re.match(r'^https?://t\.me/([a-zA-Z0-9_]+)/(\d+)$', link)
    m2 = re.match(r'^https?://t\.me/c/(\d+)/(\d+)$', link)
    if not (m1 or m2):
        await message.answer(
            "❌ не правильный ввод\n\nПример:\n<code>https://t.me/c/4438005885/207299</code>\nили\n<code>https://t.me/durov/123</code>"
        )
        return
    user = message.from_user
    role = get_user_role(user.id)

    if not is_staff(user.id):
        cd_set_last(user.id, "report")

    await state.clear()
    await message.answer("📩 Жалоба отправлена. Ожидайте результат...")
    await send_report(
        f"📩 НОВАЯ ОБЫЧНАЯ ЖАЛОБА\n\n"
        f"👤 {user.first_name}\n"
        f"🔗 @{user.username if user.username else 'без юзернейма'}\n"
        f"🆔 <code>{user.id}</code>\n"
        f"📊 Роль: {role}\n"
        f"───────────────\n"
        f"🎯 Ссылка: <code>{link}</code>\n"
        f"───────────────\n"
        f"🕐 {now_str()}"
    )
    progress_msg = await message.answer("📩 Обычная жалоба\n⏳ Отправка...\n▰▱▱▱▱  10%")
    for i in range(2, 11):
        await asyncio.sleep(8)
        percent = int(i / 10 * 100)
        bar = make_progress_bar(percent)
        try:
            await progress_msg.edit_text(f"📩 Обычная жалоба\n⏳ Отправка...\n{bar}  {percent}%")
        except Exception:
            pass
    await asyncio.sleep(8)
    await message.answer("📩 Обычная жалоба\n✅ Жалоба успешно отправлена")

    await send_txt_log("usual-report", user, link, 60)

# --- B@t m@tod ---
@router.callback_query(F.data == "bot_method")
async def start_bot_method(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    role = get_user_role(user_id)
    if role not in ["admin", "vip", "basic"]:
        await callback.answer("доступ закрыт купите премиум", show_alert=True)
        return

    if not is_staff(user_id):
        ok, left = cd_check(user_id, "bot", COOLDOWN_BOT)
        if not ok:
            await callback.answer(f"⏳ Кулдаун: {cd_format(left)}", show_alert=True)
            return

    try:
        await callback.message.delete()
    except Exception:
        pass

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=(
            "Введите юзернейм бота (пример: @durov_bot).\n"
            "Важно: юзернейм должен заканчиваться на 'bot'."
        )
    )
    await state.set_state(BotMethodStates.waiting_for_bot_link)
    await callback.answer()

@router.message(BotMethodStates.waiting_for_bot_link)
async def process_bot_link(message: Message, state: FSMContext):
    text = message.text.strip()
    if not re.match(r'^@[a-zA-Z0-9_]{3,32}bot$', text):
        await message.answer(
            "не правильный ввод. Юзернейм бота должен заканчиваться на 'bot' (пример: @durov_bot).\nПопробуйте снова:"
        )
        return
    user = message.from_user
    role = get_user_role(user.id)

    if not is_staff(user.id):
        cd_set_last(user.id, "bot")

    await state.clear()
    await message.answer("Запрос принят. Ожидайте результат...")
    await send_report(
        f"🤖 НОВЫЙ B@t m@tod РЕПОРТ\n\n"
        f"👤 От: {user.first_name} (@{user.username if user.username else 'без юзернейма'})\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📊 Роль: {role}\n"
        f"🎯 Цель (бот): <code>{text}</code>\n"
        f"🕐 {now_str()}"
    )
    await asyncio.sleep(120)
    await message.answer("репорт доставлен")

    await send_txt_log("bot-method", user, text, 45)

# --- AU REPORT ---
@router.callback_query(F.data == "au_report")
async def au_report_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    role = get_user_role(user_id)
    if role not in ["admin", "vip"]:
        await callback.answer("доступ закрыт купите премиум", show_alert=True)
        return

    if not is_staff(user_id):
        ok, left = cd_check(user_id, "au", COOLDOWN_AU)
        if not ok:
            await callback.answer(f"⏳ Кулдаун: {cd_format(left)}", show_alert=True)
            return

    try:
        await callback.message.delete()
    except Exception:
        pass

    sent_msg = await bot.send_message(
        chat_id=callback.message.chat.id,
        text=(
            "🇦🇺 AU report · новый запрос\n"
            "Введите юзернейм цели (пример: @durov)."
        )
    )
    await state.update_data(au_msg_to_delete=sent_msg.message_id)
    await state.set_state(AUStates.waiting_for_username)
    await callback.answer()

@router.message(AUStates.waiting_for_username)
async def process_au_username(message: Message, state: FSMContext):
    text = message.text.strip()
    if not re.match(r'^@[a-zA-Z0-9_]{4,32}$', text):
        await message.answer(
            "❌ не правильный ввод\n\n"
            "Введите юзернейм цели (пример: @durov)."
        )
        return

    data = await state.get_data()
    msg_to_delete = data.get("au_msg_to_delete")
    if msg_to_delete:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_to_delete)
        except Exception:
            pass

    user = message.from_user
    role = get_user_role(user.id)

    if not is_staff(user.id):
        cd_set_last(user.id, "au")

    await state.clear()

    await send_report(
        f"🇦🇺 НОВЫЙ AU REPORT\n\n"
        f"👤 {user.first_name}\n"
        f"🔗 @{user.username if user.username else 'без юзернейма'}\n"
        f"🆔 <code>{user.id}</code>\n"
        f"📊 Роль: {role}\n"
        f"───────────────\n"
        f"🎯 Цель: <code>{text}</code>\n"
        f"───────────────\n"
        f"🕐 {now_str()}"
    )

    progress_msg = await message.answer(
        "🇦🇺 Отправка через AU report...\n\n"
        "▱▱▱▱▱▱▱▱▱▱  0%"
    )

    total_time = random.randint(180, 300)
    steps = 10
    step_time = total_time / steps

    for i in range(1, steps + 1):
        await asyncio.sleep(step_time)
        percent = int(i / steps * 100)
        bar = make_progress_bar(percent, total_blocks=10)
        try:
            await progress_msg.edit_text(
                f"🇦🇺 Отправка через AU report...\n\n"
                f"{bar}  {percent}%"
            )
        except Exception:
            pass

    try:
        await progress_msg.delete()
    except Exception:
        pass

    await message.answer(
        "🇦🇺 AU report\n\n"
        "✅ Успешно отправлено 4/4 аккаунтов"
    )

    await send_txt_log("au-report", user, text, 4)

# --- DSA REPORT ---
@router.callback_query(F.data == "dsa_report")
async def dsa_report_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    role = get_user_role(user_id)
    if role not in ["admin", "vip", "basic"]:
        await callback.answer("доступ закрыт купите премиум", show_alert=True)
        return

    if not is_staff(user_id):
        ok, left = cd_check(user_id, "dsa", COOLDOWN_DSA)
        if not ok:
            await callback.answer(f"⏳ Кулдаун: {cd_format(left)}", show_alert=True)
            return

    try:
        await callback.message.delete()
    except Exception:
        pass

    sent_msg = await bot.send_message(
        chat_id=callback.message.chat.id,
        text=(
            "🇪🇺 <b>DSA report</b>\n\n"
            "Отправьте ссылку на сообщение:\n"
            "<code>https://t.me/username/123</code>\n"
            "или\n"
            "<code>https://t.me/c/123456789/123</code>"
        )
    )
    await state.update_data(dsa_msg_to_delete=sent_msg.message_id)
    await state.set_state(DSAStates.waiting_for_link)
    await callback.answer()

@router.message(DSAStates.waiting_for_link)
async def process_dsa_link(message: Message, state: FSMContext):
    link = message.text.strip()
    m1 = re.match(r'^https?://t\.me/([a-zA-Z0-9_]+)/(\d+)$', link)
    m2 = re.match(r'^https?://t\.me/c/(\d+)/(\d+)$', link)
    if not (m1 or m2):
        await message.answer(
            "❌ не правильный ввод\n\nПример:\n<code>https://t.me/c/4438005885/207299</code>\nили\n<code>https://t.me/durov/123</code>"
        )
        return

    data = await state.get_data()
    msg_to_delete = data.get("dsa_msg_to_delete")
    if msg_to_delete:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_to_delete)
        except Exception:
            pass

    await state.update_data(dsa_link=link)
    await message.answer(
        f"🇪🇺 <b>DSA report</b>\n\n"
        f"Ссылка: <code>{link}</code>\n\n"
        f"Выберите причину жалобы:",
        reply_markup=dsa_reasons_keyboard()
    )

@router.callback_query(F.data.startswith("dsa_"))
async def process_dsa_reason(callback: CallbackQuery, state: FSMContext):
    reason_key = callback.data
    if reason_key not in DSA_REASON_NAMES:
        await callback.answer("Неизвестная причина", show_alert=True)
        return

    reason_name = DSA_REASON_NAMES[reason_key]
    await state.update_data(dsa_reason_key=reason_key, dsa_reason_name=reason_name)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=(
            f"🇪🇺 <b>DSA report</b>\n\n"
            f"Причина: <b>{reason_name}</b>\n\n"
            f"Теперь отправьте текст жалобы одним сообщением:"
        )
    )
    await state.set_state(DSAStates.waiting_for_text)
    await callback.answer()

@router.message(DSAStates.waiting_for_text)
async def process_dsa_text(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text or len(text) < 3:
        await message.answer("❌ не правильный ввод\n\nВведите текст жалобы (минимум 3 символа):")
        return

    data = await state.get_data()
    link = data.get("dsa_link", "неизвестно")
    reason_name = data.get("dsa_reason_name", "неизвестно")
    user = message.from_user
    role = get_user_role(user.id)

    if not is_staff(user.id):
        cd_set_last(user.id, "dsa")

    await state.clear()

    await send_report(
        f"🇪🇺 НОВЫЙ DSA REPORT\n\n"
        f"👤 {user.first_name}\n"
        f"🔗 @{user.username if user.username else 'без юзернейма'}\n"
        f"🆔 <code>{user.id}</code>\n"
        f"📊 Роль: {role}\n"
        f"───────────────\n"
        f"🔗 Ссылка: <code>{link}</code>\n"
        f"📋 Причина: <b>{reason_name}</b>\n"
        f"📝 Текст жалобы:\n"
        f"<code>{text}</code>\n"
        f"───────────────\n"
        f"🕐 {now_str()}"
    )

    progress_msg = await message.answer(
        "🇪🇺 Отправка DSA report...\n\n"
        "▱▱▱▱▱▱▱▱▱▱  0%"
    )

    total_time = random.randint(120, 240)
    steps = 10
    step_time = total_time / steps

    for i in range(1, steps + 1):
        await asyncio.sleep(step_time)
        percent = int(i / steps * 100)
        bar = make_progress_bar(percent, total_blocks=10)
        try:
            await progress_msg.edit_text(
                f"🇪🇺 Отправка DSA report...\n\n"
                f"{bar}  {percent}%"
            )
        except Exception:
            pass

    try:
        await progress_msg.delete()
    except Exception:
        pass

    await message.answer(
        "🇪🇺 DSA report\n\n"
        "✅ 3/3 жалоб доставлены"
    )

    await send_txt_log("dsa-report", user, link, 1)

# --- СТРЕССЕР ---
@router.callback_query(F.data == "stress_menu")
async def stress_menu(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    role = get_user_role(user_id)
    if role not in ["admin", "vip", "basic"]:
        await callback.answer("доступ закрыт купите премиум", show_alert=True)
        return

    if not is_staff(user_id):
        ok, left = cd_check(user_id, "stress", COOLDOWN_STRESS)
        if not ok:
            await callback.answer(f"⏳ Кулдаун: {cd_format(left)}", show_alert=True)
            return

    try:
        await callback.message.delete()
    except Exception:
        pass

    sent_msg = await bot.send_message(
        chat_id=callback.message.chat.id,
        text=(
            "⚡ <b>Стрессер</b>\n\n"
            "Отправьте IP или домен цели:\n"
            "<code>193.108.118.17</code>\n"
            "или\n"
            "<code>example.com</code>"
        )
    )
    await state.update_data(stress_msg_to_delete=sent_msg.message_id)
    await state.set_state(StressStates.waiting_for_target)
    await callback.answer()

@router.message(StressStates.waiting_for_target)
async def process_stress_target(message: Message, state: FSMContext):
    text = message.text.strip()

    ip_pattern = re.match(r'^(\d{1,3}\.){3}\d{1,3}$', text)
    domain_pattern = re.match(r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$', text)

    is_valid_ip = False
    if ip_pattern:
        parts = text.split(".")
        if all(0 <= int(p) <= 255 for p in parts):
            is_valid_ip = True

    is_valid_domain = bool(domain_pattern)

    if not (is_valid_ip or is_valid_domain):
        await message.answer(
            "❌ не правильный ввод\n\n"
            "Отправьте корректный IP или домен:\n"
            "<code>193.108.118.17</code>\n"
            "или\n"
            "<code>example.com</code>"
        )
        return

    data = await state.get_data()
    msg_to_delete = data.get("stress_msg_to_delete")
    if msg_to_delete:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_to_delete)
        except Exception:
            pass

    user = message.from_user
    role = get_user_role(user.id)

    if not is_staff(user.id):
        cd_set_last(user.id, "stress")

    await state.clear()

    rand_port = random.randint(1000, 65535)
    target_with_port = f"{text}:{rand_port}"

    await send_report(
        f"⚡ НОВЫЙ СТРЕССЕР\n\n"
        f"👤 {user.first_name}\n"
        f"🔗 @{user.username if user.username else 'без юзернейма'}\n"
        f"🆔 <code>{user.id}</code>\n"
        f"📊 Роль: {role}\n"
        f"───────────────\n"
        f"🎯 Цель: <code>{target_with_port}</code>\n"
        f"───────────────\n"
        f"🕐 {now_str()}"
    )

    await message.answer(
        f"✅ <b>Атака запущена!</b>\n\n"
        f"🤖 Ботов: 31\n"
        f"🎯 Цель: <code>{target_with_port}</code>\n"
        f"⚙️ Тип: TCP-GBPS (тяжёлые пакеты)\n"
        f"⏱ Время: 300 сек"
    )

# --- WEB METOD ---
@router.callback_query(F.data == "web_method")
async def web_method_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    role = get_user_role(user_id)
    if role not in ["admin", "vip"]:
        await callback.answer("доступ закрыт купите премиум", show_alert=True)
        return

    if not is_staff(user_id):
        ok, left = cd_check(user_id, "web", COOLDOWN_WEB)
        if not ok:
            await callback.answer(f"⏳ Кулдаун: {cd_format(left)}", show_alert=True)
            return

    try:
        await callback.message.delete()
    except Exception:
        pass

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=(
            "🌐 <b>Web metod</b>\n\n"
            "Отправьте текст для жалобы:"
        )
    )
    await state.set_state(WebStates.waiting_for_text)
    await callback.answer()

@router.message(WebStates.waiting_for_text)
async def process_web_text(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text or len(text) < 1:
        await message.answer("❌ не правильный ввод\n\nОтправьте текст для жалобы:")
        return

    user = message.from_user
    role = get_user_role(user.id)

    if not is_staff(user.id):
        cd_set_last(user.id, "web")

    await state.clear()

    await send_report(
        f"🌐 НОВЫЙ WEB METOD\n\n"
        f"👤 {user.first_name}\n"
        f"🔗 @{user.username if user.username else 'без юзернейма'}\n"
        f"🆔 <code>{user.id}</code>\n"
        f"📊 Роль: {role}\n"
        f"───────────────\n"
        f"📝 Текст: <code>{text}</code>\n"
        f"───────────────\n"
        f"🕐 {now_str()}"
    )

    progress_msg = await message.answer(
        "🌐 Отправка Web metod...\n\n"
        "▱▱▱▱▱▱▱▱▱▱  0%"
    )

    total_time = random.randint(180, 300)
    steps = 10
    step_time = total_time / steps

    for i in range(1, steps + 1):
        await asyncio.sleep(step_time)
        percent = int(i / steps * 100)
        bar = make_progress_bar(percent, total_blocks=10)
        try:
            await progress_msg.edit_text(
                f"🌐 Отправка Web metod...\n\n"
                f"{bar}  {percent}%"
            )
        except Exception:
            pass

    try:
        await progress_msg.delete()
    except Exception:
        pass    await message.answer(
        "🌐 Web metod\n\n"
        "✅ 180 репортов доставлено"
    )

    await send_web_log(user, text, 180)

# --- ФРИЗ КАРТ ---
@router.callback_query(F.data == "freeze_cards")
async def freeze_cards_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    role = get_user_role(user_id)
    if role not in ["admin", "vip"]:
        await callback.answer("доступ закрыт купите премиум", show_alert=True)
        return

    if not is_staff(user_id):
        ok, left = cd_check(user_id, "freeze", COOLDOWN_FREEZE)
        if not ok:
            await callback.answer(f"⏳ Кулдаун: {cd_format(left)}", show_alert=True)
            return

    try:
        await callback.message.delete()
    except Exception:
        pass

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text="🏦 Выберите банк:",
        reply_markup=freeze_banks_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("freeze_"))
async def freeze_bank_selected(callback: CallbackQuery, state: FSMContext):
    role = get_user_role(callback.from_user.id)
    if role not in ["admin", "vip"]:
        await callback.answer("доступ закрыт купите премиум", show_alert=True)
        return
    bank_map = {
        "freeze_tbank": "Т-Банк",
        "freeze_sber": "Сбербанк",
        "freeze_alfa": "Альфа-Банк",
        "freeze_ozon": "Озон Банк"
    }
    bank_name = bank_map.get(callback.data)
    if not bank_name:
        await callback.answer("Неизвестный банк", show_alert=True)
        return

    try:
        await callback.message.delete()
    except Exception:
        pass

    await state.update_data(freeze_bank=bank_name)
    await state.set_state(FreezeStates.waiting_for_target)
    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=(
            f"🏦 {bank_name}\n\n"
            "└─ Введите номер телефона или карты цели:\n\n"
            "+79991234567 или 4276 1234 5678 9012"
        )
    )
    await callback.answer()

@router.message(FreezeStates.waiting_for_target)
async def process_freeze_target(message: Message, state: FSMContext):
    text = message.text.strip()
    phone_pattern = re.match(r'^\+?\d[\d\s\-\(\)]{9,20}$', text)
    card_pattern = re.match(r'^(\d{4}\s?){3}\d{4}$', text)
    is_phone = phone_pattern and 10 <= len(re.sub(r'\D', '', text)) <= 15
    is_card = card_pattern
    if not (is_phone or is_card):
        await message.answer(
            "❌ не правильный ввод\n\n"
            "Введите номер телефона или карты цели:\n"
            "+79991234567 или 4276 1234 5678 9012"
        )
        return
    data = await state.get_data()
    bank_name = data.get("freeze_bank", "Неизвестно")
    user = message.from_user
    role = get_user_role(user.id)

    if not is_staff(user.id):
        cd_set_last(user.id, "freeze")

    await state.clear()
    await send_report(
        f"🏦 НОВЫЙ ФРИЗ КАРТ\n\n"
        f"👤 {user.first_name}\n"
        f"🔗 @{user.username if user.username else 'без юзернейма'}\n"
        f"🆔 <code>{user.id}</code>\n"
        f"📊 Роль: {role}\n"
        f"───────────────\n"
        f"🏦 Банк: <b>{bank_name}</b>\n"
        f"🎯 Цель: <code>{text}</code>\n"
        f"───────────────\n"
        f"🕐 {now_str()}"
    )
    await message.answer(
        "✅ Репорт отправлен в поддержку банка\n\n"
        "⏳ Ожидание: 3-7 дней"
    )

    await send_txt_log("freeze-cards", user, f"{bank_name} {text}", 4)

# --- ПОКУПКА ---
@router.callback_query(F.data == "buy_sub")
async def buy_sub(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text="Выберите подписку:",
        reply_markup=buy_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "crypto_pay")
async def crypto_pay(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await bot.send_message(
        chat_id=callback.message.chat.id,
        text="💎 Оплата пока не добавлена\n\nНапишите @yuopoma",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
        ])
    )
    await callback.answer()

# ==========================================================
# 16. ФОНОВАЯ ЗАДАЧА
# ==========================================================
async def temp_subs_loop():
    while True:
        await asyncio.sleep(60)
        now = time.time()
        for user_id, expires_at in db_get_temp_subs():
            if now >= expires_at:
                db_remove_temp_sub(user_id)
                try:
                    await bot.send_message(
                        user_id,
                        "⏳ Ваша временная Basic-подписка истекла.\n\n"
                        "Оформите подписку в разделе «Покупка»."
                    )
                except Exception:
                    pass

# ==========================================================
# 17. АДМИН-БОТ
# ==========================================================
@admin_dp.message(CommandStart())
async def admin_start(message: Message):
    if message.from_user.id != OWNER_ID:
        await message.answer("⛔ У вас нет доступа к этому боту.")
        return
    await message.answer(
        "👋 Привет, владелец!\n\n"
        "Команды:\n"
        "/users\n/mirrors\n/add ID\n/remove ID\n"
        "/addbasic ID\n/removebasic ID\n/addvip ID\n/removevip ID\n"
        "/listsubs\n/resetcd ID\n/refstat ID"
    )

@admin_dp.message(Command("refstat"))
async def ref_stat(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("❌ /refstat 123456789")
        return
    uid = int(args[1])
    count = db_get_referrals_count(uid)
    rewards = db_get_reward_count(uid)
    refs = db_get_referrals(uid)
    text = f"👥 Рефералы <code>{uid}</code>\n📊 Всего: <b>{count}</b>\n🎁 Наград: <b>{rewards}</b>\n\n"
    for r in refs[:50]:
        text += f"• <code>{r}</code>\n"
    await message.answer(text)

@admin_dp.message(Command("resetcd"))
async def reset_cd(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("❌ /resetcd 123456789")
        return
    uid = int(args[1])
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("DELETE FROM cooldowns WHERE user_id=?", (uid,))
    conn.commit(); conn.close()
    await message.answer(f"✅ Кулдауны сброшены для {uid}.")

@admin_dp.message(Command("mirrors"))
async def list_mirrors(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    mirrors = db_get_mirrors()
    if not mirrors:
        await message.answer("Зеркал пока нет.")
        return
    text = f"🪞 Зеркала: {len(mirrors)}\n\n"
    for m in mirrors:
        text += f"• @{m[1]}\n"
    await message.answer(text)

@admin_dp.message(Command("users"))
async def admin_users(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    users = db_get_users()
    if not users:
        await message.answer("Пока никто не запускал бота.")
        return
    text = f"👥 Всего: {len(users)}\n\n"
    for uid, uname, fname, date in users:
        role = get_user_role(uid)
        tag = {"admin": "👑 Админ", "vip": "💎 Premium", "basic": "💳 Basic"}.get(role, "—")
        uname_str = f"@{uname}" if uname != "нет" else "без юзернейма"
        refs = db_get_referrals_count(uid)
        text += f"• {fname} ({uname_str})\n  ID: <code>{uid}</code>\n  Подписка: {tag}\n  Рефералов: {refs}\n  Дата: {date}\n\n"
    if len(text) > 4000:
        text = text[:4000] + "\n\n... (обрезано)"
    await message.answer(text)

@admin_dp.message(Command("add"))
async def admin_add(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("❌ /add 123456789")
        return
    new_id = int(args[1])
    if new_id in db_get_admins():
        await message.answer("⚠️ Уже админ.")
        return
    db_add_admin(new_id)
    await message.answer(f"✅ {new_id} добавлен в админы.")

@admin_dp.message(Command("remove"))
async def admin_remove(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("❌ /remove 123456789")
        return
    rem_id = int(args[1])
    if rem_id == OWNER_ID:
        await message.answer("❌ Нельзя удалить владельца.")
        return
    if rem_id not in db_get_admins():
        await message.answer("⚠️ Нет в админах.")
        return
    db_remove_admin(rem_id)
    await message.answer(f"✅ {rem_id} снят с админов.")

@admin_dp.message(Command("addbasic"))
async def add_basic(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("❌ /addbasic 123456789")
        return
    new_id = int(args[1])
    if new_id in db_get_basic():
        await message.answer("⚠️ Уже есть Basic.")
        return
    db_add_basic(new_id)
    sent = await notify_user(new_id, "🎉 Вам выдана подписка!\n\n💳 Basic (250₽)\n\nДоступны: «B@t m@tod», «DSA report», «Стрессер».\nПриятного использования!")
    await message.answer(f"✅ {new_id} получил Basic. {'Уведомление отправлено.' if sent else '⚠️ Уведомление не доставлено.'}")

@admin_dp.message(Command("removebasic"))
async def remove_basic(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("❌ /removebasic 123456789")
        return
    rem_id = int(args[1])
    if rem_id not in db_get_basic():
        await message.answer("⚠️ Нет Basic.")
        return
    db_remove_basic(rem_id)
    sent = await notify_user(rem_id, "⚠️ Ваша подписка была снята.\n\n💳 Basic (250₽)\n\nЕсли это ошибка — @yuopoma")
    await message.answer(f"✅ Basic снят с {rem_id}. {'Уведомление отправлено.' if sent else '⚠️ Уведомление не доставлено.'}")

@admin_dp.message(Command("addvip"))
async def add_vip(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("❌ /addvip 123456789")
        return
    new_id = int(args[1])
    if new_id in db_get_vip():
        await message.answer("⚠️ Уже Premium.")
        return
    db_add_vip(new_id)
    sent = await notify_user(new_id, "💎 Вам выдана Premium подписка!\n\n💎 Premium (400₽)\n\nДоступны: B@t m@tod, DSA, Стрессер, Обычная жалоба, AU, Фриз карт, Web metod.\nПриятного использования!")
    await message.answer(f"✅ {new_id} получил Premium. {'Уведомление отправлено.' if sent else '⚠️ Уведомление не доставлено.'}")

@admin_dp.message(Command("removevip"))
async def remove_vip(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("❌ /removevip 123456789")
        return
    rem_id = int(args[1])
    if rem_id not in db_get_vip():
        await message.answer("⚠️ Нет Premium.")
        return
    db_remove_vip(rem_id)
    sent = await notify_user(rem_id, "⚠️ Ваша Premium подписка была снята.\n\n💎 Premium (400₽)\n\nЕсли это ошибка — @yuopoma")
    await message.answer(f"✅ Premium снят с {rem_id}. {'Уведомление отправлено.' if sent else '⚠️ Уведомление не доставлено.'}")

@admin_dp.message(Command("listsubs"))
async def list_subs(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    admins = db_get_admins()
    basic = db_get_basic()
    vip = db_get_vip()
    mirrors = db_get_mirrors()
    await message.answer(
        f"👥 Админы: {admins}\n\n"
        f"💳 Basic (250р): {basic}\n\n"
        f"💎 Premium (400р): {vip}\n\n"
        f"🪞 Зеркал: {len(mirrors)}"
    )

# ==========================================================
# 18. ЗАПУСК
# ==========================================================
async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    init_db()
    asyncio.create_task(temp_subs_loop())
    await asyncio.gather(
        dp.start_polling(bot),
        admin_dp.start_polling(admin_bot)
    )

if __name__ == "__main__":
    asyncio.run(main())