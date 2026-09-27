import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

logging.basicConfig(level=logging.INFO)

# === ВСТАВЬТЕ СЮДА НОВЫЙ ТОКЕН В КАВЫЧКАХ ===
BOT_TOKEN = "8626104342:AAH4vbsp2YOzcqqa7XYDz8vuFSTOquTmjfk"

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()


class Form(StatesGroup):
    waiting_for_username = State()
    waiting_for_phone = State()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Запустить", callback_data="start_action")]
        ]
    )
    await message.answer("Привет! Нажми кнопку ниже:", reply_markup=kb)


@dp.callback_query(F.data == "start_action")
async def process_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите юзернейм:")
    await state.set_state(Form.waiting_for_username)
    await callback.answer()


@dp.message(Form.waiting_for_username)
async def process_username(message: Message, state: FSMContext):
    await state.update_data(username=message.text)
    await message.answer("Введите номер телефона:")
    await state.set_state(Form.waiting_for_phone)


@dp.message(Form.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("⏳ Обработка...")
    await asyncio.sleep(5)
    await message.answer("✅ Атака завершена!")
    await state.clear()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
