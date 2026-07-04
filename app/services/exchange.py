"""P2P-биржа Coin↔USD. Цены назначают игроки внутри дневного коридора админа.

Эскроу: sell держит Coin, buy держит USD. Деньги только int (микро-доллы).
Маркетмейкер (user id 0) печатает fake-сделки, удерживая курс у официального.
"""

import random
from datetime import timedelta

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import (
    BAND_MAX_MULT,
    BAND_MIN_MULT,
    BASE_PRICE_MICRO,
    KEEPER_STEP,
    MARKET_MAKER_ID,
    MAX_OPEN_ORDERS,
    ORDER_MIN_COINS,
    ORDER_MIN_TOTAL_MICRO,
    USD_MICRO,
)
from app.core.clock import ts, utcnow
from app.core.fees import fee_amount, fee_rate
from app.db.models import MarketConfig, Order, Trade, User
from app.services import settings_store
from app.services.economy import credit, credit_usd
from app.services.errors import GameError


def _usd(micro: int) -> float:
    return round(micro / USD_MICRO, 6)


async def get_market_config(session: AsyncSession) -> MarketConfig:
    cfg = await session.get(MarketConfig, 1)
    if cfg is None:  # подстраховка, обычно сеется в init_db
        cfg = MarketConfig(
            id=1,
            official_micro=BASE_PRICE_MICRO,
            day_min_micro=int(BASE_PRICE_MICRO * BAND_MIN_MULT),
            day_max_micro=int(BASE_PRICE_MICRO * BAND_MAX_MULT),
        )
        session.add(cfg)
        await session.flush()
    return cfg


async def last_price_micro(session: AsyncSession) -> int:
    row = (
        await session.execute(
            select(Trade.price_micro).order_by(Trade.id.desc()).limit(1)
        )
    ).scalar_one_or_none()
    if row is not None:
        return row
    return (await get_market_config(session)).official_micro


def _check_frozen(user: User) -> None:
    if user.frozen:
        raise GameError("frozen", "Your wallet is frozen. Contact support.")


