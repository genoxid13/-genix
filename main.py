import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# ==========================================================
# ВСТАВЬ СЮДА СВОЙ ТОКЕН ОТ @BotFather
# ==========================================================
BOT_TOKEN = 8626104342:AAH4vbsp2YOzcqqa7XYDz8vuFSTOquTmjfk

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    # Создаем меню с кнопками
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Атака", callback_data="attack")],
            [
                InlineKeyboardButton(text="Наш канал", callback_data="channel"),
                InlineKeyboardButton(text="Работы", callback_data="works")
            ],
            [InlineKeyboardButton(text="Профиль", callback_data="profile")],
            [InlineKeyboardButton(text="Мои зеркала", callback_data="mirrors")]
        ]
    )
    
    # Отправляем только текст "Главное меню" и кнопки
    await message.answer("Главное меню", reply_markup=keyboard)

# Обработчик нажатий на кнопки
@dp.callback_query()
async def callbacks(callback: CallbackQuery):
    if callback.data == "attack":
        await callback.message.answer("Вы нажали: Атака")
    elif callback.data == "channel":
        await callback.message.answer("Вы нажали: Наш канал")
    elif callback.data == "works":
        await callback.message.answer("Вы нажали: Работы")
    elif callback.data == "profile":
        await callback.message.answer("Вы нажали: Профиль")
    elif callback.data == "mirrors":
        await callback.message.answer("Вы нажали: Мои зеркала")
    
    # Убирает "часики" загрузки на кнопке после нажатия
    await callback.answer()

async def main() -> None:
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())



