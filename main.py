import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8946297186:AAFqzABNVz0ZODPPkr1XF_DFZVFj42LXkXg"
BOT_USERNAME = "@Notif_Egg_bot"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

SUBSCRIBERS = set()

def get_unsubscribe_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔕 Отписаться", callback_data="unsubscribe")]
        ]
    )

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    SUBSCRIBERS.add(message.chat.id)
    await message.answer(
        f"👋 **Привет! Это {BOT_USERNAME}**\n\n"
        "Вы успешно подписались на уведомления о спавне редких яиц и разломов!",
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data == "unsubscribe")
async def process_unsubscribe(callback: types.CallbackQuery):
    SUBSCRIBERS.discard(callback.message.chat.id)
    await callback.answer("Вы отписались от уведомлений.", show_alert=True)

# Прием сообщений от парсера чата Roblox
async def handle_roblox_webhook(request):
    try:
        data = await request.json()
        raw_text = data.get("text", "")

        # Форматирование текста под стиль бота
        if "Secret" in raw_text or "Divine" in raw_text or "Eternal" in raw_text:
            text = (
                f"🔔 **Появилось редкое яйцо!** 🔒\n\n"
                f"💬 **Сообщение из игры:**\n`{raw_text}`"
            )
        elif "Dr. Scramble" in raw_text or "Boss" in raw_text or "spawned" in raw_text:
            text = (
                f"⚠️ **Разлом был открыт** ⚠️\n\n"
                f"🥊 `{raw_text}`"
            )
        else:
            text = f"📢 **Уведомление из игры:**\n{raw_text}"

        for chat_id in list(SUBSCRIBERS):
            try:
                await bot.send_message(
                    chat_id, 
                    text, 
                    parse_mode="Markdown", 
                    reply_markup=get_unsubscribe_kb()
                )
            except Exception as e:
                logging.error(f"Ошибка отправки пользователю {chat_id}: {e}")

        return web.json_response({"status": "success"})

    except Exception as e:
        logging.error(f"Ошибка обработки: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def main():
    app = web.Application()
    app.router.add_post("/webhook", handle_roblox_webhook)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
