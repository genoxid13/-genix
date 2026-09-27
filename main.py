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
# ВСТАВЬ СЮДА СВОЙ ТОКЕН ОТ @BotFather
# ==========================================================
BOT_TOKEN = "8626104342:AAH4vbsp2YOzcqqa7XYDz8vuFSTOquTmjfk"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Состояния для "Атаки" (чтобы бот знал, что мы ждем от пользователя)
class AttackStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_phone = State()

# Функция для задержки (имитация атаки)
async def delayed_attack_notification(message: Message):
    # 120 секунд = 2 минуты. Если хочешь проверить быстрее, поменяй на 10.
    await asyncio.sleep(120)
    await message.answer("Атака завершена ✅")

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    # Создаем меню с двумя кнопками
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Атака", callback_data="start_attack")],
            [InlineKeyboardButton(text="Наш канал", url="https://t.me/+7Juwn6rwy6owNGYy")]
        ]
    )
    
    await message.answer("Главное меню", reply_markup=keyboard)

# Обработка нажатия на кнопку "Атака"
@dp.callback_query(F.data == "start_attack")
async def start_attack(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите юзернейм цели (без @):")
    await state.set_state(AttackStates.waiting_for_username)
    await callback.answer() # Убирает часики загрузки

# Обработка введенного юзернейма
@dp.message(AttackStates.waiting_for_username)
async def process_username(message: Message, state: FSMContext):
    await state.update_data(username=message.text)
    await message.answer("Теперь введите номер телефона цели:")
    await state.set_state(AttackStates.waiting_for_phone)

# Обработка введенного телефона
@dp.message(AttackStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.clear() # Сбрасываем состояние после ввода
    
    await message.answer("Атака запущена. Ожидайте результат...")
    
    # Запускаем таймер в фоне, чтобы бот не завис
    asyncio.create_task(delayed_attack_notification(message))

async def main() -> None:
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())