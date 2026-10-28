import asyncio
import logging
import os
import threading

from flask import Flask
from aiogram import Bot, Dispatcher, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile

# ==== НАСТРОЙКИ ====
TOKEN = os.environ.get("BOT_TOKEN", "1780243372:aPw1oJFaZKGqLzbUSPSxZiTyWlssSX_o_ST")
BASE_URL = "https://misugram.cloud-ip.cc"
FILE_PATH = "video_id.txt"
LOCAL_VIDEO_PATH = "saved_video.mp4" # Сюда бот скачает видео

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

server = TelegramAPIServer.from_base(BASE_URL)
session = AiohttpSession(api=server)
bot = Bot(token=TOKEN, session=session)
dp = Dispatcher()

def get_video_id():
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r") as f:
            saved_id = f.read().strip()
            if saved_id:
                return saved_id
    return None

def save_video_id(new_id):
    with open(FILE_PATH, "w") as f:
        f.write(new_id)

async def send_saved_video(message: Message, video_id: str):
    """Скачивает видео по file_id и отправляет как локальный файл"""
    try:
        # 1. Получаем информацию о файле
        file_info = await bot.get_file(video_id)
        if not file_info.file_path:
            raise Exception("Не удалось получить путь к файлу")

        # 2. Скачиваем файл на сервер Render
        await bot.download_file(file_info.file_path, LOCAL_VIDEO_PATH)

        # 3. Отправляем как локальный файл
        video_file = FSInputFile(LOCAL_VIDEO_PATH)
        await message.answer_video(video=video_file)
        return True
    except Exception as e:
        log.error("Ошибка при скачивании/отправке видео: %s", e)
        return False
    finally:
        # Удаляем временный файл, чтобы не забивать диск
        if os.path.exists(LOCAL_VIDEO_PATH):
            os.remove(LOCAL_VIDEO_PATH)

@dp.message(CommandStart())
async def cmd_start(message: Message):
    video_id = get_video_id()
    if not video_id:
        await message.answer("Привет! Отправь мне видео, и я запомню его.")
        return

    await message.answer("Привет! Сейчас отправлю твоё видео 🎬")
    success = await send_saved_video(message, video_id)
    if not success:
        if os.path.exists(FILE_PATH): os.remove(FILE_PATH)
        await message.answer("Не смог отправить видео 😔 Пожалуйста, отправь его заново.")

@dp.message(F.text)
async def handle_text(message: Message):
    text = (message.text or "").strip().lower()
    if "эль дрифто" in text:
        video_id = get_video_id()
        if not video_id:
            await message.answer("Я пока не знаю, какое видео отправлять. Отправь мне его!")
            return

        success = await send_saved_video(message, video_id)
        if not success:
            if os.path.exists(FILE_PATH): os.remove(FILE_PATH)
            await message.answer("Видео перестало работать 😔 Отправь мне его заново.")

@dp.message(F.video)
async def catch_video(message: Message):
    new_id = message.video.file_id
    save_video_id(new_id)
    log.info("Получено видео. file_id: %s", new_id)
    await message.answer("✅ Видео сохранено! Теперь я буду отправлять его по команде «эль дрифто».")
    
    # Пробуем сразу отправить, чтобы убедиться, что схема работает
    await message.answer("Проверяю, как оно отправляется...")
    await send_saved_video(message, new_id)

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
