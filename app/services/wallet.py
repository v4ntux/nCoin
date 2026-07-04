from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.constants import (
    P2P_DAILY_LIMIT_COINS,
    P2P_MIN_COINS,
    USD_MICRO,
    WITHDRAW_MIN_USD,
)
from app.core.clock import utcnow
from app.core.fees import fee_amount, fee_rate
from app.core.vip import tier_name
from app.db.models import DepositRequest, LedgerEntry, User, WithdrawRequest
from app.services import settings_store
from app.services.economy import credit, credit_usd
from app.services.errors import GameError
from app.services.exchange import rate_usd

# методы вывода: ключ → человекочитаемое имя + подпись поля реквизитов
WITHDRAW_METHODS = {
    "card": {"name": "Bank card", "field": "Card number"},
    "usdt": {"name": "USDT (TRC-20)", "field": "Wallet address"},
    "ton": {"name": "TON", "field": "Wallet address"},
    "paypal": {"name": "PayPal", "field": "PayPal email"},
}


def _usd(micro: int) -> float:
    return round(micro / USD_MICRO, 6)


def _check_frozen(user: User) -> None:
    if user.frozen:
        raise GameError("frozen", "Your wallet is frozen. Contact support.")


async def _resolve_recipient(session: AsyncSession, to: str) -> User | None:
    to = to.strip().lstrip("@")
    if to.isdigit():
        return await session.get(User, int(to))
    return (
        await session.execute(
            select(User).where(func.lower(User.username) == to.lower())
        )
    ).scalar_one_or_none()


async def _sent_today(session: AsyncSession, user_id: int) -> int:
    day_start = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    total = (
        await session.execute(
            select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(
                LedgerEntry.user_id == user_id,
                LedgerEntry.reason == "p2p_out",
                LedgerEntry.currency == "coin",
                LedgerEntry.created_at >= day_start,
            )
        )
    ).scalar_one()
    return -int(total)


async def _discount(session: AsyncSession, tier: int) -> float:
    s = await settings_store.load(session)
    return settings_store.discount_mult(settings_store.vip_rules(s), tier)


async def transfer(session: AsyncSession, sender: User, to: str, amount: int) -> dict:
    _check_frozen(sender)
    if amount < P2P_MIN_COINS:
        raise GameError("min_amount", f"Minimum transfer is {P2P_MIN_COINS} Coin")
    if sender.coins < amount:
        raise GameError("not_enough", "Not enough Coin")

    used = await _sent_today(session, sender.id)
    if used + amount > P2P_DAILY_LIMIT_COINS:
        left = max(0, P2P_DAILY_LIMIT_COINS - used)
        raise GameError(
            "daily_limit",
            f"Daily send limit is {P2P_DAILY_LIMIT_COINS} Coin. Left today: {left}",
        )

    recipient = await _resolve_recipient(session, to)
    if recipient is None or recipient.banned or recipient.id == 0:
        raise GameError("no_user", "User not found (they must open the app first)")
    if recipient.id == sender.id:
        raise GameError("self", "Cannot send to yourself")

    mult = await _discount(session, sender.vip_tier)
    fee = fee_amount(amount, "p2p", sender.vip_tier, mult)
    received = amount - fee
    await credit(session, sender, -amount, "p2p_out", {"to": recipient.id})
    await credit(
        session, recipient, received, "p2p_in",
        {"from": sender.id, "fee": fee}, count_earned=False,
    )

    from app.bot.instance import safe_send

    sender_name = sender.first_name or sender.username or sender.id
    await safe_send(
        recipient.id,
        f"💸 <b>+{received:,} Coin</b> from {sender_name}".replace(",", " "),
    )
    return {"sent": amount, "received": received, "fee": fee, "coins": sender.coins}


async def _withdraws_this_week(session: AsyncSession, user_id: int) -> int:
    week_ago = utcnow() - timedelta(days=7)
    return (
        await session.execute(
            select(func.count(WithdrawRequest.id)).where(
                WithdrawRequest.user_id == user_id,
                WithdrawRequest.status != "declined",
                WithdrawRequest.created_at >= week_ago,
            )
        )
    ).scalar_one()


async def wallet_view(session: AsyncSession, user: User) -> dict:
    s = await settings_store.load(session)
    rules = settings_store.vip_rules(s)
    mult = settings_store.discount_mult(rules, user.vip_tier)
    used = await _withdraws_this_week(session, user.id)
    slots = settings_store.withdraws_for(rules, user.vip_tier)
    sent = await _sent_today(session, user.id)
    rate = await rate_usd(session)
    return {
        "vip": user.vip_tier,
        "vip_name": tier_name(user.vip_tier),
        # планы для витрины: цена/скидка/выводы из настроек админа
        "tiers": [
            {
                "tier": rules[t]["tier"],
                "name": rules[t]["name"],
                "deposit_usd": rules[t]["price"],
                "discount": rules[t]["discount"],
                "withdraw_per_week": rules[t]["withdraws"],
            }
            for t in sorted(rules)
        ],
        "withdraw_slots": slots,
        "withdraw_used": used,
        "withdraw_min_usd": WITHDRAW_MIN_USD,
        "withdraw_methods": [
            {"key": k, "name": v["name"], "field": v["field"]}
            for k, v in WITHDRAW_METHODS.items()
        ],
        "usd_rate": rate,
        "fees": {
            "trade": round(fee_rate("trade", user.vip_tier, mult) * 100, 2),
            "p2p": round(fee_rate("p2p", user.vip_tier, mult) * 100, 2),
            "withdraw": round(fee_rate("withdraw", user.vip_tier, mult) * 100, 2),
        },
        "p2p_min": P2P_MIN_COINS,
        "p2p_daily_limit": P2P_DAILY_LIMIT_COINS,
        "p2p_sent_today": sent,
        "support": settings_store.support_view(s),
        "coins": user.coins,
        "usd": _usd(user.usd_micro),
        "frozen": user.frozen,
    }


