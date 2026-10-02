import asyncio
import logging
import random
import re
import os
import sqlite3
import time
from datetime import datetime

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

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
# 4. КУЛДАУНЫ (в секундах)
# ==========================================================
COOLDOWN_SESSION = 15 * 60
COOLDOWN_BOT = 10 * 60
COOLDOWN_REPORT = 15 * 60
COOLDOWN_FREEZE = 12 * 60 * 60

# ==========================================================
# 5. БАЗА ДАННЫХ
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

# ==========================================================
# 6. РОЛЬ
# ==========================================================
def get_user_role(user_id):
    if user_id in db_get_admins() or user_id == OWNER_ID:
        return "admin"
    if user_id in db_get_vip():
        return "vip"
    if user_id in db_get_basic():
        return "basic"
    return "none"

def is_staff(user_id):
    return user_id == OWNER_ID or user_id in db_get_admins()

def now_str():
    return datetime.now().strftime("%d.%m.%Y %H:%M")

# ==========================================================
# 7. РОУТЕР
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
# 8. ПРОВЕРКА ПОДПИСКИ
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
# 9. СОСТОЯНИЯ
# ==========================================================
class AttackStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_phone = State()

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

# ==========================================================
# 10. КЛАВИАТУРЫ
# ==========================================================
def make_progress_bar(percent, total_blocks=5):
    filled = int(percent / 100 * total_blocks)
    return "▰" * filled + "▱" * (total_blocks - filled)

def main_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="session met@d", callback_data="start_attack")],
            [InlineKeyboardButton(text="Обычная жалоба", callback_data="usual_report")],
            [InlineKeyboardButton(text="B@t m@tod", callback_data="bot_method")],
            [InlineKeyboardButton(text="Фриз карт", callback_data="freeze_cards")],
            [
                InlineKeyboardButton(text="Покупка", callback_data="buy_sub"),
                InlineKeyboardButton(text="Профиль", callback_data="profile")
            ],
            [InlineKeyboardButton(text="Зеркала", callback_data="mirrors")],
            [
                InlineKeyboardButton(text="Наш канал", url=CHANNEL_LINK),
                InlineKeyboardButton(text="Работы", url="https://t.me/+bUkMsYZDc2o3YzRl")
            ]
        ]
    )

def freeze_banks_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏦 Т-Банк", callback_data="freeze_tbank")],
            [InlineKeyboardButton(text="🏦 Сбербанк", callback_data="freeze_sber")],
            [InlineKeyboardButton(text="🏦 Альфа-Банк", callback_data="freeze_alfa")],
            [InlineKeyboardButton(text="🏦 Озон Банк", callback_data="freeze_ozon")]
        ]
    )

# ==========================================================
# 11. ХЕНДЛЕРЫ
# ==========================================================

@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    user = message.from_user

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

    data = await state.get_data()
    if data.get("captcha_passed"):
        PHOTO_URL = "https://i.postimg.cc/BnWNfr6N/IMG-3869.jpg"
        await message.answer_photo(photo=PHOTO_URL, caption="Главное меню", reply_markup=main_menu_keyboard())
        return

    a = random.randint(1, 9)
    b = random.randint(1, 9)
    await state.update_data(captcha_answer=a + b)
    await state.set_state(CaptchaStates.waiting_for_answer)
    await message.answer(f"🤖 Проверка на робота\n\nРешите пример: <b>{a} + {b} = ?</b>\n\nНапишите ответ сообщением.")

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

    data = await state.get_data()
    if data.get("captcha_passed"):
        PHOTO_URL = "https://i.postimg.cc/BnWNfr6N/IMG-3869.jpg"
        await callback.message.answer_photo(photo=PHOTO_URL, caption="Главное меню", reply_markup=main_menu_keyboard())
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
    PHOTO_URL = "https://i.postimg.cc/BnWNfr6N/IMG-3869.jpg"
    await message.answer_photo(photo=PHOTO_URL, caption="Главное меню", reply_markup=main_menu_keyboard())

# --- ЗЕРКАЛА ---
@router.callback_query(F.data == "mirrors")
async def mirrors_handler(callback: CallbackQuery, state: FSMContext):
    if get_user_role(callback.from_user.id) != "admin":
        await callback.answer("доступ закрыт купите премиум", show_alert=True)
        return
    await callback.message.answer(
        "🪞 Создание зеркала\n\n"
        "Отправьте токен нового бота (получите его у @BotFather).\n"
        "Формат: <code>123456789:AAxxxxxxxxxxxxxxxxxxxxxx</code>"
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
        "vip": "Премиум (600₽)",
        "basic": "Базовая (400₽)",
    }.get(role, "Отсутствует")
    await callback.message.answer(
        f"👤 Профиль\n\nЮзернейм: {username}\nID: <code>{user.id}</code>\nПодписка: {sub_text}"
    )
    await callback.answer()

