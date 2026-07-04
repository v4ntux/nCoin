"""P2P-движок: объявления, сделки, эскроу, чат, споры, разбор админом.

Платформа держит эскроу коинов и чат; фиат ходит между людьми мимо нас.
Комиссия берётся из продаваемых коинов (покупатель получает amount − fee),
fee уходит на системный аккаунт (MARKET_MAKER_ID).
"""

from datetime import timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import (
    MARKET_MAKER_ID,
    P2P_FEE_BP,
    P2P_MAX_ACTIVE_ADS,
    P2P_MIN_AD_COINS,
    P2P_PAY_WINDOW_SEC,
    PAY_METHODS,
)
from app.core.clock import ts, utcnow
from app.db.models import Ad, Deal, DealMessage, Trade, User
from app.services.economy import credit
from app.services.errors import GameError

ACTIVE_DEAL = ("pending_payment", "paid", "disputed")


def fee_coins(amount: int) -> int:
    return (amount * P2P_FEE_BP) // 10_000


def _name(u: User | None, uid: int) -> str:
    if u is None:
        return "Admin" if uid == MARKET_MAKER_ID else f"Player {uid}"
    return u.display_name or u.first_name or u.username or f"Player {u.id}"


def _check_active(user: User) -> None:
    if user.banned:
        raise GameError("banned", "Account banned")
    if user.frozen:
        raise GameError("frozen", "Account frozen — dispute in progress")


# ---------------------------------------------------------------- объявления


async def create_ad(
    session: AsyncSession, user: User, price_uzs: int, amount: int,
    pay_method: str, pay_details: str,
) -> dict:
    _check_active(user)
    price_uzs = int(price_uzs)
    amount = int(amount)
    if price_uzs < 1:
        raise GameError("bad_price", "Price must be at least 1 UZS")
    if amount < P2P_MIN_AD_COINS:
        raise GameError("min_amount", f"Minimum {P2P_MIN_AD_COINS} Coin")
    if user.coins < amount:
        raise GameError("not_enough", "Not enough Coin")
    if pay_method not in PAY_METHODS:
        raise GameError("bad_method", "Unknown payment method")
    if not pay_details.strip():
        raise GameError("no_details", "Add your payment requisites")

    active = (
        await session.execute(
            select(func.count(Ad.id)).where(Ad.user_id == user.id, Ad.status == "active")
        )
    ).scalar_one()
    if active >= P2P_MAX_ACTIVE_ADS:
        raise GameError("too_many", f"Max {P2P_MAX_ACTIVE_ADS} active ads")

    await credit(session, user, -amount, "p2p_hold", {"ad": True}, count_earned=False)
    ad = Ad(
        user_id=user.id, side="sell", price_uzs=price_uzs, amount_coins=amount,
        remaining_coins=amount, pay_method=pay_method, pay_details=pay_details.strip()[:128],
        status="active",
    )
    session.add(ad)
    await session.flush()
    return {"ad_id": ad.id, "coins": user.coins}


async def close_ad(session: AsyncSession, user: User, ad_id: int) -> dict:
    ad = await session.get(Ad, ad_id)
    if not ad or ad.user_id != user.id:
        raise GameError("no_ad", "Ad not found")
    if ad.status != "active":
        raise GameError("not_active", "Ad already closed")
    busy = (
        await session.execute(
            select(func.count(Deal.id)).where(
                Deal.ad_id == ad.id, Deal.status.in_(ACTIVE_DEAL)
            )
        )
    ).scalar_one()
    if busy:
        raise GameError("ad_busy", "Ad has an active deal — finish it first")
    ad.status = "closed"
    if ad.remaining_coins > 0:
        await credit(session, user, ad.remaining_coins, "p2p_refund",
                     {"ad": ad.id}, count_earned=False)
        ad.remaining_coins = 0
    return {"closed": ad.id, "coins": user.coins}