async def request_withdraw(
    session: AsyncSession,
    user: User,
    amount_usd: float,
    method: str,
    details: str,
) -> dict:
    _check_frozen(user)
    s = await settings_store.load(session)
    rules = settings_store.vip_rules(s)
    slots = settings_store.withdraws_for(rules, user.vip_tier)
    if slots <= 0:
        raise GameError("vip_required", "Upgrade your plan to withdraw")
    used = await _withdraws_this_week(session, user.id)
    if used >= slots:
        raise GameError("no_slots", f"Withdraw limit: {slots}/week for your plan")
    if method not in WITHDRAW_METHODS:
        raise GameError("bad_method", "Choose a withdraw method")
    if not details.strip():
        raise GameError("no_details", f"Enter your {WITHDRAW_METHODS[method]['field']}")
    if amount_usd < WITHDRAW_MIN_USD:
        raise GameError("min_amount", f"Minimum withdraw is {WITHDRAW_MIN_USD} USD")

    micro = round(amount_usd * USD_MICRO)
    mult = settings_store.discount_mult(rules, user.vip_tier)
    fee = fee_amount(micro, "withdraw", user.vip_tier, mult)
    if user.usd_micro < micro + fee:
        raise GameError(
            "not_enough",
            f"Not enough USD (need {_usd(micro + fee)} incl. fee). "
            "Sell Coin on the Exchange first.",
        )

    await credit_usd(session, user, -micro, "withdraw_hold")
    if fee > 0:
        await credit_usd(session, user, -fee, "fee_withdraw")
    req = WithdrawRequest(
        user_id=user.id,
        amount_micro=micro,
        fee_micro=fee,
        amount_usd=round(amount_usd, 2),
        method=method,
        details=details.strip()[:128],
    )
    session.add(req)
    await session.flush()

    from app.bot.instance import safe_send, withdraw_admin_kb

    settings = get_settings()
    mname = WITHDRAW_METHODS[method]["name"]
    for admin_id in settings.admin_id_list:
        await safe_send(
            admin_id,
            (
                f"💵 <b>Withdraw request #{req.id}</b>\n"
                f"User: {user.first_name} (@{user.username or '—'}, id {user.id})\n"
                f"Plan: {tier_name(user.vip_tier)}\n"
                f"Amount: {req.amount_usd} USD (fee {_usd(fee)})\n"
                f"Method: {mname}\n"
                f"Details: <code>{req.details}</code>"
            ),
            reply_markup=withdraw_admin_kb(req.id),
        )
    return {
        "request_id": req.id,
        "amount_usd": req.amount_usd,
        "fee_usd": _usd(fee),
        "usd": _usd(user.usd_micro),
        "slots_left": slots - used - 1,
    }


async def request_deposit(session: AsyncSession, user: User, tier: int) -> dict:
    s = await settings_store.load(session)
    rules = settings_store.vip_rules(s)
    if tier not in (1, 2, 3):
        raise GameError("bad_tier", "Unknown plan")
    info = rules[tier]

    req = DepositRequest(user_id=user.id, tier=tier)
    session.add(req)
    await session.flush()

    from app.bot.instance import safe_send

    settings = get_settings()
    for admin_id in settings.admin_id_list:
        await safe_send(
            admin_id,
            (
                f"🏦 <b>Deposit request #{req.id}</b>\n"
                f"User: {user.first_name} (@{user.username or '—'}, id {user.id})\n"
                f"Wants: {info['name']} (${info['price']})\n"
                f"Approve in admin panel or /setvip {user.id} {tier} after payment."
            ),
        )
    return {"request_id": req.id, "requested_tier": tier, "price_usd": info["price"]}


_TOPUP_METHODS = {
    "visa": "Visa / Mastercard",
    "crypto": "USDT (TRC-20)",
    "humo": "Humo / Uzcard",
}


async def request_topup(
    session: AsyncSession, user: User, method: str, amount_usd: float
) -> dict:
    """Пополнение USD-баланса. Приём платежей ещё не подключён —
    создаём заявку админу, деньги начисляются вручную после оплаты."""
    label = _TOPUP_METHODS.get(method)
    if not label:
        raise GameError("bad_method", "Unknown payment method")
    if amount_usd <= 0:
        raise GameError("bad_amount", "Amount must be positive")

    from app.bot.instance import safe_send

    settings = get_settings()
    for admin_id in settings.admin_id_list:
        await safe_send(
            admin_id,
            (
                f"💳 <b>Top-up request</b>\n"
                f"User: {user.first_name} (@{user.username or '—'}, id {user.id})\n"
                f"Method: {label}\n"
                f"Amount: ${amount_usd:.2f}\n"
                f"After payment: /giveusd {user.id} {amount_usd:.2f}"
            ),
        )
    return {"method": label, "amount_usd": round(amount_usd, 2), "status": "pending"}
