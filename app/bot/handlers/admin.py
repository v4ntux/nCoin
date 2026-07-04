from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)
from sqlalchemy import func, select

from app.bot.instance import safe_send
from app.config import get_settings
from app.core.vip import tier_name
from app.db.engine import SessionMaker
from app.db.models import User, WithdrawRequest
from app.services.economy import credit, credit_usd
from app.services.errors import GameError

router = Router()

_admin_ids = get_settings().admin_id_list
router.message.filter(F.from_user.id.in_(_admin_ids))
router.callback_query.filter(F.from_user.id.in_(_admin_ids))


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    await message.answer(
        "🛠 <b>Admin</b>\n"
        "/panel — веб-панель администратора\n"
        "/stats — метрики\n"
        "/give &lt;id&gt; &lt;amount&gt; — начислить Coin\n"
        "/giveusd &lt;id&gt; &lt;usd&gt; — начислить USD\n"
        "/setvip &lt;id&gt; &lt;tier 0-3&gt; — выдать VIP\n"
        "Заявки на вывод приходят сюда с кнопками."
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    async with SessionMaker() as session:
        users = (await session.execute(select(func.count(User.id)))).scalar_one()
        coins = (
            await session.execute(select(func.coalesce(func.sum(User.coins), 0)))
        ).scalar_one()
        pending = (
            await session.execute(
                select(func.count(WithdrawRequest.id)).where(
                    WithdrawRequest.status == "pending"
                )
            )
        ).scalar_one()
    await message.answer(
        f"📊 <b>Stats</b>\n"
        f"Users: {users}\n"
        f"Coins in game: {coins:,}\n"
        f"Pending withdraws: {pending}".replace(",", " ")
    )


@router.message(Command("give"))
async def cmd_give(message: Message, command: CommandObject) -> None:
    args = (command.args or "").split()
    if len(args) != 2 or not args[0].isdigit() or not args[1].lstrip("-").isdigit():
        await message.answer("Usage: /give <user_id> <amount>")
        return
    uid, amount = int(args[0]), int(args[1])
    async with SessionMaker() as session:
        user = await session.get(User, uid)
        if not user:
            await message.answer("User not found")
            return
        await credit(session, user, amount, "admin_give", {"by": message.from_user.id})
        await session.commit()
        balance = user.coins
    await safe_send(uid, f"🎁 Admin sent you <b>{amount:,} Coin</b>".replace(",", " "))
    await message.answer(f"Done. Balance: {balance:,}".replace(",", " "))


@router.message(Command("giveusd"))
async def cmd_giveusd(message: Message, command: CommandObject) -> None:
    args = (command.args or "").split()
    try:
        uid, usd = int(args[0]), float(args[1])
    except (IndexError, ValueError):
        await message.answer("Usage: /giveusd <user_id> <usd>")
        return
    async with SessionMaker() as session:
        user = await session.get(User, uid)
        if not user:
            await message.answer("User not found")
            return
        await credit_usd(
            session, user, round(usd * 1_000_000), "admin_give",
            {"by": message.from_user.id},
        )
        await session.commit()
        balance = user.usd_micro / 1_000_000
    await safe_send(uid, f"🎁 Admin sent you <b>{usd:g} USD</b>")
    await message.answer(f"Done. USD balance: {balance:g}")


@router.message(Command("setvip"))
async def cmd_setvip(message: Message, command: CommandObject) -> None:
    args = (command.args or "").split()
    if len(args) != 2 or not args[0].isdigit() or args[1] not in {"0", "1", "2", "3"}:
        await message.answer("Usage: /setvip <user_id> <tier 0-3>")
        return
    uid, tier = int(args[0]), int(args[1])
    async with SessionMaker() as session:
        user = await session.get(User, uid)
        if not user:
            await message.answer("User not found")
            return
        user.vip_tier = tier
        await session.commit()
    await safe_send(uid, f"👑 Your rank is now <b>{tier_name(tier)}</b>!")
    await message.answer(f"User {uid} → {tier_name(tier)}")


@router.message(Command("panel"))
async def cmd_panel(message: Message) -> None:
    settings = get_settings()
    url = settings.web_url
    if url:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🛠 Open Admin panel",
                        web_app=WebAppInfo(url=url + "/admin.html"),
                    )
                ]
            ]
        )
        await message.answer("🛠 <b>Admin panel</b>", reply_markup=kb)
    else:
        await message.answer(
            "⚙️ Публичный URL ещё не готов.\n"
            "На Railway домен подхватится сам (RAILWAY_PUBLIC_DOMAIN) после генерации "
            "домена в Settings → Networking. Локально открой "
            f"http://127.0.0.1:{settings.port}/admin.html"
        )


@router.callback_query(F.data.startswith("wd:"))
async def cb_withdraw(query: CallbackQuery) -> None:
    from app.services import admin as admin_service

    _, action, raw_id = (query.data or "").split(":")
    async with SessionMaker() as session:
        try:
            note = await admin_service.decide_withdraw(
                session, int(raw_id), action == "ok"
            )
            await session.commit()
        except GameError as e:
            await query.answer(e.message, show_alert=True)
            return

    if query.message:
        await query.message.edit_text(
            (query.message.html_text or "") + f"\n\n{note}"
        )
    await query.answer("Done")
