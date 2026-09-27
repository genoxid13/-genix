import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# ==========================================================
# ВСТАВЬ СЮДА СВОЙ ТОКЕН ОТ @BotFather (ОБЯЗАТЕЛЬНО В КАВЫЧКАХ!)
# ==========================================================
BOT_TOKEN = "8626104342:AAH4vbsp2YOzcqqa7XYDz8vuFSTOquTmjfk"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

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
async def start_attack(callback: CallbackQuery):
    # Отправляем сообщение про подписку
    await callback.message.answer("у вас нету подписки,напишите админу за покупкой @yuopoma")
    # Убирает часики загрузки на кнопке
    await callback.answer()

async def main() -> None:
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())