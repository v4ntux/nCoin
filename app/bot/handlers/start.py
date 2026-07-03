from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

from app.bot.instance import safe_send
from app.config import get_settings
from app.constants import REF_BONUS_INVITER
from app.db.engine import SessionMaker
from app.services.users import get_or_create_user

router = Router()


def _main_kb() -> InlineKeyboardMarkup | None:
    url = get_settings().webapp_url
    if url.startswith("https://"):
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🚀 Play nCoin", web_app=WebAppInfo(url=url)
                    )
                ]
            ]
        )
    return None


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject) -> None:
    if not message.from_user:
        return
    ref_id: int | None = None
    if command.args and command.args.strip().isdigit():
        ref_id = int(command.args.strip())

    async with SessionMaker() as session:
        user, created = await get_or_create_user(
            session,
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name or "",
            referrer_id=ref_id,
        )
        inviter_id = user.referrer_id
        await session.commit()

    if created and inviter_id:
        name = message.from_user.first_name or "Friend"
        await safe_send(
            inviter_id,
            f"👥 <b>{name}</b> joined via your link! +{REF_BONUS_INVITER} Coin",
        )

    kb = _main_kb()
    text = (
        "⚡ <b>Welcome to nCoin!</b>\n\n"
        "👆 Tap the core, earn Coin\n"
        "⛏ Mining works while you rest\n"
        "⬆️ Upgrade your rig\n"
        "👥 Invite friends — get a share of their mining\n"
        "💵 Deposit for VIP rank and withdraw real money\n"
    )
    if kb is None:
        text += "\n<i>Web App URL is not configured yet.</i>"
    await message.answer(text, reply_markup=kb)
