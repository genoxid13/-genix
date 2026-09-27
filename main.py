import asyncio
import logging

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
# 2. АДМИН-АЙДИ (Твой ID уже здесь). 
# Если нужно добавить кого-то еще, пиши через запятую: [8883033440, 123456789]
# ==========================================================
ADMIN_IDS = [8883033440]

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Состояния для админской "Атаки"
class AttackStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_phone = State()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    # Главное меню с 3 кнопками
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

# Обработка нажатия на кнопку "Атака"
@dp.callback_query(F.data == "start_attack")
async def start_attack(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    
    # Проверяем, является ли пользователь админом
    if user_id in ADMIN_IDS:
        # Если админ - запускаем процесс атаки
        await callback.message.answer("Введите юзернейм цели (без @):")
        await state.set_state(AttackStates.waiting_for_username)
    else:
        # Если не админ - показываем отказ и кнопку покупки
        buy_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Покупка", callback_data="buy_sub")]
            ]
        )
        await callback.message.answer("доступ закрыт", reply_markup=buy_keyboard)
    
    await callback.answer() # Убирает часики загрузки

# Обработка кнопки "Покупка"
@dp.callback_query(F.data == "buy_sub")
async def buy_sub(callback: CallbackQuery):
    pay_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="400 рублей", url="https://t.me/yuopoma")]
        ]
    )
    await callback.message.answer("Для покупки подписки нажмите кнопку ниже:", reply_markup=pay_keyboard)
    await callback.answer()

# --- АДМИНСКИЙ ФЛОУ (Пошаговый ввод) ---

# 1. Получаем юзернейм
@dp.message(AttackStates.waiting_for_username)
async def process_username(message: Message, state: FSMContext):
    await state.update_data(username=message.text)
    await message.answer("Теперь введите номер телефона цели:")
    await state.set_state(AttackStates.waiting_for_phone)

# 2. Получаем телефон и запускаем таймер
@dp.message(AttackStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.clear() # Сбрасываем состояние
    
    await message.answer("Атака запущена. Ожидайте результат...")
    
    # Ждем 2 минуты (120 секунд) в фоне
    await asyncio.sleep(120)
    
    # Отправляем результат
    await message.answer("Атака завершена ✅")

async def main() -> None:
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())