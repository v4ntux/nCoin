"""Общий инстанс бота: им пользуются и polling, и веб-слой (уведомления)."""

import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import get_settings

log = logging.getLogger(__name__)

_bot: Bot | None = None
bot_username: str | None = None  # заполняется на старте polling


def get_bot() -> Bot | None:
    global _bot
    if _bot is None:
        settings = get_settings()
        if not settings.bot_token:
            return None
        _bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
    return _bot


async def safe_send(chat_id: int, text: str, **kwargs) -> None:
    """Уведомление без падения запроса, если юзер заблокировал бота и т.п."""
    bot = get_bot()
    if bot is None:
        return
    try:
        await bot.send_message(chat_id, text, **kwargs)
    except Exception as e:  # noqa: BLE001
        log.warning("notify %s failed: %s", chat_id, e)


def withdraw_admin_kb(request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Approve", callback_data=f"wd:ok:{request_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Decline", callback_data=f"wd:no:{request_id}"
                ),
            ]
        ]
    )