async def list_ads(session: AsyncSession, viewer_id: int, limit: int = 30) -> list[dict]:
    rows = (
        await session.execute(
            select(Ad, User)
            .join(User, Ad.user_id == User.id)
            .where(Ad.status == "active", Ad.remaining_coins > 0)
            .order_by(Ad.price_uzs.asc(), Ad.id.asc())
            .limit(limit)
        )
    ).all()
    out = []
    for ad, u in rows:
        busy = (
            await session.execute(
                select(func.count(Deal.id)).where(
                    Deal.ad_id == ad.id, Deal.status.in_(ACTIVE_DEAL)
                )
            )
        ).scalar_one()
        out.append({
            "id": ad.id,
            "price": ad.price_uzs,
            "amount": ad.remaining_coins,
            "method": ad.pay_method,
            "method_name": PAY_METHODS.get(ad.pay_method, ad.pay_method),
            "seller": _name(u, u.id),
            "seller_id": u.id,
            "mine": u.id == viewer_id,
            "busy": bool(busy),
        })
    return out


async def my_ads(session: AsyncSession, user: User) -> list[dict]:
    rows = (
        (await session.execute(
            select(Ad).where(Ad.user_id == user.id, Ad.status == "active")
            .order_by(Ad.id.desc())
        )).scalars().all()
    )
    return [{
        "id": a.id, "price": a.price_uzs, "amount": a.remaining_coins,
        "total": a.amount_coins, "method_name": PAY_METHODS.get(a.pay_method, a.pay_method),
    } for a in rows]


# ---------------------------------------------------------------- сделки


async def _sys(session: AsyncSession, deal_id: int, body: str) -> None:
    session.add(DealMessage(deal_id=deal_id, sender_id=0, kind="system", body=body))


async def _notify(uid: int, text: str) -> None:
    from app.bot.instance import safe_send
    await safe_send(uid, text)


async def open_deal(session: AsyncSession, buyer: User, ad_id: int, amount: int) -> dict:
    _check_active(buyer)
    ad = await session.get(Ad, ad_id)
    if not ad or ad.status != "active":
        raise GameError("no_ad", "Ad not available")
    if ad.user_id == buyer.id:
        raise GameError("own_ad", "This is your own ad")
    amount = int(amount)
    if amount < 1 or amount > ad.remaining_coins:
        raise GameError("bad_amount", "Amount exceeds what's available")
    busy = (
        await session.execute(
            select(func.count(Deal.id)).where(
                Deal.ad_id == ad.id, Deal.status.in_(ACTIVE_DEAL)
            )
        )
    ).scalar_one()
    if busy:
        raise GameError("ad_busy", "Someone is already dealing on this ad")

    ad.remaining_coins -= amount  # коины уходят в эскроу сделки
    deal = Deal(
        ad_id=ad.id, buyer_id=buyer.id, seller_id=ad.user_id, amount_coins=amount,
        price_uzs=ad.price_uzs, total_uzs=ad.price_uzs * amount,
        fee_coins=fee_coins(amount), escrow_coins=amount, status="pending_payment",
        pay_deadline=utcnow() + timedelta(seconds=P2P_PAY_WINDOW_SEC),
    )
    session.add(deal)
    await session.flush()
    await _sys(session, deal.id,
               f"Deal opened for {amount} Coin at {ad.price_uzs} UZS "
               f"(total {deal.total_uzs} UZS). Buyer, pay via {PAY_METHODS.get(ad.pay_method, ad.pay_method)} "
               f"then press «I paid».")
    await _notify(ad.user_id, f"🔔 New P2P deal on your ad: {amount} Coin for {deal.total_uzs} UZS.")
    return {"deal_id": deal.id}


async def _expire_if_needed(session: AsyncSession, deal: Deal) -> None:
    """Ленивая авто-отмена: покупатель не оплатил в окно → эскроу назад в объявление."""
    if deal.status == "pending_payment" and deal.pay_deadline and utcnow() > deal.pay_deadline:
        deal.status = "cancelled"
        ad = await session.get(Ad, deal.ad_id)
        if ad:
            ad.remaining_coins += deal.escrow_coins
        deal.escrow_coins = 0
        await _sys(session, deal.id, "Payment window expired — deal cancelled, coins returned.")


async def _guard(session: AsyncSession, user: User, deal_id: int) -> Deal:
    deal = await session.get(Deal, deal_id)
    if not deal or user.id not in (deal.buyer_id, deal.seller_id):
        raise GameError("no_deal", "Deal not found")
    await _expire_if_needed(session, deal)
    return deal