# --- SESSION MET@D ---
@router.callback_query(F.data == "start_attack")
async def start_attack(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    role = get_user_role(user_id)
    if role not in ["admin", "vip", "basic"]:
        await callback.answer("доступ закрыт купите премиум", show_alert=True)
        return

    if not is_staff(user_id):
        ok, left = cd_check(user_id, "session", COOLDOWN_SESSION)
        if not ok:
            await callback.answer(f"⏳ Кулдаун: {cd_format(left)}", show_alert=True)
            return

    sent_msg = await callback.message.answer(
        "📵 Session met@d · новый запрос\n"
        "Введите цель: @username или id123456.\n"
        "Пример: @durov или id987654321."
    )
    await state.update_data(msg_to_delete=sent_msg.message_id)
    await state.set_state(AttackStates.waiting_for_username)
    await callback.answer()

@router.message(AttackStates.waiting_for_username)
async def process_username(message: Message, state: FSMContext):
    text = message.text.strip()
    if not (re.match(r'^@[a-zA-Z0-9_]{4,32}$', text) or re.match(r'^id\d+$', text)):
        await message.answer(
            "не правильный ввод\nВведите цель: @username или id123456.\nПример: @durov или id987654321."
        )
        return
    data = await state.get_data()
    msg_to_delete = data.get("msg_to_delete")
    if msg_to_delete:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_to_delete)
        except Exception:
            pass
    await state.update_data(username=text)
    await message.answer("Теперь введите номер телефона цели (пример: +79999999999):")
    await state.set_state(AttackStates.waiting_for_phone)

