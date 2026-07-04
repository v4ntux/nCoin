from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

from app.bot import instance
from app.bot.instance import safe_send
from app.config import get_settings
from app.constants import REF_BONUS_INVITER, REF_BONUS_NEW
from app.db.engine import SessionMaker
from app.services.users import get_or_create_user

router = Router()


def main_kb() -> InlineKeyboardMarkup:
    """Главная клавиатура: Play (если есть URL) + соцссылки/друзья."""
    s = get_settings()
    url = s.web_url
    rows: list[list[InlineKeyboardButton]] = []
    if url:
        rows.append(
            [InlineKeyboardButton(text="🎮 Play nCoin", web_app=WebAppInfo(url=url))]
        )
    rows.append(
        [InlineKeyboardButton(text="👥 Invite friends", callback_data="invite")]
    )
    row3 = [InlineKeyboardButton(text="ℹ️ How it works", callback_data="how")]
    if s.channel_url.startswith("https://"):
        row3.append(InlineKeyboardButton(text="📢 Channel", url=s.channel_url))
    rows.append(row3)
    return InlineKeyboardMarkup(inline_keyboard=rows)


WELCOME = (
    "⚡️ <b>nCoin</b> — tap, mine &amp; trade\n\n"
    "🪙 Tap the Mellstroy coin — earn Coin\n"
    "⛏ Mining runs even while you sleep\n"
    "📈 Trade Coin for USD on the P2P exchange\n"
    "⬆️ Upgrade your rig, climb the leagues\n"
    "👥 Invite friends — <b>3%</b> of everything they earn, forever\n\n"
    "Tap <b>Play</b> to start 👇"
)

HOW = (
    "ℹ️ <b>How nCoin works</b>\n\n"
    "1️⃣ <b>Tap</b> the coin — each tap = Coin. Watch energy &amp; heat.\n"
    "2️⃣ <b>Mine</b> — passive Coin every 2h, press Collect.\n"
    "3️⃣ <b>Upgrade</b> — spend Coin to earn more (tap / mining / global).\n"
    "4️⃣ <b>Tasks</b> — daily/weekly + partner tasks for big rewards.\n"
    "5️⃣ <b>Exchange</b> — sell Coin for USD at player prices.\n"
    "6️⃣ <b>Wallet</b> — VIP plans, top-up and withdraw.\n\n"
    "The more you upgrade, the faster it all grows. 🚀"
)


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
            f"👥 <b>{name}</b> joined via your link!\n+{REF_BONUS_INVITER} Coin 🪙",
        )

    text = WELCOME
    if not get_settings().web_url:
        text += "\n\n<i>⚙️ Web App URL not set yet — admin is configuring it.</i>"
    await message.answer(text, reply_markup=main_kb())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HOW, reply_markup=main_kb())


@router.callback_query(F.data == "how")
async def cb_how(query: CallbackQuery) -> None:
    await query.message.answer(HOW, reply_markup=main_kb())
    await query.answer()


@router.callback_query(F.data == "invite")
async def cb_invite(query: CallbackQuery) -> None:
    uid = query.from_user.id
    link = f"https://t.me/{instance.bot_username or 'bot'}?start={uid}"
    share = f"https://t.me/share/url?url={link}&text=⚡ Join me in nCoin — tap, mine and trade!"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="📨 Share link", url=share)]]
    )
    await query.message.answer(
        "👥 <b>Invite friends</b>\n\n"
        f"Your link:\n<code>{link}</code>\n\n"
        f"You get <b>+{REF_BONUS_INVITER}</b> Coin, your friend <b>+{REF_BONUS_NEW}</b>, "
        "plus <b>3%</b> of everything they ever earn.",
        reply_markup=kb,
    )
    await query.answer()
