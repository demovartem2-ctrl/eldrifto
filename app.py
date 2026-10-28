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
FILE_PATH = "video_id.txt"

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

# Функция для получения актуального file_id
def get_video_id():
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r") as f:
            saved_id = f.read().strip()
            if saved_id:
                return saved_id
    return None

# Функция для сохранения нового file_id
def save_video_id(new_id):
    with open(FILE_PATH, "w") as f:
        f.write(new_id)
    log.info("Новый file_id сохранен в файл!")


@dp.message(CommandStart())
async def cmd_start(message: Message):
    log.info("Получен /start от %s", message.from_user.id)
    video_id = get_video_id()
    
    if not video_id:
        await message.answer("Привет! Я пока не знаю, какое видео отправлять. Пожалуйста, отправь мне видео, и я его запомню.")
        return

    await message.answer("Привет! Вот твоё видео 🎬")
    try:
        await message.answer_video(video=video_id)
        log.info("Видео отправлено успешно")
    except Exception as e:
        log.exception("Не удалось отправить видео: %s", e)
        # Если сохраненный ID перестал работать, удаляем файл, чтобы бот запросил новое видео
        if os.path.exists(FILE_PATH):
            os.remove(FILE_PATH)
        await message.answer("Ой, видео сломалось 😔 Пожалуйста, отправь мне его заново, и я запомню новое.")


@dp.message(F.text)
async def handle_text(message: Message):
    text = (message.text or "").strip().lower()
    if "эль дрифто" in text:
        video_id = get_video_id()
        if not video_id:
            await message.answer("Я пока не знаю, какое видео отправлять. Отправь мне его, и я запомню!")
            return

        try:
            await message.answer_video(video=video_id)
        except Exception as e:
            log.exception("Ошибка отправки видео: %s", e)
            if os.path.exists(FILE_PATH):
                os.remove(FILE_PATH)
            await message.answer("Видео перестало работать 😔 Отправь мне его заново, и я запомню новое.")


@dp.message(F.video)
async def catch_video(message: Message):
    # Автоматически сохраняем новый file_id
    new_id = message.video.file_id
    save_video_id(new_id)
    log.info("ПОЛУЧЕН И СОХРАНЕН FILE_ID: %s", new_id)
    await message.answer("✅ Видео сохранено! Теперь я буду отправлять его по команде «эль дрифто».")
    # Сразу пересылаем видео, чтобы проверить, что оно работает
    await message.answer_video(video=new_id, caption="Проверка: вот как оно будет выглядеть.")


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
