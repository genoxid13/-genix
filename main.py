import asyncio
import logging
import re

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# ==========================================================
# 1. ВСТАВЬ СЮДА СВОЙ НОВЫЙ ТОКЕН ОТ @BotFather (В КАВЫЧКАХ!)
# ==========================================================
BOT_TOKEN = "8626104342:AAH4vbsp2YOzcqqa7XYDz8vuFSTOquTmjfk"

# ==========================================================
# 2. АДМИН-АЙДИ (Ты + новый пользователь)
# ==========================================================
ADMIN_IDS = [8883033440, 8325273558]

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Состояния для админской "Атаки"
class AttackStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_phone = State()

# Функция для отрисовки полоски прогресса
def make_progress_bar(percent, total_blocks=5):
    filled = int(percent / 100 * total_blocks)
    empty = total_blocks - filled
    return "▰" * filled + "▱" * empty

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Атака", callback_data="start_attack")],
            [
                InlineKeyboardButton(text="Наш канал", url="https://t.me/+SnBdQ2r74BBiNWQ6"),
                InlineKeyboardButton(text="Работы", url="https://t.me/+bUkMsYZDc2o3YzRl")
            ]
        ]
    )
    
    PHOTO_URL = "https://i.postimg.cc/BnWNfr6N/IMG-3869.jpg"
    
    await message.answer_photo(
        photo=PHOTO_URL,
        caption="Главное меню",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "start_attack")
async def start_attack(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    
    if user_id in ADMIN_IDS:
        text = (
            "📵 Session Report · новый запрос\n"
            "Введите цель: @username или id123456.\n"
            "Пример: @durov или id987654321."
        )
        
        sent_msg = await callback.message.answer(text)
        await state.update_data(msg_to_delete=sent_msg.message_id)
        await state.set_state(AttackStates.waiting_for_username)
    else:
        buy_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Покупка", callback_data="buy_sub")]
            ]
        )
        await callback.message.answer("доступ закрыт", reply_markup=buy_keyboard)
    
    await callback.answer()

@dp.callback_query(F.data == "buy_sub")
async def buy_sub(callback: CallbackQuery):
    pay_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="400 рублей", url="https://t.me/yuopoma")]
        ]
    )
    await callback.message.answer("Для покупки подписки нажмите кнопку ниже:", reply_markup=pay_keyboard)
    await callback.answer()

# 1. Получаем юзернейм
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

# 2. Получаем телефон, проверяем и запускаем анимацию
@dp.message(AttackStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    text = message.text.strip()
    
    allowed_chars = re.match(r'^[\d\s\+\-\(\)]+$', text)
    if not allowed_chars:
        await message.answer(
            "не правильный ввод\n"
            "Введите номер телефона цели (пример: +79999999999):"
        )
        return
    
    digits_only = re.sub(r'\D', '', text)
    if not (10 <= len(digits_only) <= 15):
        await message.answer(
            "не правильный ввод\n"
            "Введите номер телефона цели (пример: +79999999999):"
        )
        return
    
    await state.update_data(phone=text)
    await state.clear()
    
    # Стартовое сообщение
    await message.answer("Атака запущена. Ожидайте результат...")
    
    # Первый кадр прогресса - 10%
    progress_msg = await message.answer(
        "📵 Session Report\n"
        "⏳ Проверяю номер и соединение\n"
        "▰▱▱▱▱  10%\n"
        "Попытка: 1/40"
    )
    
    # Анимация от 20% до 100% (10 шагов * 12 секунд = 120 секунд)
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
    
    # Финальная пауза и сообщение об успехе
    await asyncio.sleep(12)
    await message.answer("📵 Session Report\n✅ Репорт успешно дошел")

async def main() -> None:
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())