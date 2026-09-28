import asyncio
import logging
import random
import re
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from telethon import TelegramClient, functions, types
from telethon.errors import FloodWaitError, SessionPasswordNeededError

# ==========================================================
# 1. ТОКЕНЫ
# ==========================================================
BOT_TOKEN = "8624162572:AAHfUBS0EDdZHb6MrDVzlOQ5mV6Ilfa_gqw"
ADMIN_BOT_TOKEN = "8099293642:AAHZvzUMVG-b_E2sxmFbhD7KOCYSlihRWD8"

# ==========================================================
# 2. TELEthon API
# ==========================================================
API_ID = ТВОЙ_API_ID
API_HASH = "ТВОЙ_API_HASH"
SESSIONS_DIR = "sessions"

# ==========================================================
# 3. ГЛАВНЫЙ АДМИН
# ==========================================================
OWNER_ID = 8883033440

# ==========================================================
# 4. СПИСКИ
# ==========================================================
ADMINS = [8883033440]
BASIC_SUBS = [8325273558]
VIP_SUBS = []
USERS = {}
MIRRORS = []

def get_user_role(user_id):
    if user_id in ADMINS or user_id == OWNER_ID:
        return "admin"
    if user_id in VIP_SUBS:
        return "vip"
    if user_id in BASIC_SUBS:
        return "basic"
    return "none"

def now_str():
    return datetime.now().strftime("%d.%m.%Y %H:%M")

# ==========================================================
# 5. TELEthon — РЕАЛЬНЫЕ ЖАЛОБЫ
# ==========================================================
async def report_message(client, peer_id, message_id, reason_keyword="spam"):
    try:
        step1 = await client(functions.messages.ReportRequest(
            peer=peer_id,
            id=[message_id],
            option=b'',
            message=""
        ))
        if 'Reported' in str(type(step1)):
            return True, "Reported сразу"

        options = getattr(step1, 'options', [])
        if not options:
            return False, "Нет опций на шаге 1"

        target_option = None
        for opt in options:
            if reason_keyword.lower() in opt.text.lower():
                target_option = opt.option
                break
        if not target_option:
            target_option = options[0].option

        step2 = await client(functions.messages.ReportRequest(
            peer=peer_id,
            id=[message_id],
            option=target_option,
            message=""
        ))
        if 'Reported' in str(type(step2)):
            return True, "Reported на шаге 2"

        options2 = getattr(step2, 'options', [])
        if not options2:
            return False, "Нет опций на шаге 2"

        sub_option = options2[0].option
        for opt in options2:
            if "promo" in opt.text.lower():
                sub_option = opt.option
                break

        step3 = await client(functions.messages.ReportRequest(
            peer=peer_id,
            id=[message_id],
            option=sub_option,
            message=""
        ))
        if 'Reported' in str(type(step3)):
            return True, "Reported на шаге 3"

        final_option = getattr(step3, 'option', None)
        if final_option is None:
            final_step = await client(functions.messages.ReportRequest(
                peer=peer_id,
                id=[message_id],
                option=b'',
                message="Spam and abuse"
            ))
        else:
            final_step = await client(functions.messages.ReportRequest(
                peer=peer_id,
                id=[message_id],
                option=final_option,
                message=""
            ))

        if 'Reported' in str(type(final_step)):
            return True, "Reported (финал)"
        return False, f"Не Reported: {final_step}"

    except FloodWaitError as e:
        return False, f"FloodWait: ждать {e.seconds} сек"
    except Exception as e:
        return False, f"Ошибка: {e}"


async def load_sessions():
    sessions = []
    if not os.path.isdir(SESSIONS_DIR):
        os.makedirs(SESSIONS_DIR, exist_ok=True)
        return sessions
    for f in os.listdir(SESSIONS_DIR):
        if f.endswith(".session"):
            sessions.append(os.path.join(SESSIONS_DIR, f.replace(".session", "")))
    return sessions


async def report_with_all_sessions(peer_id, message_id, reason="spam"):
    sessions = await load_sessions()
    if not sessions:
        return [], "Нет сессий в папке sessions"

    results = []
    for session_path in sessions:
        try:
            client = TelegramClient(session_path, API_ID, API_HASH)
            await client.start()
            success, msg = await report_message(client, peer_id, message_id, reason)
            await client.disconnect()
            results.append((os.path.basename(session_path), success, msg))
            await asyncio.sleep(random.uniform(2, 5))
        except Exception as e:
            results.append((os.path.basename(session_path), False, str(e)))
    return results, None

# ==========================================================
# 6. ОБЩИЙ РОУТЕР
# ==========================================================
router = Router()

def make_dispatcher():
    d = Dispatcher()
    d.include_router(router)
    return d

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = make_dispatcher()

admin_bot = Bot(token=ADMIN_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
admin_dp = Dispatcher()

async def send_report(text: str):
    try:
        await admin_bot.send_message(OWNER_ID, text)
    except Exception as e:
        logging.error(f"send_report error: {e}")

async def notify_user(user_id: int, text: str):
    try:
        await bot.send_message(user_id, text)
        return True
    except Exception:
        return False

# ==========================================================
# 7. СОСТОЯНИЯ
# ==========================================================
class AttackStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_phone = State()

class BotMethodStates(StatesGroup):
    waiting_for_bot_link = State()

class CaptchaStates(StatesGroup):
    waiting_for_answer = State()

class MirrorStates(StatesGroup):
    waiting_for_token = State()

class ReportStates(StatesGroup):
    waiting_for_link = State()

# ==========================================================
# 8. УТИЛИТЫ
# ==========================================================
def make_progress_bar(percent, total_blocks=5):
    filled = int(percent / 100 * total_blocks)
    empty = total_blocks - filled
    return "▰" * filled + "▱" * empty

def main_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Атака", callback_data="start_attack")],
            [InlineKeyboardButton(text="Обычная жалоба", callback_data="usual_report")],
            [InlineKeyboardButton(text="B@t m@tod", callback_data="bot_method")],
            [
                InlineKeyboardButton(text="Покупка", callback_data="buy_sub"),
                InlineKeyboardButton(text="Профиль", callback_data="profile")
            ],
            [InlineKeyboardButton(text="Зеркала", callback_data="mirrors")],
            [
                InlineKeyboardButton(text="Наш канал", url="https://t.me/+SnBdQ2r74BBiNWQ6"),
                InlineKeyboardButton(text="Работы", url="https://t.me/+bUkMsYZDc2o3YzRl")
            ]
        ]
    )

# ==========================================================
# 9. ХЕНДЛЕРЫ
# ==========================================================

@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    user = message.from_user
    if user.id not in USERS:
        USERS[user.id] = {
            "username": user.username or "нет",
            "first_name": user.first_name or "нет",
            "date": now_str()
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
    await state.update_data(captcha_answer=a + b)
    await state.set_state(CaptchaStates.waiting_for_answer)
    await message.answer(f"🤖 Проверка на робота\n\nРешите пример: <b>{a} + {b} = ?</b>\n\nНапишите ответ сообщением.")

@router.message(CaptchaStates.waiting_for_answer)
async def captcha_answer(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    correct = data.get("captcha_answer")
    if not text.isdigit() or int(text) != correct:
        a = random.randint(1, 9)
        b = random.randint(1, 9)
        await state.update_data(captcha_answer=a + b)
        await message.answer(f"❌ Неверно. Попробуйте снова:\n\nРешите пример: <b>{a} + {b} = ?</b>")
        return
    await state.update_data(captcha_p