async def mark_paid(session: AsyncSession, user: User, deal_id: int) -> dict:
    deal = await _guard(session, user, deal_id)
    if user.id != deal.buyer_id:
        raise GameError("not_buyer", "Only the buyer can mark as paid")
    if deal.status != "pending_payment":
        raise GameError("bad_state", "Deal is not awaiting payment")
    deal.status = "paid"
    deal.paid_at = utcnow()
    await _sys(session, deal_id, "Buyer marked the payment as sent. Seller, confirm you received it.")
    await _notify(deal.seller_id, "💸 Buyer says they paid. Check and release the coins.")
    return {"status": deal.status}


async def release(session: AsyncSession, user: User, deal_id: int) -> dict:
    deal = await _guard(session, user, deal_id)
    if user.id != deal.seller_id:
        raise GameError("not_seller", "Only the seller can release")
    if deal.status not in ("paid", "pending_payment"):
        raise GameError("bad_state", "Nothing to release")
    buyer = await session.get(User, deal.buyer_id)
    fee = deal.fee_coins
    payout = deal.escrow_coins - fee
    if buyer:
        await credit(session, buyer, payout, "p2p_release", {"deal": deal.id}, count_earned=False)
    if fee > 0:
        platform = await session.get(User, MARKET_MAKER_ID)
        if platform:
            await credit(session, platform, fee, "p2p_fee", {"deal": deal.id}, count_earned=False)
    session.add(Trade(
        buyer_id=deal.buyer_id, seller_id=deal.seller_id,
        price_micro=deal.price_uzs, amount_coins=deal.amount_coins, taker_side="buy",
    ))
    deal.escrow_coins = 0
    deal.status = "completed"
    deal.completed_at = utcnow()
    await _sys(session, deal_id, f"Seller released {payout} Coin to the buyer. Deal complete ✅")
    await _notify(deal.buyer_id, f"✅ Deal complete — you received {payout} Coin.")
    return {"status": deal.status, "coins": user.coins}


async def reject(session: AsyncSession, user: User, deal_id: int) -> dict:
    """Продавец «не получил деньги» — сделка остаётся, покупателя дёргаем."""
    deal = await _guard(session, user, deal_id)
    if user.id != deal.seller_id:
        raise GameError("not_seller", "Only the seller can do this")
    if deal.status != "paid":
        raise GameError("bad_state", "Buyer hasn't marked payment yet")
    await _sys(session, deal_id,
               "Seller says the money hasn't arrived. Buyer — resend the payment, or open a dispute.")
    await _notify(deal.buyer_id, "⚠️ Seller hasn't received the money. Resend or open a dispute.")
    return {"status": deal.status}


async def cancel(session: AsyncSession, user: User, deal_id: int) -> dict:
    deal = await _guard(session, user, deal_id)
    if deal.status == "cancelled":
        return {"status": deal.status}
    # до оплаты отменить может любая сторона; после оплаты — нельзя (только спор)
    if deal.status != "pending_payment":
        raise GameError("bad_state", "Can't cancel after payment — use dispute")
    deal.status = "cancelled"
    ad = await session.get(Ad, deal.ad_id)
    if ad:
        ad.remaining_coins += deal.escrow_coins
    deal.escrow_coins = 0
    who = "Seller" if user.id == deal.seller_id else "Buyer"
    await _sys(session, deal_id, f"{who} cancelled the deal — coins returned to the ad.")
    other = deal.seller_id if user.id == deal.buyer_id else deal.buyer_id
    await _notify(other, "❌ The P2P deal was cancelled.")
    return {"status": deal.status}


async def open_dispute(session: AsyncSession, user: User, deal_id: int) -> dict:
    deal = await _guard(session, user, deal_id)
    if deal.status in ("completed", "cancelled", "resolved"):
        raise GameError("bad_state", "Deal is already closed")
    deal.status = "disputed"
    deal.disputed_at = utcnow()
    for uid in (deal.buyer_id, deal.seller_id):
        u = await session.get(User, uid)
        if u:
            u.frozen = True
    await _sys(session, deal_id,
               "🚩 Dispute opened. Both accounts are frozen. An admin will join to resolve this.")
    await _notify(deal.buyer_id, "🚩 Dispute opened on your deal. Wait for an admin.")
    await _notify(deal.seller_id, "🚩 Dispute opened on your deal. Wait for an admin.")
    return {"status": deal.status}


