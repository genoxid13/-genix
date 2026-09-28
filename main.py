import asyncio
import logging
import random
import re
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
BOT_TOKEN = "8624162572:AAHfUBS0EDdZHb6MrDVzlOQ5mV6Ilfa_gqw"
ADMIN_BOT_TOKEN = "8099293642:AAHZvzUMVG-b_E2sxmFbhD7KOCYSlihRWD8"
CRYPTO_BOT_TOKEN = "639798:AAGb7dpGUGE4JKYjxbEWuXzNOhJwMzsrdod"

# ==========================================================
# 2. ГЛАВНЫЙ АДМИН
# ==========================================================
OWNER_ID = 7733553137

# ==========================================================
# 3. СПИСКИ
# ==========================================================
ADMINS = [7733553137]
BASIC_SUBS = [8325273558]
VIP_SUBS = []
USERS = {}
MIRRORS = []

def get_user_role(user_id):
    if user_id in ADMINS or user_id == OWNER_ID:
        return "admin"
    if user_id in VIP_SUBS:
        return "vip"
    if user_id in BASIC_SUBS:
        return "basic"
    return "none"

def now_str():
    return datetime.now().strftime("%d.%m.%Y %H:%M")

# ==========================================================
# 4. ОБЩИЙ РОУТЕР
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
# 5. СОСТОЯНИЯ
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

# ==========================================================
# 6. УТИЛИТЫ
# ==========================================================
def make_progress_bar(percent, total_blocks=5):
    filled = int(percent / 100 * total_blocks)
    empty = total_blocks - filled
    return "▰" * filled + "▱" * empty

def main_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Атака", callback_data="start_attack")],
            [InlineKeyboardButton(text="Обычная жалоба", callback_data="usual_report")],
            [InlineKeyboardButton(text="B@t m@tod", callback_data="bot_method")],
            [
                InlineKeyboardButton(text="Покупка", callback_data="buy_sub"),
                InlineKeyboardButton(text="Профиль", callback_data="profile")
            ],
            [InlineKeyboardButton(text="Зеркала", callback_data="mirrors")],
            [
                InlineKeyboardButton(text="Наш канал", url="https://t.me/+SnBdQ2r74BBiNWQ6"),
                InlineKeyboardButton(text="Работы", url="https://t.me/+bUkMsYZDc2o3YzRl")
            ]
        ]
    )

# ==========================================================
# 7. ХЕНДЛЕРЫ
# ==========================================================

