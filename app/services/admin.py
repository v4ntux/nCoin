"""Админ-сервис: статистика, мониторинг юзеров, заявки, ивенты, управление курсом."""

from datetime import timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import MARKET_MAKER_ID, USD_MICRO
from app.core.clock import ts, utcnow
from app.core.vip import tier_name
from app.db.models import (
    CustomTask,
    Deal,
    DepositRequest,
    Event,
    LedgerEntry,
    News,
    Trade,
    User,
    WithdrawRequest,
)
from app.services import market
from app.services.economy import credit, credit_usd
from app.services.errors import GameError


def _usd(micro: int) -> float:
    return round(micro / USD_MICRO, 6)


def _user_row(u: User) -> dict:
    return {
        "id": u.id,
        "name": u.first_name or u.username or f"Player {u.id}",
        "username": u.username,
        "level": u.level,
        "vip": u.vip_tier,
        "vip_name": tier_name(u.vip_tier),
        "coins": u.coins,
        "usd": _usd(u.usd_micro),
        "total_earned": u.total_earned,
        "ref_count": u.ref_count,
        "banned": u.banned,
        "frozen": u.frozen,
        "is_operator": u.is_operator,
        "created_at": ts(u.created_at),
        "last_seen_at": ts(u.last_seen_at),
    }


# ---------------------------------------------------------------- дашборд


async def stats(session: AsyncSession) -> dict:
    day_ago = utcnow() - timedelta(days=1)
    real = User.id != MARKET_MAKER_ID

    async def count_users(*conds) -> int:
        return (
            await session.execute(select(func.count(User.id)).where(real, *conds))
        ).scalar_one()

    users_total = await count_users()
    users_new = await count_users(User.created_at >= day_ago)
    users_active = await count_users(User.last_seen_at >= day_ago)
    coins_supply = (
        await session.execute(
            select(func.coalesce(func.sum(User.coins), 0)).where(real)
        )
    ).scalar_one()
    usd_supply = (
        await session.execute(
            select(func.coalesce(func.sum(User.usd_micro), 0)).where(real)
        )
    ).scalar_one()
    trades_24h, volume_24h = (
        await session.execute(
            select(
                func.count(Trade.id),
                func.coalesce(func.sum(Trade.amount_coins), 0),
            ).where(Trade.created_at >= day_ago)
        )
    ).one()
    pending_w = (
        await session.execute(
            select(func.count(WithdrawRequest.id)).where(
                WithdrawRequest.status == "pending"
            )
        )
    ).scalar_one()
    pending_d = (
        await session.execute(
            select(func.count(DepositRequest.id)).where(
                DepositRequest.status == "pending"
            )
        )
    ).scalar_one()
    open_disputes = (
        await session.execute(
            select(func.count(Deal.id)).where(Deal.status == "disputed")
        )
    ).scalar_one()

    price = await market.price_uzs(session)
    official = await market.official_price_uzs(session)
    top = (
        (
            await session.execute(
                select(User)
                .where(real, User.banned.is_(False))
                .order_by(User.total_earned.desc())
                .limit(5)
            )
        )
        .scalars()
        .all()
    )
    return {
        "users": {
            "total": users_total,
            "new_24h": users_new,
            "active_24h": users_active,
        },
        "supply": {"coins": int(coins_supply), "usd": _usd(int(usd_supply))},
        "market": {
            "price": price,
            "official": official,
            "trades_24h": int(trades_24h),
            "volume_24h": int(volume_24h),
            "open_disputes": int(open_disputes),
        },
        "pending": {"withdraws": pending_w, "deposits": pending_d},
        "top": [_user_row(u) for u in top],
    }


async def chart(session: AsyncSession, kind: str, tf: str = "month") -> list[dict]:
    """3 типа графиков: цена (свечи→линия close), рост юзеров, объём торгов."""
    if kind == "price":
        mtf = {"day": "1h", "month": "1d"}.get(tf, "1d")
        return [{"t": c["t"], "v": c["c"]} for c in await market.candles(session, mtf)]

    span = {"day": timedelta(days=1), "month": timedelta(days=30)}.get(tf)
    if kind == "users":
        bucket = func.strftime("%Y-%m-%d", User.created_at).label("bucket")
        q = (
            select(bucket, func.count(User.id))
            .where(User.id != MARKET_MAKER_ID)
            .group_by("bucket")
            .order_by("bucket")
        )
        if span is not None:
            q = q.where(User.created_at >= utcnow() - span)
    elif kind == "volume":
        bucket = func.strftime("%Y-%m-%d", Trade.created_at).label("bucket")
        q = (
            select(bucket, func.coalesce(func.sum(Trade.amount_coins), 0))
            .group_by("bucket")
            .order_by("bucket")
        )
        if span is not None:
            q = q.where(Trade.created_at >= utcnow() - span)
    else:
        raise GameError("bad_chart", "kind must be price | users | volume")
    rows = (await session.execute(q)).all()
    return [{"t": b, "v": int(v)} for b, v in rows]


