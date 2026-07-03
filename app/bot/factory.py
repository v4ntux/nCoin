from aiogram import Bot, Dispatcher

from app.bot import instance
from app.bot.handlers import admin, start


def create_bot() -> Bot:
    bot = instance.get_bot()
    if bot is None:
        raise RuntimeError("BOT_TOKEN is not set")
    return bot


async def _on_startup(bot: Bot) -> None:
    me = await bot.get_me()
    instance.bot_username = me.username


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.startup.register(_on_startup)
    return dp
