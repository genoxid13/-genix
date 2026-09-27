import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# ==========================================================
# 1. ВСТАВЬ СЮДА СВОЙ НОВЫЙ ТОКЕН ОТ @BotFather (В КАВЫЧКАХ!)
# ==========================================================
BOT_TOKEN = "8626104342:AAH4vbsp2YOzcqqa7XYDz8vuFSTOquTmjfk"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    # Создаем меню с кнопками
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Атака", callback_data="start_attack")],
            [
                InlineKeyboardButton(text="Наш канал", url="https://t.me/+7Juwn6rwy6owNGYy"),
                InlineKeyboardButton(text="Работы", url="https://t.me/+bUkMsYZDc2o3YzRl")
            ]
        ]
    )
    
    # Твоя картинка
    PHOTO_URL = "https://i.postimg.cc/BnWNfr6N/IMG-3869.jpg"
    
    # Отправляем картинку с подписью "Главное меню" и кнопками
    await message.answer_photo(
        photo=PHOTO_URL,
        caption="Главное меню",
        reply_markup=keyboard
    )

# Обработка нажатия на кнопку "Атака"
@dp.callback_query(F.data == "start_attack")
async def start_attack(callback: CallbackQuery):
    # Отправляем сообщение про подписку
    await callback.message.answer("у вас нету подписки,для покупки пишите @yuopoma")
    # Убирает часики загрузки на кнопке
    await callback.answer()

async def main() -> None:
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())