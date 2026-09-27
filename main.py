import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# ==========================================================
# 1. ВСТАВЬ СЮДА СВОЙ ТОКЕН ОТ @BotFather (внутри кавычек)
# ==========================================================
BOT_TOKEN = "8626104342:AAH4vbsp2YOzcqqa7XYDz8vuFSTOquTmjfk"

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    # ==========================================================
    # 2. ЗАМЕНИ ССЫЛКУ НИЖЕ НА СВОЙ КАНАЛ (когда скинешь её)
    # ==========================================================
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Наш канал", url="https://t.me/ТУТ_БУДЕТ_ССЫЛКА")]
        ]
    )
    
    # Отправляем текст "Главное меню" с кнопкой
    await message.answer("Главное меню", reply_markup=keyboard)

async def main() -> None:
    # Запуск бота (бесконечный цикл)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