# ---------------------------------------------------------------- чат


async def send_message(
    session: AsyncSession, user: User, deal_id: int, body: str,
    kind: str = "text", media_path: str | None = None,
) -> dict:
    deal = await session.get(Deal, deal_id)
    is_staff = user.is_operator or user.id == MARKET_MAKER_ID
    if not deal or (user.id not in (deal.buyer_id, deal.seller_id) and not is_staff):
        raise GameError("no_deal", "Deal not found")
    body = (body or "").strip()[:1024]
    if kind == "text" and not body:
        raise GameError("empty", "Empty message")
    msg = DealMessage(deal_id=deal_id, sender_id=user.id, kind=kind,
                      body=body, media_path=media_path)
    session.add(msg)
    await session.flush()
    other = None
    if user.id == deal.buyer_id:
        other = deal.seller_id
    elif user.id == deal.seller_id:
        other = deal.buyer_id
    if other:
        await _notify(other, "💬 New message in your P2P deal.")
    return {"id": msg.id}


async def messages(session: AsyncSession, user: User, deal_id: int, after: int = 0) -> dict:
    deal = await session.get(Deal, deal_id)
    is_staff = user.is_operator or user.id == MARKET_MAKER_ID
    if not deal or (user.id not in (deal.buyer_id, deal.seller_id) and not is_staff):
        raise GameError("no_deal", "Deal not found")
    rows = (
        (await session.execute(
            select(DealMessage).where(DealMessage.deal_id == deal_id, DealMessage.id > after)
            .order_by(DealMessage.id.asc())
        )).scalars().all()
    )
    ids = {m.sender_id for m in rows if m.sender_id}
    names = {}
    if ids:
        for u in (await session.execute(select(User).where(User.id.in_(ids)))).scalars().all():
            names[u.id] = _name(u, u.id)
    return {"items": [{
        "id": m.id, "sender": m.sender_id, "kind": m.kind, "body": m.body,
        "media": ("/media/" + m.media_path) if m.media_path else None,
        "name": names.get(m.sender_id, "Admin" if m.sender_id == 0 else f"Player {m.sender_id}"),
        "mine": m.sender_id == user.id, "t": ts(m.created_at),
    } for m in rows]}


# ---------------------------------------------------------------- вид сделки


def _actions(deal: Deal, uid: int) -> list[str]:
    """Доступные кнопки по роли и статусу."""
    is_buyer = uid == deal.buyer_id
    is_seller = uid == deal.seller_id
    a: list[str] = []
    if deal.status == "pending_payment":
        if is_buyer:
            a += ["paid", "cancel"]
        if is_seller:
            a += ["release", "cancel"]
    elif deal.status == "paid":
        if is_seller:
            a += ["release", "reject", "dispute"]
        if is_buyer:
            a += ["dispute"]
    return a


async def deal_view(session: AsyncSession, user: User, deal_id: int) -> dict:
    deal = await session.get(Deal, deal_id)
    is_staff = user.is_operator or user.id == MARKET_MAKER_ID
    if not deal or (user.id not in (deal.buyer_id, deal.seller_id) and not is_staff):
        raise GameError("no_deal", "Deal not found")
    await _expire_if_needed(session, deal)
    ad = await session.get(Ad, deal.ad_id)
    seller = await session.get(User, deal.seller_id)
    buyer = await session.get(User, deal.buyer_id)
    role = "seller" if user.id == deal.seller_id else ("buyer" if user.id == deal.buyer_id else "staff")
    return {
        "id": deal.id,
        "status": deal.status,
        "role": role,
        "amount": deal.amount_coins,
        "price": deal.price_uzs,
        "total": deal.total_uzs,
        "fee": deal.fee_coins,
        "payout": deal.escrow_coins - deal.fee_coins if deal.escrow_coins else deal.amount_coins - deal.fee_coins,
        "pay_method": PAY_METHODS.get(ad.pay_method, ad.pay_method) if ad else "",
        "pay_details": ad.pay_details if ad else "",
        "seller": _name(seller, deal.seller_id),
        "buyer": _name(buyer, deal.buyer_id),
        "counterparty": _name(buyer if role == "seller" else seller,
                              deal.buyer_id if role == "seller" else deal.seller_id),
        "deadline": ts(deal.pay_deadline),
        "actions": _actions(deal, user.id),
        "resolution": deal.resolution,
    }


