import asyncio
import logging
import os
import threading
import aiohttp

from flask import Flask
from aiogram import Bot, Dispatcher, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile

# ==== НАСТРОЙКИ ====
TOKEN = os.environ.get("BOT_TOKEN", "1780243372:aPw1oJFaZKGqLzbUSPSxZiTyWlssSX_o_ST")
BASE_URL = "https://misugram.cloud-ip.cc"
VIDEO_URL = "https://raw.githubusercontent.com/demovartem2-ctrl/eldrifto/main/ad671c7895d3939722c28e23161df18c.mp4"
LOCAL_VIDEO_PATH = "saved_video.mp4"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("driftbot")

app = Flask(__name__)

@app.route("/")
@app.route("/health")
def health():
    return "OK", 200

server = TelegramAPIServer.from_base(BASE_URL)
session = AiohttpSession(api=server)
bot = Bot(token=TOKEN, session=session)
dp = Dispatcher()

async def download_video():
    """Скачивает видео с GitHub, если его еще нет на сервере"""
    if not os.path.exists(LOCAL_VIDEO_PATH):
        log.info("Скачиваю видео с GitHub...")
        async with aiohttp.ClientSession() as http_session:
            async with http_session.get(VIDEO_URL) as response:
                if response.status == 200:
                    with open(LOCAL_VIDEO_PATH, "wb") as f:
                        f.write(await response.read())
                else:
                    log.error("Ошибка скачивания: статус %s", response.status)
                    return False
    return True

async def send_video(message: Message):
    success = await download_video()
    if not success:
        await message.answer("Не смог скачать видео с GitHub 😔")
        return

    try:
        video_file = FSInputFile(LOCAL_VIDEO_PATH)
        await message.answer_video(video=video_file)
    except Exception as e:
        log.error("Ошибка при отправке видео: %s", e)
        await message.answer("Видео скачалось, но Telegram его не принял 😔")

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Привет! Сейчас отправлю твоё видео 🎬")
    await send_video(message)

@dp.message(F.text)
async def handle_text(message: Message):
    text = (message.text or "").strip().lower()
    if "эль дрифто" in text:
        await send_video(message)

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