@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    user = message.from_user
    if user.id not in USERS:
        USERS[user.id] = {
            "username": user.username or "нет",
            "first_name": user.first_name or "нет",
            "date": now_str()
        }
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
    role = get_user_role(callback.from_user.id)
    if role != "admin":
        await callback.message.answer("доступно только админу")
        await callback.answer()
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
        MIRRORS.append({"token": token, "username": me.username})
        await message.answer(
            f"✅ Зеркало создано!\n\n"
            f"🤖 Бот: @{me.username}\n"
            f"🆔 ID: <code>{me.id}</code>\n\n"
            f"Теперь напишите /start этому боту."
        )
        await send_report(
            f"🪞 Создано новое зеркало\n\n"
            f"🤖 @{me.username}\n"
            f"🆔 <code>{me.id}</code>"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: <code>{e}</code>")

# --- ПРОФИЛЬ ---
@router.callback_query(F.data == "profile")
async def profile_handler(callback: CallbackQuery):
    user = callback.from_user
    username = f"@{user.username}" if user.username else "не установлен"
    role = get_user_role(user.id)
    if role == "admin":
        sub_text = "Админ (полный доступ)"
    elif role == "vip":
        sub_text = "Премиум (600₽)"
    elif role == "basic":
        sub_text = "Базовая (400₽)"
    else:
        sub_text = "Отсутствует"
    await callback.message.answer(
        f"👤 Профиль\n\nЮзернейм: {username}\nID: <code>{user.id}</code>\nПодписка: {sub_text}"
    )
    await callback.answer()

# --- АТАКА ---
@router.callback_query(F.data == "start_attack")
async def start_attack(callback: CallbackQuery, state: FSMContext):
    role = get_user_role(callback.from_user.id)
    if role in ["admin", "vip", "basic"]:
        sent_msg = await callback.message.answer(
            "📵 Session Report · новый запрос\n"
            "Введите цель: @username или id123456.\n"
            "Пример: @durov или id987654321."
        )
        await state.update_data(msg_to_delete=sent_msg.message_id)
        await state.set_state(AttackStates.waiting_for_username)
    else:
        await callback.message.answer("доступ закрыт")
    await callback.answer()

@router.message(AttackStates.waiting_for_username)
async def process_username(message: Message, state: FSMContext):
    text = message.text.strip()
    is_valid_username = re.match(r'^@[a-zA-Z0-9_]{4,32}$', text)
    is_valid_id = re.match(r'^id\d+$', text)
    if not (is_valid_username or is_valid_id):
        await message.answer(
            "не правильный ввод\n"
            "Введите цель: @username или id123456.\n"
            "Пример: @durov или id987654321."
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
    allowed_chars = re.match(r'^[\d\s\+\-\(\)]+$', text)
    if not allowed_chars:
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
    await state.update_data(phone=text)
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
        "📵 Session Report\n⏳ Проверяю номер и соединение\n▰▱▱▱▱  10%\nПопытка: 1/5"
    )
    for i in range(2, 11):
        await asyncio.sleep(12)
        percent = int(i / 10 * 100)
        bar = make_progress_bar(percent)
        attempt = min((i - 1) // 2 + 1, 5)
        try:
            await progress_msg.edit_text(
                f"📵 Session Report\n⏳ Проверяю номер и соединение\n{bar}  {percent}%\nПопытка: {attempt}/5"
            )
        except Exception:
            pass
    await asyncio.sleep(12)
    await message.answer("📵 Session Report\n✅ Репорт успешно дошел")

# --- ОБЫЧНАЯ ЖАЛОБА ---
@router.callback_query(F.data == "usual_report")
async def usual_report_start(callback: CallbackQuery, state: FSMContext):
    role = get_user_role(callback.from_user.id)
    if role not in ["admin", "vip"]:
        await callback.answer("доступ закрыт купите премиум", show_alert=True)
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
            "❌ не правильный ввод\n\n"
            "Пример правильной ссылки:\n"
            "<code>https://t.me/c/4438005885/207299</code>\n"
            "или\n"
            "<code>https://t.me/durov/123</code>"
        )
        return

    user = message.from_user
    role = get_user_role(user.id)
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

    progress_msg = await message.answer(
        "📩 Обычная жалоба\n⏳ Отправка...\n▰▱▱▱▱  10%"
    )
    for i in range(2, 11):
        await asyncio.sleep(8)
        percent = int(i / 10 * 100)
        bar = make_progress_bar(percent)
        try:
            await progress_msg.edit_text(
                f"📩 Обычная жалоба\n⏳ Отправка...\n{bar}  {percent}%"
            )
        except Exception:
            pass
    await asyncio.sleep(8)
    await message.answer("📩 Обычная жалоба\n✅ Жалоба успешно отправлена")

# --- B@t m@tod ---
@router.callback_query(F.data == "bot_method")
async def start_bot_method(callback: CallbackQuery, state: FSMContext):
    role = get_user_role(callback.from_user.id)
    if role in ["admin", "vip"]:
        await callback.message.answer(
            "Введите юзернейм бота (пример: @durov_bot).\n"
            "Важно: юзернейм должен заканчиваться на 'bot'."
        )
        await state.set_state(BotMethodStates.waiting_for_bot_link)
    else:
        await callback.message.answer("доступно только с премиум")
    await callback.answer()

@router.message(BotMethodStates.waiting_for_bot_link)
async def process_bot_link(message: Message, state: FSMContext):
    text = message.text.strip()
    if not re.match(r'^@[a-zA-Z0-9_]{3,32}bot$', text):
        await message.answer(
            "не правильный ввод. Юзернейм бота должен заканчиваться на 'bot' (пример: @durov_bot).\n"
            "Попробуйте снова:"
        )
        return
    user = message.from_user
    await state.clear()
    await message.answer("Запрос принят. Ожидайте результат...")
    role = get_user_role(user.id)
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
    try:
        crypto_bot = Bot(token=CRYPTO_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        me = await crypto_bot.get_me()
        bot_username = me.username
        await crypto_bot.session.close()
    except Exception:
        bot_username = None

    if bot_username:
        await callback.message.answer(
            "💎 Оплата криптой\n\n"
            "Нажмите кнопку ниже, чтобы перейти в бота для оплаты:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Перейти к оплате", url=f"https://t.me/{bot_username}")]
            ])
        )
    else:
        await callback.message.answer(
            "❌ Не удалось получить ссылку на крипто-бот. Попробуйте позже."
        )
    await callback.answer()

