import asyncio
import logging
import os
import threading

from flask import Flask
from aiogram import Bot, Dispatcher, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.filters import Command
from aiogram.types import Message

# ==== 配置 ====
TOKEN = os.environ.get("BOT_TOKEN", "1780243372:aPw1oJFaZKGqLzbUSPSxZiTyWlssSX_o_ST")
BASE_URL = "https://misugram.cloud-ip.cc"
VIDEO_FILE_ID = "ZG9jOjIwMDY2MTg3NzcwMDM5NDU4Njc"

logging.basicConfig(level=logging.INFO)

# Flask 应用，用于 Render 健康检查
app = Flask(__name__)

@app.route("/")
@app.route("/health")
def health():
    return "OK", 200

# aiogram 机器人
server = TelegramAPIServer.from_base(BASE_URL)
session = AiohttpSession(api=server)
bot = Bot(token=TOKEN, session=session)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Напиши «эль дрифто» — и я пришлю видео.")

@dp.message(F.text)
async def handle_text(message: Message):
    text = (message.text or "").strip().lower()
    if "эль дрифто" in text:
        try:
            await message.answer_video(video=VIDEO_FILE_ID)
        except Exception as e:
            logging.exception("Ошибка отправки видео: %s", e)
            await message.answer("Не смог отправить видео 😔")

async def run_bot():
    # 启动 polling
    await dp.start_polling(bot)

def start_bot_thread():
    # 在独立线程中运行 asyncio 事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_bot())

if __name__ == "__main__":
    # 启动机器人线程
    threading.Thread(target=start_bot_thread, daemon=True).start()
    # 启动 Flask，监听 Render 分配的端口
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
