import asyncio
import logging
import os
import threading

from flask import Flask
from aiogram import Bot, Dispatcher, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.filters import CommandStart
from aiogram.types import Message

# ==== НАСТРОЙКИ ====
TOKEN = os.environ.get("BOT_TOKEN", "1780243372:aPw1oJFaZKGqLzbUSPSxZiTyWlssSX_o_ST")
BASE_URL = "https://misugram.cloud-ip.cc"

# Тот самый ID со скриншота
VIDEO_FILE_ID = "ZG9jOjJxODg2NjIxMzE4MzUwMzk0NTg2Nw"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("driftbot")

app = Flask(__name__)

@app.route("/")
@app.route("/health")
def health():
    return "OK", 200

# aiogram
server = TelegramAPIServer.from_base(BASE_URL)
session = AiohttpSession(api=server)
bot = Bot(token=TOKEN, session=session)
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    log.info("Получен /start от %s", message.from_user.id)
    await message.answer("Привет! Вот твоё видео 🎬")
    try:
        await message.answer_video(video=VIDEO_FILE_ID)
        log.info("Видео отправлено успешно")
    except Exception as e:
        log.exception("Не удалось отправить видео: %s", e)
        await message.answer("Не смог отправить видео 😔")


@dp.message(F.text)
async def handle_text(message: Message):
    text = (message.text or "").strip().lower()
    if "эль дрифто" in text:
        try:
            await message.answer_video(video=VIDEO_FILE_ID)
        except Exception as e:
            log.exception("Ошибка отправки видео: %s", e)
            await message.answer("Не смог отправить видео 😔")


@dp.message(F.video)
async def catch_video(message: Message):
    # Если пришлёте новое видео, бот покажет новый ID в чате (на случай если старый перестанет работать)
    log.info("ПОЛУЧЕН FILE_ID: %s", message.video.file_id)
    await message.answer(f"Новый file_id:\n{message.video.file_id}")


async def run_bot():
    log.info("Запуск polling на %s", BASE_URL)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        log.warning("delete_webhook не удался: %s", e)
    await dp.start_polling(bot)


def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)


if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(run_bot()) 