@router.message(AttackStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    text = message.text.strip()
    if not re.match(r'^[\d\s\+\-\(\)]+$', text):
        await message.answer("не правильный ввод\nВведите номер телефона цели (пример: +79999999999):")
        return
    digits_only = re.sub(r'\D', '', text)
    if not (10 <= len(digits_only) <= 15):
        await message.answer("не правильный ввод\nВведите номер телефона цели (пример: +79999999999):")
        return
    data = await state.get_data()
    target_username = data.get("username", "неизвестно")
    user = message.from_user
    role = get_user_role(user.id)

    if not is_staff(user.id):
        cd_set_last(user.id, "session")

    await state.clear()
    await message.answer("Атака запущена. Ожидайте результат...")
    await send_report(
        f"📵 НОВЫЙ РЕПОРТ · АТАКА\n\n"
        f"👤 {user.first_name}\n"
        f"🔗 @{user.username if user.username else 'без юзернейма'}\n"
        f"🆔 <code>{user.id}</code>\n"
        f"📊 Роль: {role}\n"
        f"───────────────\n"
        f"🎯 Цель: <code>{target_username}</code>\n"
        f"📞 Номер: <code>{text}</code>\n"
        f"───────────────\n"
        f"🕐 {now_str()}"
    )
    progress_msg = await message.answer(
        "📵 Session met@d\n⏳ Проверяю номер и соединение\n▰▱▱▱▱  10%\nПопытка: 1/5"
    )
    for i in range(2, 11):
        await asyncio.sleep(12)
        percent = int(i / 10 * 100)
        bar = make_progress_bar(percent)
        attempt = min((i - 1) // 2 + 1, 5)
        try:
            await progress_msg.edit_text(
                f"📵 Session met@d\n⏳ Проверяю номер и соединение\n{bar}  {percent}%\nПопытка: {attempt}/5"
            )
        except Exception:
            pass
    await asyncio.sleep(12)
    await message.answer("📵 Session met@d\n✅ Репорт успешно дошел")

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

    await callback.message.answer(
        "📩 Обычная жалоба\n\n"
        "Отправьте ссылку на сообщение в формате:\n"
        "<code>https://t.me/username/123</code>\n"
        "или\n"
        "<code>https://t.me/c/123456789/123</code>"
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

# --- B@t m@tod ---
@router.callback_query(F.data == "bot_method")
async def start_bot_method(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    role = get_user_role(user_id)
    if role not in ["admin", "vip"]:
        await callback.answer("доступ закрыт купите премиум", show_alert=True)
        return

    if not is_staff(user_id):
        ok, left = cd_check(user_id, "bot", COOLDOWN_BOT)
        if not ok:
            await callback.answer(f"⏳ Кулдаун: {cd_format(left)}", show_alert=True)
            return

    await callback.message.answer(
        "Введите юзернейм бота (пример: @durov_bot).\n"
        "Важно: юзернейм должен заканчиваться на 'bot'."
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

    await callback.message.answer("🏦 Выберите банк:", reply_markup=freeze_banks_keyboard())
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
    await state.update_data(freeze_bank=bank_name)
    await state.set_state(FreezeStates.waiting_for_target)
    await callback.message.answer(
        f"🏦 {bank_name}\n\n"
        "└─ Введите номер телефона или карты цели:\n\n"
        "+79991234567 или 4276 1234 5678 9012"
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

# --- ПОКУПКА ---
@router.callback_query(F.data == "buy_sub")
async def buy_sub(callback: CallbackQuery):
    await callback.message.answer(
        "Выберите подписку:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="400 рублей", url="https://t.me/yuopoma")],
            [InlineKeyboardButton(text="Премиум 600 руб", url="https://t.me/yuopoma")],
            [InlineKeyboardButton(text="Крипта", callback_data="crypto_pay")]
        ])
    )
    await callback.answer()

@router.callback_query(F.data == "crypto_pay")
async def crypto_pay(callback: CallbackQuery):
    await callback.message.answer("💎 Оплата пока не добавлена\n\nНапишите @yuopoma")
    await callback.answer()

# ==========================================================
# 12. АДМИН-БОТ
# ==========================================================
@admin_dp.message(CommandStart())
async def admin_start(message: Message):
    if message.from_user.id != OWNER_ID:
        await message.answer("⛔ У вас нет доступа к этому боту.")
        return
    await message.answer(
        "👋 Привет, владелец!\n\n"
        "Команды:\n"
        "/users — все пользователи\n"
        "/mirrors — список зеркал\n"
        "/add 123456789 — админ\n"
        "/remove 123456789 — снять админа\n"
        "/addbasic 123456789 — База (400р)\n"
        "/removebasic 123456789 — снять Базу\n"
        "/addvip 123456789 — VIP (600р)\n"
        "/removevip 123456789 — снять VIP\n"
        "/listsubs — подписки\n"
        "/resetcd 123456789 — сбросить кулдауны юзера"
    )

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
        tag = {"admin": "👑 Админ", "vip": "💎 VIP", "basic": "💳 База"}.get(role, "—")
        uname_str = f"@{uname}" if uname != "нет" else "без юзернейма"
        text += f"• {fname} ({uname_str})\n  ID: <code>{uid}</code>\n  Подписка: {tag}\n  Дата: {date}\n\n"
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
        await message.answer("⚠️ Уже есть база.")
        return
    db_add_basic(new_id)
    sent = await notify_user(new_id, "🎉 Вам выдана подписка!\n\n💳 Тариф: Базовая (400₽)\n\nТеперь вам доступны кнопки «session met@d».\nПриятного использования!")
    await message.answer(f"✅ {new_id} получил Базу. {'Уведомление отправлено.' if sent else '⚠️ Уведомление не доставлено.'}")

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
        await message.answer("⚠️ Нет базы.")
        return
    db_remove_basic(rem_id)
    sent = await notify_user(rem_id, "⚠️ Ваша подписка была снята.\n\n💳 Тариф: Базовая (400₽)\n\nЕсли это ошибка — напишите @yuopoma")
    await message.answer(f"✅ База снята с {rem_id}. {'Уведомление отправлено.' if sent else '⚠️ Уведомление не доставлено.'}")

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
        await message.answer("⚠️ Уже VIP.")
        return
    db_add_vip(new_id)
    sent = await notify_user(new_id, "💎 Вам выдана VIP подписка!\n\n💎 Тариф: Премиум (600₽)\n\nТеперь вам доступны:\n• Кнопка «session met@d»\n• Кнопка «B@t m@tod»\n• Кнопка «Обычная жалоба»\n• Кнопка «Фриз карт»\n\nПриятного использования!")
    await message.answer(f"✅ {new_id} получил VIP. {'Уведомление отправлено.' if sent else '⚠️ Уведомление не доставлено.'}")

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
        await message.answer("⚠️ Нет VIP.")
        return
    db_remove_vip(rem_id)
    sent = await notify_user(rem_id, "⚠️ Ваша VIP подписка была снята.\n\n💎 Тариф: Премиум (600₽)\n\nЕсли это ошибка — напишите @yuopoma")
    await message.answer(f"✅ VIP снят с {rem_id}. {'Уведомление отправлено.' if sent else '⚠️ Уведомление не доставлено.'}")

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
        f"💳 База (400р): {basic}\n\n"
        f"💎 VIP (600р): {vip}\n\n"
        f"🪞 Зеркал: {len(mirrors)}"
    )

# ==========================================================
# 13. ЗАПУСК
# ==========================================================
async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    init_db()
    await asyncio.gather(
        dp.start_polling(bot),
        admin_dp.start_polling(admin_bot)
    )

if __name__ == "__main__":
    asyncio.run(main())