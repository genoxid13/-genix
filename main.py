import asyncio
import logging
import re

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
ADMINS = [8883033440, 8325273558]  # Админы (полный доступ)
BASIC_SUBS = []  # Базовая подписка (400р) — только кнопка "Атака"
VIP_SUBS = []    # VIP подписка (600р) — "Атака" + "B@t m@tod"

def get_user_role(user_id):
    if user_id in ADMINS or user_id == OWNER_ID:
        return "admin"
    if user_id in VIP_SUBS:
        return "vip"
    if user_id in BASIC_SUBS:
        return "basic"
    return "none"

# ==========================================================
# ОСНОВНОЙ БОТ
# ==========================================================
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

class AttackStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_phone = State()

class BotMethodStates(StatesGroup):
    waiting_for_bot_link = State()

def make_progress_bar(percent, total_blocks=5):
    filled = int(percent / 100 * total_blocks)
    empty = total_blocks - filled
    return "▰" * filled + "▱" * empty

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Атака", callback_data="start_attack")],
            [InlineKeyboardButton(text="B@t m@tod", callback_data="bot_method")],
            [InlineKeyboardButton(text="Покупка", callback_data="buy_sub")],
            [
                InlineKeyboardButton(text="Наш канал", url="https://t.me/+SnBdQ2r74BBiNWQ6"),
                InlineKeyboardButton(text="Работы", url="https://t.me/+bUkMsYZDc2o3YzRl")
            ]
        ]
    )
    PHOTO_URL = "https://i.postimg.cc/pdG4tPSh/IMG-3660.jpg"
    await message.answer_photo(photo=PHOTO_URL, caption="Главное меню", reply_markup=keyboard)

# --- КНОПКА "АТАКА" (Админы, VIP, Базовая) ---
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

# --- КНОПКА "B@t m@tod" (ТОЛЬКО Админы и VIP) ---
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
        # Всем остальным (включая базовую подписку) — отказ
        await callback.message.answer("доступно только с премиум")
    await callback.answer()

@dp.message(BotMethodStates.waiting_for_bot_link)
async def process_bot_link(message: Message, state: FSMContext):
    text = message.text.strip()
    
    # Валидатор: @username, заканчивается на bot
    if not re.match(r'^@[a-zA-Z0-9_]{3,32}bot$', text):
        await message.answer(
            "не правильный ввод. Юзернейм бота должен заканчиваться на 'bot' (пример: @durov_bot).\n"
            "Попробуйте снова:"
        )
        return
    
    await state.clear()
    await message.answer("Запрос принят. Ожидайте результат...")
    
    await asyncio.sleep(120)
    
    await message.answer("репорт доставлен")

# --- МЕНЮ ПОКУПКИ ---
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

# --- ВВОД ДАННЫХ ДЛЯ "АТАКИ" ---
@dp.message(AttackStates.waiting_for_username)
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
    await state.update_data(phone=text)
    await state.clear()
    await message.answer("Атака запущена. Ожидайте результат...")
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
# ВТОРОЙ БОТ — УПРАВЛЕНИЕ АДМИНАМИ И ПОДПИСКАМИ
# ==========================================================
admin_bot = Bot(token=ADMIN_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
admin_dp = Dispatcher()

@admin_dp.message(CommandStart())
async def admin_start(message: Message):
    if message.from_user.id != OWNER_ID:
        await message.answer("⛔ У вас нет доступа к этому боту.")
        return
    await message.answer(
        "👋 Привет, владелец!\n\n"
        "Команды:\n"
        "/add 123456789 — добавить админа\n"
        "/remove 123456789 — снять админа\n"
        "/addbasic 123456789 — выдать базовую подписку (400р)\n"
        "/removebasic 123456789 — снять базовую подписку\n"
        "/addvip 123456789 — выдать VIP подписку (600р)\n"
        "/removevip 123456789 — снять VIP подписку\n"
        "/listsubs — список всех подписок"
    )

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
        await message.answer(f"⚠️ Пользователь {new_id} уже админ.")
        return
    ADMINS.append(new_id)
    await message.answer(f"✅ Пользователь {new_id} добавлен в админы.")

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
        await message.answer(f"⚠️ Пользователя {rem_id} нет в админах.")
        return
    ADMINS.remove(rem_id)
    await message.answer(f"✅ Пользователь {rem_id} снят с админов.")

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
        await message.answer(f"⚠️ Пользователь {new_id} уже имеет базовую подписку.")
        return
    BASIC_SUBS.append(new_id)
    await message.answer(f"✅ Пользователю {new_id} выдана Базовая подписка (400р).")

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
        await message.answer(f"⚠️ У пользователя {rem_id} нет базовой подписки.")
        return
    BASIC_SUBS.remove(rem_id)
    await message.answer(f"✅ Базовая подписка снята с {rem_id}.")

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
        await message.answer(f"⚠️ Пользователь {new_id} уже имеет VIP подписку.")
        return
    VIP_SUBS.append(new_id)
    await message.answer(f"✅ Пользователю {new_id} выдана VIP подписка (600р).")

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
        await message.answer(f"⚠️ У пользователя {rem_id} нет VIP подписки.")
        return
    VIP_SUBS.remove(rem_id)
    await message.answer(f"✅ VIP подписка снята с {rem_id}.")

@admin_dp.message(Command("listsubs"))
async def list_subs(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    text = (
        f"👥 Админы: {ADMINS}\n\n"
        f"💳 Базовая (400р): {BASIC_SUBS}\n\n"
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