async def place_order(
    session: AsyncSession, user: User, side: str, price_micro: int, amount: int
) -> dict:
    _check_frozen(user)
    if side not in ("buy", "sell"):
        raise GameError("bad_side", "Side must be buy or sell")

    cfg = await get_market_config(session)
    # Дневной коридор НЕ блокирует ордер игрока — он лишь ориентир. Если игроки
    # уводят цену за коридор, маркетмейкер (keep_price_in_band) вернёт её обратно
    # плавными fake-сделками. Здесь только защита от абсурда (0 или 100x official).
    lo = max(1, cfg.official_micro // 100)
    hi = cfg.official_micro * 100
    if not (lo <= price_micro <= hi):
        raise GameError(
            "bad_price", "Price is out of sane range — check official rate"
        )
    if amount < ORDER_MIN_COINS:
        raise GameError("min_amount", f"Minimum order is {ORDER_MIN_COINS} Coin")
    if amount * price_micro < ORDER_MIN_TOTAL_MICRO:
        raise GameError(
            "min_total", f"Order total is below {_usd(ORDER_MIN_TOTAL_MICRO)} USD"
        )

    open_count = (
        await session.execute(
            select(func.count(Order.id)).where(
                Order.user_id == user.id, Order.status == "open"
            )
        )
    ).scalar_one()
    if open_count >= MAX_OPEN_ORDERS:
        raise GameError("too_many", f"Max {MAX_OPEN_ORDERS} open orders")

    # эскроу
    if side == "sell":
        if user.coins < amount:
            raise GameError("not_enough", "Not enough Coin")
        await credit(session, user, -amount, "exchange_hold", count_earned=False)
    else:
        cost = amount * price_micro
        if user.usd_micro < cost:
            raise GameError("not_enough", "Not enough USD")
        await credit_usd(session, user, -cost, "exchange_hold")

    order = Order(
        user_id=user.id,
        side=side,
        price_micro=price_micro,
        amount_coins=amount,
        filled_coins=0,
        status="open",
    )
    session.add(order)
    await session.flush()

    filled, avg = await _match(session, order, user)
    return {
        "order_id": order.id,
        "status": order.status,
        "filled": filled,
        "avg_price": _usd(avg) if avg else None,
        "coins": user.coins,
        "usd": _usd(user.usd_micro),
    }


async def _match(session: AsyncSession, order: Order, taker: User) -> tuple[int, int]:
    """Матчит новый ордер против стакана. Возвращает (заполнено, ср. цена micro)."""
    from app.services import settings_store

    _s = await settings_store.load(session)
    _rules = settings_store.vip_rules(_s)
    opp_side = "sell" if order.side == "buy" else "buy"
    if order.side == "buy":
        price_ok = Order.price_micro <= order.price_micro
        ordering = (Order.price_micro.asc(), Order.id.asc())
    else:
        price_ok = Order.price_micro >= order.price_micro
        ordering = (Order.price_micro.desc(), Order.id.asc())

    makers = (
        (
            await session.execute(
                select(Order)
                .where(
                    Order.status == "open",
                    Order.side == opp_side,
                    Order.user_id != taker.id,  # свои ордера не матчим
                    price_ok,
                )
                .order_by(*ordering)
            )
        )
        .scalars()
        .all()
    )

    remaining = order.amount_coins - order.filled_coins
    spent_micro = 0
    filled_total = 0

    for maker in makers:
        if remaining <= 0:
            break
        maker_user = await session.get(User, maker.user_id)
        if maker_user is None:
            continue
        take = min(remaining, maker.amount_coins - maker.filled_coins)
        trade_micro = take * maker.price_micro

        if order.side == "buy":
            buyer, seller = taker, maker_user
            buy_id, sell_id = order.id, maker.id
        else:
            buyer, seller = maker_user, taker
            buy_id, sell_id = maker.id, order.id

        # коины продавца уже в эскроу sell-ордера, USD покупателя — в его buy
        await credit(
            session, buyer, take, "trade_buy",
            {"price": maker.price_micro}, count_earned=False,
        )
        await credit_usd(session, seller, trade_micro, "trade_sell", {"amount": take})
        _mult = settings_store.discount_mult(_rules, seller.vip_tier)
        fee = fee_amount(trade_micro, "trade", seller.vip_tier, _mult)
        if fee > 0:
            await credit_usd(session, seller, -fee, "fee_trade")

        maker.filled_coins += take
        if maker.filled_coins >= maker.amount_coins:
            maker.status = "filled"
        order.filled_coins += take
        remaining -= take
        spent_micro += trade_micro
        filled_total += take

        session.add(
            Trade(
                buy_order_id=buy_id,
                sell_order_id=sell_id,
                buyer_id=buyer.id,
                seller_id=seller.id,
                price_micro=maker.price_micro,
                amount_coins=take,
                taker_side=order.side,
            )
        )

    if order.filled_coins >= order.amount_coins:
        order.status = "filled"

    # buy-тейкер купил дешевле своего лимита — вернуть разницу из холда
    if order.side == "buy" and filled_total > 0:
        refund = filled_total * order.price_micro - spent_micro
        if refund > 0:
            await credit_usd(session, taker, refund, "exchange_refund")

    avg = spent_micro // filled_total if filled_total else 0
    return filled_total, avg


async def cancel_order(session: AsyncSession, user: User, order_id: int) -> dict:
    order = await session.get(Order, order_id)
    if not order or order.user_id != user.id:
        raise GameError("no_order", "Order not found")
    if order.status != "open":
        raise GameError("not_open", "Order is not open")

    rest = order.amount_coins - order.filled_coins
    order.status = "cancelled"
    if rest > 0:
        if order.side == "sell":
            await credit(session, user, rest, "exchange_refund", count_earned=False)
        else:
            await credit_usd(session, user, rest * order.price_micro, "exchange_refund")
    return {"cancelled": order.id, "coins": user.coins, "usd": _usd(user.usd_micro)}


# ---------------------------------------------------------------- маркетмейкер


def _human_amount() -> int:
    """«Живой» объём: круглые числа (200, 350, 500…), не палевные 1753."""
    base = random.choice([50, 100, 150, 200, 250, 300, 350, 400, 500, 600, 750, 1000])
    # иногда чуть-чуть шума, но остаётся ровным (кратно 10)
    return base + random.choice([0, 0, 0, 10, 20, 50])


async def fake_trade(
    session: AsyncSession, price_micro: int, amount: int | None = None
) -> None:
    """Сделка маркетмейкера сам-с-собой: двигает last price, рисует график.

    Объёмы человечные и круглые, сторона случайна — выглядит как живые сделки.
    """
    session.add(
        Trade(
            buy_order_id=None,
            sell_order_id=None,
            buyer_id=MARKET_MAKER_ID,
            seller_id=MARKET_MAKER_ID,
            price_micro=max(1, price_micro),
            amount_coins=amount or _human_amount(),
            taker_side=random.choice(["buy", "sell"]),
        )
    )


async def keep_price_in_band(session: AsyncSession) -> bool:
    """Естественный маркетмейкинг: каждую минуту незаметно тянет цену к official.

    Не один рывок, а серия мелких сделок «сам с собой» с рандомным шагом,
    рандомным объёмом и небольшим джиттером цены — чтобы график выглядел живым
    и без подозрений. Чем дальше от коридора, тем агрессивнее шаг.
    """
    cfg = await get_market_config(session)
    last = await last_price_micro(session)
    target = cfg.official_micro
    if target <= 0:
        return False

    gap = target - last
    rel = abs(gap) / target

    # у самой цели — иногда чуть-чуть шевелим для «жизни», но не тащим
    if rel <= 0.015:
        if random.random() < 0.5:
            jitter = int(target * random.uniform(-0.006, 0.006))
            await fake_trade(session, target + jitter)
            return True
        return False

    # вне коридора — тянем сильнее, внутри — мягко
    out_of_band = last < cfg.day_min_micro or last > cfg.day_max_micro
    frac = random.uniform(0.30, 0.55) if out_of_band else random.uniform(0.12, 0.30)
    step = int(gap * frac)
    if step == 0:
        step = 1 if gap > 0 else -1
    # джиттер, чтобы не было идеально прямой линии
    new_price = last + step + int(target * random.uniform(-0.004, 0.004))
    await fake_trade(session, max(1, new_price))
    return True


async def rate_usd(session: AsyncSession) -> float:
    """Текущий курс: сколько USD стоит 1 Coin (по последней цене рынка)."""
    return (await last_price_micro(session)) / USD_MICRO


# ---------------------------------------------------------------- график / вид

# таймфрейм → длина свечи в секундах (как у TradingView)
_TF_SEC = {
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
}
CANDLE_LIMIT = 80  # сколько последних свечей отдаём


async def candles(session: AsyncSession, tf: str) -> list[dict]:
    """OHLC-свечи фиксированной длины (бакеты по секундам) для трейдерского графика.

    Бакет = floor(epoch / sec) * sec. open/close — первая/последняя сделка в бакете,
    high/low — max/min. Возвращает последние CANDLE_LIMIT свечей: [{t, o, h, l, c, v}],
    t — эпоха начала свечи (сек, UTC).
    """
    sec = _TF_SEC.get(tf, 3600)
    epoch = cast(func.strftime("%s", Trade.created_at), Integer)
    bstart = (epoch - epoch % sec).label("bstart")  # начало свечи (epoch, целое)
    q = (
        select(
            bstart,
            func.min(Trade.price_micro),
            func.max(Trade.price_micro),
            func.min(Trade.id),
            func.max(Trade.id),
            func.coalesce(func.sum(Trade.amount_coins), 0),
        )
        .group_by("bstart")
        .order_by(func.min(Trade.id).desc())
        .limit(CANDLE_LIMIT)
    )
    rows = list(reversed((await session.execute(q)).all()))

    # цены первой/последней сделки в бакете (open/close)
    prices: dict[int, int] = {}
    ids: set[int] = set()
    for _, _, _, first_id, last_id, _ in rows:
        ids.add(first_id)
        ids.add(last_id)
    if ids:
        for tid, pm in (
            await session.execute(
                select(Trade.id, Trade.price_micro).where(Trade.id.in_(ids))
            )
        ).all():
            prices[tid] = pm

    out = []
    for bstart, lo, hi, first_id, last_id, vol in rows:
        o = prices.get(first_id, lo)
        c = prices.get(last_id, hi)
        out.append(
            {
                "t": int(bstart),
                "o": round(o / USD_MICRO, 6),
                "h": round(hi / USD_MICRO, 6),
                "l": round(lo / USD_MICRO, 6),
                "c": round(c / USD_MICRO, 6),
                "v": int(vol),
            }
        )
    if not out:
        cfg = await get_market_config(session)
        p = _usd(cfg.official_micro)
        out = [{"t": 0, "o": p, "h": p, "l": p, "c": p, "v": 0}]
    return out


async def orders_page(
    session: AsyncSession, side: str, viewer_id: int, offset: int = 0, limit: int = 12
) -> dict:
    """Индивидуальные открытые ордера одной стороны (для кликабельного стакана).

    buy — лучшие цены сверху (desc), sell — дешевле сверху (asc). Чужие ордера,
    свои показываем в «My orders». Возвращает {items, total, has_more}.
    """
    rest = Order.amount_coins - Order.filled_coins
    base = (
        select(Order, User)
        .join(User, Order.user_id == User.id)
        .where(
            Order.status == "open",
            Order.side == side,
            Order.user_id != viewer_id,
            Order.user_id != MARKET_MAKER_ID,
        )
    )
    total = (
        await session.execute(
            select(func.count(Order.id)).where(
                Order.status == "open",
                Order.side == side,
                Order.user_id != viewer_id,
                Order.user_id != MARKET_MAKER_ID,
            )
        )
    ).scalar_one()
    order_by = Order.price_micro.desc() if side == "buy" else Order.price_micro.asc()
    rows = (
        await session.execute(
            base.order_by(order_by, Order.id.asc()).offset(offset).limit(limit)
        )
    ).all()
    items = [
        {
            "id": o.id,
            "side": o.side,
            "price": _usd(o.price_micro),
            "amount": o.amount_coins - o.filled_coins,
            "name": u.first_name or u.username or f"Player {u.id}",
        }
        for o, u in rows
    ]
    return {"items": items, "total": int(total), "has_more": offset + limit < total}


async def market_view(session: AsyncSession, user: User) -> dict:
    cfg = await get_market_config(session)
    last = await last_price_micro(session)
    change = (
        (last - cfg.official_micro) / cfg.official_micro * 100
        if cfg.official_micro
        else 0.0
    )

    trades = (
        (await session.execute(select(Trade).order_by(Trade.id.desc()).limit(10)))
        .scalars()
        .all()
    )
    my_orders = (
        (
            await session.execute(
                select(Order)
                .where(Order.user_id == user.id, Order.status == "open")
                .order_by(Order.id.desc())
            )
        )
        .scalars()
        .all()
    )
    holders = (
        (
            await session.execute(
                select(User)
                .where(User.banned.is_(False), User.id != MARKET_MAKER_ID)
                .order_by(User.coins.desc())
                .limit(7)
            )
        )
        .scalars()
        .all()
    )
    s = await settings_store.load(session)
    mult = settings_store.discount_mult(settings_store.vip_rules(s), user.vip_tier)
    return {
        "price": _usd(last),
        "change_pct": round(change, 2),
        "coins": user.coins,
        "usd": _usd(user.usd_micro),
        "min_order": ORDER_MIN_COINS,
        "fee_pct": round(fee_rate("trade", user.vip_tier, mult) * 100, 2),
        "frozen": user.frozen,
        # кликабельный стакан — индивидуальные ордера, первая страница
        "orders_buy": await orders_page(session, "buy", user.id),
        "orders_sell": await orders_page(session, "sell", user.id),
        "my_orders": [
            {
                "id": o.id,
                "side": o.side,
                "price": _usd(o.price_micro),
                "amount": o.amount_coins,
                "filled": o.filled_coins,
            }
            for o in my_orders
        ],
        "trades": [
            {
                "t": ts(t.created_at),
                "price": _usd(t.price_micro),
                "amount": t.amount_coins,
                "side": t.taker_side,
                "mine": user.id in (t.buyer_id, t.seller_id),
            }
            for t in trades
        ],
        "holders": [
            {
                "name": h.first_name or h.username or f"Player {h.id}",
                "coins": h.coins,
                "me": h.id == user.id,
            }
            for h in holders
        ],
    }
