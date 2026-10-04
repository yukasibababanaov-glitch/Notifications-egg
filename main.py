import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# Логирование
logging.basicConfig(level=logging.INFO)

# Твой токен и данные бота
BOT_TOKEN = "8946297186:AAFqzABNVz0ZODPPkr1XF_DFZVFj42LXkXg"
BOT_USERNAME = "@Notif_Egg_bot"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилище ID чатов (пользователей и каналов), куда отправлять уведомления
SUBSCRIBERS = set()

def get_unsubscribe_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔕 Отписаться", callback_data="unsubscribe")]
        ]
    )

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    SUBSCRIBERS.add(message.chat.id)
    await message.answer(
        f"👋 **Привет! Это {BOT_USERNAME}**\n\n"
        "Вы успешно подписались на уведомления о спавне редких яиц и боссов!",
        parse_mode="Markdown"
    )

# Кнопка отписки
@dp.callback_query(lambda c: c.data == "unsubscribe")
async def process_unsubscribe(callback: types.CallbackQuery):
    SUBSCRIBERS.discard(callback.message.chat.id)
    await callback.answer("Вы отписались от уведомлений.", show_alert=True)

# ---------------------------------------------------------
# HTTP-сервер для приема сигналов из Roblox
# ---------------------------------------------------------

async def handle_roblox_webhook(request):
    try:
        data = await request.json()
        event_type = data.get("type")  # "egg" или "rift"

        if event_type == "egg":
            rarity = data.get("rarity", "Secret")
            egg_name = data.get("egg_name", "Unknown Egg")
            location = data.get("location", "Unknown Area")
            income = data.get("income", "~$0/s")
            rec_speed = data.get("rec_speed", "100M")

            text = (
                f"🔔 **Появилось яйцо · {rarity}** 🔒\n\n"
                f"🥚 **Яйцо:** {egg_name}\n"
                f"📍 **Локация:** {location}\n"
                f"💸 **Доход:** {income}\n"
                f"⚡ **Рекомендованная скорость:** {rec_speed}"
            )

        elif event_type == "rift":
            boss_name = data.get("boss_name", "Dr. Scramble Experiment")
            next_boss = data.get("next_boss", "15:00 (через 29 минут)")

            text = (
                f"⚠️ **Разлом был открыт** ⚠️\n\n"
                f"🥊 Появился **{boss_name}** — битва с боссом началась!! ⚔️\n"
                f"⏳ **Следующий бой босса:** {next_boss}"
            )
        else:
            return web.json_response({"status": "error", "message": "Unknown event type"}, status=400)

        # Отправка всем подписчикам
        for chat_id in list(SUBSCRIBERS):
            try:
                await bot.send_message(
                    chat_id, 
                    text, 
                    parse_mode="Markdown", 
                    reply_markup=get_unsubscribe_kb()
                )
            except Exception as e:
                logging.error(f"Не удалось отправить пользователю {chat_id}: {e}")

        return web.json_response({"status": "success"})

    except Exception as e:
        logging.error(f"Ошибка вебхука: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def main():
    # Запуск HTTP сервера на порту 8080 для Render/Koyeb
    app = web.Application()
    app.router.add_post("/webhook", handle_roblox_webhook)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    logging.info("Веб-сервер запущен на порту 8080")

    # Запуск Long Polling для команд в Telegram
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