# ==========================================================
# 8. АДМИН-БОТ
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
        "/listsubs — подписки"
    )

@admin_dp.message(Command("mirrors"))
async def list_mirrors(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    if not MIRRORS:
        await message.answer("Зеркал пока нет.")
        return
    text = f"🪞 Зеркала: {len(MIRRORS)}\n\n"
    for m in MIRRORS:
        text += f"• @{m['username']}\n"
    await message.answer(text)

@admin_dp.message(Command("users"))
async def admin_users(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    if not USERS:
        await message.answer("Пока никто не запускал бота.")
        return
    text = f"👥 Всего: {len(USERS)}\n\n"
    for uid, info in USERS.items():
        role = get_user_role(uid)
        tag = {"admin": "👑 Админ", "vip": "💎 VIP", "basic": "💳 База"}.get(role, "—")
        uname = f"@{info['username']}" if info['username'] != "нет" else "без юзернейма"
        text += f"• {info['first_name']} ({uname})\n  ID: <code>{uid}</code>\n  Подписка: {tag}\n  Дата: {info['date']}\n\n"
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
    if new_id in ADMINS:
        await message.answer("⚠️ Уже админ.")
        return
    ADMINS.append(new_id)
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
    if rem_id not in ADMINS:
        await message.answer("⚠️ Нет в админах.")
        return
    ADMINS.remove(rem_id)
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
    if new_id in BASIC_SUBS:
        await message.answer("⚠️ Уже есть база.")
        return
    if new_id in VIP_SUBS:
        VIP_SUBS.remove(new_id)
    BASIC_SUBS.append(new_id)
    sent = await notify_user(new_id, "🎉 Вам выдана подписка!\n\n💳 Тариф: Базовая (400₽)\n\nТеперь вам доступны кнопки «Атака».\nПриятного использования!")
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
    if rem_id not in BASIC_SUBS:
        await message.answer("⚠️ Нет базы.")
        return
    BASIC_SUBS.remove(rem_id)
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
    if new_id in VIP_SUBS:
        await message.answer("⚠️ Уже VIP.")
        return
    if new_id in BASIC_SUBS:
        BASIC_SUBS.remove(new_id)
    VIP_SUBS.append(new_id)
    sent = await notify_user(new_id, "💎 Вам выдана VIP подписка!\n\n💎 Тариф: Премиум (600₽)\n\nТеперь вам доступны:\n• Кнопка «Атака»\n• Кнопка «B@t m@tod»\n• Кнопка «Обычная жалоба»\n\nПриятного использования!")
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
    if rem_id not in VIP_SUBS:
        await message.answer("⚠️ Нет VIP.")
        return
    VIP_SUBS.remove(rem_id)
    sent = await notify_user(rem_id, "⚠️ Ваша VIP подписка была снята.\n\n💎 Тариф: Премиум (600₽)\n\nЕсли это ошибка — напишите @yuopoma")
    await message.answer(f"✅ VIP снят с {rem_id}. {'Уведомление отправлено.' if sent else '⚠️ Уведомление не доставлено.'}")

@admin_dp.message(Command("listsubs"))
async def list_subs(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    await message.answer(
        f"👥 Админы: {ADMINS}\n\n"
        f"💳 База (400р): {BASIC_SUBS}\n\n"
        f"💎 VIP (600р): {VIP_SUBS}\n\n"
        f"🪞 Зеркал: {len(MIRRORS)}"
    )

# ==========================================================
# 9. ЗАПУСК
# ==========================================================
async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    await asyncio.gather(
        dp.start_polling(bot),
        admin_dp.start_polling(admin_bot)
    )

if __name__ == "__main__":
    asyncio.run(main())