# ---------------------------------------------------------------- юзеры


async def users_list(
    session: AsyncSession, q: str = "", offset: int = 0, limit: int = 50
) -> dict:
    conds = [User.id != MARKET_MAKER_ID]
    q = (q or "").strip().lstrip("@")
    if q.isdigit():
        conds.append(User.id == int(q))
    elif q:
        like = f"%{q.lower()}%"
        conds.append(
            or_(
                func.lower(func.coalesce(User.username, "")).like(like),
                func.lower(User.first_name).like(like),
            )
        )
    total = (
        await session.execute(select(func.count(User.id)).where(*conds))
    ).scalar_one()
    rows = (
        (
            await session.execute(
                select(User)
                .where(*conds)
                .order_by(User.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    return {"total": total, "items": [_user_row(u) for u in rows]}


async def user_detail(session: AsyncSession, uid: int) -> dict:
    u = await session.get(User, uid)
    if not u:
        raise GameError("no_user", "User not found")
    sources = (
        await session.execute(
            select(
                LedgerEntry.currency,
                LedgerEntry.reason,
                func.sum(LedgerEntry.amount),
                func.count(LedgerEntry.id),
            )
            .where(LedgerEntry.user_id == uid)
            .group_by(LedgerEntry.currency, LedgerEntry.reason)
            .order_by(func.sum(LedgerEntry.amount).desc())
        )
    ).all()
    recent = (
        (
            await session.execute(
                select(LedgerEntry)
                .where(LedgerEntry.user_id == uid)
                .order_by(LedgerEntry.id.desc())
                .limit(15)
            )
        )
        .scalars()
        .all()
    )
    return {
        **_user_row(u),
        "sources": [
            {
                "currency": c,
                "reason": r,
                "total": int(s) if c == "coin" else _usd(int(s)),
                "ops": int(n),
            }
            for c, r, s, n in sources
        ],
        "recent": [
            {
                "t": ts(entry.created_at),
                "currency": entry.currency,
                "reason": entry.reason,
                "amount": entry.amount
                if entry.currency == "coin"
                else _usd(entry.amount),
            }
            for entry in recent
        ],
    }


async def user_action(
    session: AsyncSession, uid: int, action: str, value: float | None = None
) -> dict:
    from app.bot.instance import safe_send

    u = await session.get(User, uid)
    if not u or u.id == MARKET_MAKER_ID:
        raise GameError("no_user", "User not found")

    if action == "ban":
        u.banned = True
    elif action == "unban":
        u.banned = False
    elif action == "freeze":
        u.frozen = True
        await safe_send(uid, "🧊 Your wallet was frozen by admin.")
    elif action == "unfreeze":
        u.frozen = False
        await safe_send(uid, "✅ Your wallet is active again.")
    elif action == "operator":
        u.is_operator = True
        await safe_send(uid, "🛡 You are now a P2P dispute operator.")
    elif action == "unoperator":
        u.is_operator = False
    elif action == "vip":
        tier = int(value or 0)
        if tier not in (0, 1, 2, 3):
            raise GameError("bad_tier", "Tier must be 0-3")
        u.vip_tier = tier
        await safe_send(uid, f"👑 Your plan is now <b>{tier_name(tier)}</b>!")
    elif action == "give":
        amount = int(value or 0)
        if amount == 0:
            raise GameError("bad_amount", "Amount must not be 0")
        await credit(session, u, amount, "admin_give", count_earned=False)
        await safe_send(
            uid, f"🎁 Admin sent you <b>{amount:,} Coin</b>".replace(",", " ")
        )
    elif action == "give_usd":
        micro = round(float(value or 0) * USD_MICRO)
        if micro == 0:
            raise GameError("bad_amount", "Amount must not be 0")
        await credit_usd(session, u, micro, "admin_give")
        await safe_send(uid, f"🎁 Admin sent you <b>{micro / USD_MICRO:g} USD</b>")
    elif action == "set_coins":
        target = int(value or 0)
        delta = target - u.coins
        if delta:
            await credit(session, u, delta, "admin_set", count_earned=False)
    elif action == "set_usd":
        target = round(float(value or 0) * USD_MICRO)
        delta = target - u.usd_micro
        if delta:
            await credit_usd(session, u, delta, "admin_set")
    else:
        raise GameError("bad_action", "Unknown action")
    return _user_row(u)


# ---------------------------------------------------------------- заявки


async def requests_view(session: AsyncSession) -> dict:
    withdraws = (
        await session.execute(
            select(WithdrawRequest, User)
            .join(User, WithdrawRequest.user_id == User.id)
            .where(WithdrawRequest.status == "pending")
            .order_by(WithdrawRequest.id.desc())
        )
    ).all()
    deposits = (
        await session.execute(
            select(DepositRequest, User)
            .join(User, DepositRequest.user_id == User.id)
            .where(DepositRequest.status == "pending")
            .order_by(DepositRequest.id.desc())
        )
    ).all()
    return {
        "withdraws": [
            {
                "id": r.id,
                "user_id": u.id,
                "name": u.first_name or u.username or u.id,
                "vip_name": tier_name(u.vip_tier),
                "amount_usd": r.amount_usd,
                "fee_usd": _usd(r.fee_micro),
                "created_at": ts(r.created_at),
            }
            for r, u in withdraws
        ],
        "deposits": [
            {
                "id": r.id,
                "user_id": u.id,
                "name": u.first_name or u.username or u.id,
                "tier": r.tier,
                "tier_name": tier_name(r.tier),
                "created_at": ts(r.created_at),
            }
            for r, u in deposits
        ],
    }


async def decide_withdraw(session: AsyncSession, req_id: int, approve: bool) -> str:
    from app.bot.instance import safe_send

    req = await session.get(WithdrawRequest, req_id)
    if not req or req.status != "pending":
        raise GameError("processed", "Already processed")
    user = await session.get(User, req.user_id)

    if approve:
        req.status = "approved"
        note = f"✅ Withdraw #{req.id} approved: {req.amount_usd} USD"
        await safe_send(
            req.user_id,
            f"✅ Withdraw <b>{req.amount_usd} USD</b> approved! "
            f"Admin will contact you for payment.",
        )
    else:
        req.status = "declined"
        if user:
            await credit_usd(
                session,
                user,
                req.amount_micro + req.fee_micro,
                "withdraw_refund",
                {"request": req.id},
            )
        note = f"❌ Withdraw #{req.id} declined, USD refunded"
        await safe_send(
            req.user_id,
            f"❌ Withdraw <b>{req.amount_usd} USD</b> declined. Money refunded.",
        )
    req.processed_at = utcnow()
    return note


async def decide_deposit(session: AsyncSession, req_id: int, approve: bool) -> str:
    from app.bot.instance import safe_send

    req = await session.get(DepositRequest, req_id)
    if not req or req.status != "pending":
        raise GameError("processed", "Already processed")
    user = await session.get(User, req.user_id)

    if approve and user:
        req.status = "approved"
        user.vip_tier = max(user.vip_tier, req.tier)
        note = f"✅ Deposit #{req.id}: {user.id} → {tier_name(req.tier)}"
        await safe_send(
            req.user_id, f"👑 Your plan is now <b>{tier_name(req.tier)}</b>!"
        )
    else:
        req.status = "declined"
        note = f"❌ Deposit #{req.id} declined"
        await safe_send(req.user_id, "❌ Deposit request declined.")
    req.processed_at = utcnow()
    return note


# ---------------------------------------------------------------- ивенты


def _event_row(e: Event) -> dict:
    now = utcnow()
    return {
        "id": e.id,
        "title": e.title,
        "text": e.text,
        "reward": e.reward,
        "ends_at": ts(e.ends_at),
        "ends_in": max(0, int((e.ends_at - now).total_seconds())),
        "max_claims": e.max_claims,
        "claims": e.claims,
        "active": e.active,
    }


async def events_admin_list(session: AsyncSession) -> list[dict]:
    rows = (
        (await session.execute(select(Event).order_by(Event.id.desc()).limit(20)))
        .scalars()
        .all()
    )
    return [_event_row(e) for e in rows]


async def event_create(
    session: AsyncSession,
    title: str,
    text: str,
    reward: int,
    minutes: int,
    max_claims: int,
) -> dict:
    ev = Event(
        title=title.strip()[:64],
        text=text.strip()[:256],
        reward=reward,
        ends_at=utcnow() + timedelta(minutes=minutes),
        max_claims=max_claims,
        claims=0,
        active=True,
    )
    session.add(ev)
    await session.flush()
    return _event_row(ev)


async def event_toggle(session: AsyncSession, event_id: int, active: bool) -> dict:
    ev = await session.get(Event, event_id)
    if not ev:
        raise GameError("no_event", "Event not found")
    ev.active = active
    return _event_row(ev)


# ---------------------------------------------------------------- рынок


async def market_admin_view(session: AsyncSession) -> dict:
    cfg = await market.get_config(session)
    return {
        "official": await market.official_price_uzs(session),
        "target": cfg.target_uzs,
        "last": await market.price_uzs(session),
        "updated_at": ts(cfg.updated_at),
    }


async def market_set(session: AsyncSession, target_uzs: float) -> dict:
    """Админ задаёт цель курса в UZS. Цена плавно доедет за 5 минут (без fake-ботов)."""
    target = round(float(target_uzs))
    if target <= 0:
        raise GameError("bad_price", "Price must be positive")
    await market.set_official_price(session, target)
    return await market_admin_view(session)


# ---------------------------------------------------------------- задания


def _custom_task_row(ct: CustomTask) -> dict:
    return {
        "id": ct.id,
        "title": ct.title,
        "url": ct.url,
        "reward": ct.reward,
        "xp": ct.xp,
        "kind": ct.kind,
        "icon": ct.icon,
        "active": ct.active,
        "claims": ct.claims,
    }


async def tasks_admin_list(session: AsyncSession) -> list[dict]:
    rows = (
        (await session.execute(select(CustomTask).order_by(CustomTask.sort, CustomTask.id)))
        .scalars()
        .all()
    )
    return [_custom_task_row(ct) for ct in rows]


_TASK_ICON = {"channel": "news", "social": "users", "link": "news"}


async def task_create(
    session: AsyncSession, title: str, url: str, reward: int, xp: int, kind: str
) -> dict:
    kind = kind if kind in ("channel", "social", "link") else "link"
    ct = CustomTask(
        title=title.strip()[:64],
        url=url.strip()[:256],
        reward=reward,
        xp=xp,
        kind=kind,
        icon=_TASK_ICON[kind],
        active=True,
    )
    session.add(ct)
    await session.flush()
    return _custom_task_row(ct)


async def task_toggle(session: AsyncSession, task_id: int, active: bool) -> dict:
    ct = await session.get(CustomTask, task_id)
    if not ct:
        raise GameError("no_task", "Task not found")
    ct.active = active
    return _custom_task_row(ct)


async def task_delete(session: AsyncSession, task_id: int) -> dict:
    ct = await session.get(CustomTask, task_id)
    if ct:
        await session.delete(ct)
    return {"deleted": task_id}


# ---------------------------------------------------------------- news


def _news_row(n: News) -> dict:
    return {
        "id": n.id,
        "tag": n.tag,
        "title": n.title,
        "text": n.text,
        "active": n.active,
        "sort": n.sort,
    }


async def news_admin_list(session: AsyncSession) -> list[dict]:
    rows = (
        (await session.execute(select(News).order_by(News.sort, News.id.desc())))
        .scalars()
        .all()
    )
    return [_news_row(n) for n in rows]


async def news_create(
    session: AsyncSession, tag: str, title: str, text: str, sort: int = 0
) -> dict:
    n = News(
        tag=(tag or "NEW").strip()[:12].upper(),
        title=title.strip()[:64],
        text=text.strip()[:256],
        sort=sort,
        active=True,
    )
    session.add(n)
    await session.flush()
    return _news_row(n)


async def news_toggle(session: AsyncSession, news_id: int, active: bool) -> dict:
    n = await session.get(News, news_id)
    if not n:
        raise GameError("no_news", "News not found")
    n.active = active
    return _news_row(n)


async def news_delete(session: AsyncSession, news_id: int) -> dict:
    n = await session.get(News, news_id)
    if n:
        await session.delete(n)
    return {"deleted": news_id}


# ---------------------------------------------------------------- settings (support + VIP)


async def settings_view(session: AsyncSession) -> dict:
    from app.services import settings_store

    s = await settings_store.load(session)
    rules = settings_store.vip_rules(s)
    return {
        "support_tg": s.support_tg,
        "support_email": s.support_email,
        "support_text": s.support_text,
        "vip": [rules[t] for t in sorted(rules) if t > 0],
    }


async def settings_save(
    session: AsyncSession,
    support_tg: str,
    support_email: str,
    support_text: str,
    vip: list[dict],
) -> dict:
    from app.services import settings_store

    s = await settings_store.load(session)
    s.support_tg = (support_tg or "").strip()[:64]
    s.support_email = (support_email or "").strip()[:64]
    s.support_text = (support_text or "").strip()[:256]
    # vip: [{tier, price, discount, withdraws}, ...]
    over: dict[str, dict] = {}
    for row in vip or []:
        tier = int(row.get("tier", 0))
        if tier in (1, 2, 3):
            over[str(tier)] = {
                "price": float(row.get("price", 0)),
                "discount": int(row.get("discount", 0)),
                "withdraws": int(row.get("withdraws", 0)),
            }
    s.vip = over
    return await settings_view(session)