async def my_deals(session: AsyncSession, user: User) -> list[dict]:
    rows = (
        (await session.execute(
            select(Deal).where(or_(Deal.buyer_id == user.id, Deal.seller_id == user.id))
            .order_by(Deal.id.desc()).limit(30)
        )).scalars().all()
    )
    out = []
    for d in rows:
        other_id = d.seller_id if d.buyer_id == user.id else d.buyer_id
        other = await session.get(User, other_id)
        out.append({
            "id": d.id, "status": d.status,
            "role": "buyer" if d.buyer_id == user.id else "seller",
            "amount": d.amount_coins, "price": d.price_uzs, "total": d.total_uzs,
            "counterparty": _name(other, other_id), "t": ts(d.created_at),
        })
    return out


# ---------------------------------------------------------------- админ / споры


async def list_disputes(session: AsyncSession) -> list[dict]:
    rows = (
        (await session.execute(
            select(Deal).where(Deal.status == "disputed").order_by(Deal.disputed_at.asc())
        )).scalars().all()
    )
    out = []
    for d in rows:
        buyer = await session.get(User, d.buyer_id)
        seller = await session.get(User, d.seller_id)
        out.append({
            "id": d.id, "amount": d.amount_coins, "total": d.total_uzs,
            "buyer": _name(buyer, d.buyer_id), "seller": _name(seller, d.seller_id),
            "t": ts(d.disputed_at),
        })
    return out


async def resolve(
    session: AsyncSession, deal_id: int, action: str,
    ban_buyer: bool = False, ban_seller: bool = False,
) -> dict:
    deal = await session.get(Deal, deal_id)
    if not deal or deal.status != "disputed":
        raise GameError("no_dispute", "No open dispute for this deal")
    if action not in ("release", "refund"):
        raise GameError("bad_action", "action must be release or refund")
    buyer = await session.get(User, deal.buyer_id)
    seller = await session.get(User, deal.seller_id)

    if action == "release":
        fee = deal.fee_coins
        payout = deal.escrow_coins - fee
        if buyer:
            await credit(session, buyer, payout, "p2p_release", {"deal": deal.id, "admin": True}, count_earned=False)
        if fee > 0:
            platform = await session.get(User, MARKET_MAKER_ID)
            if platform:
                await credit(session, platform, fee, "p2p_fee", {"deal": deal.id}, count_earned=False)
        session.add(Trade(buyer_id=deal.buyer_id, seller_id=deal.seller_id,
                          price_micro=deal.price_uzs, amount_coins=deal.amount_coins, taker_side="buy"))
    else:  # refund
        if seller:
            await credit(session, seller, deal.escrow_coins, "p2p_refund", {"deal": deal.id, "admin": True}, count_earned=False)

    deal.escrow_coins = 0
    deal.status = "resolved"
    deal.resolution = action
    deal.resolved_at = utcnow()

    # разморозка невиновных, бан по решению
    if buyer:
        buyer.frozen = ban_buyer
        buyer.banned = buyer.banned or ban_buyer
    if seller:
        seller.frozen = ban_seller
        seller.banned = seller.banned or ban_seller

    verdict = "released to buyer" if action == "release" else "refunded to seller"
    await _sys(session, deal_id, f"⚖️ Admin resolved the dispute: coins {verdict}.")
    await _notify(deal.buyer_id, f"⚖️ Dispute resolved: coins {verdict}.")
    await _notify(deal.seller_id, f"⚖️ Dispute resolved: coins {verdict}.")
    return {"status": deal.status, "resolution": action}
