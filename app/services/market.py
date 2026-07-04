"""Курс коина в UZS и график.

Никаких fake-ботов. Официальную цену задаёт админ; отображаемая цена плавно
доезжает до цели за PRICE_GLIDE_SEC (5 минут). Свечи строятся ТОЛЬКО из реальных
завершённых P2P-сделок (таблица Trade, price_micro хранит цену в UZS).
"""

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import DEFAULT_PRICE_UZS, PRICE_GLIDE_SEC
from app.core.clock import ts, utcnow
from app.db.models import MarketConfig, Trade

_TF_SEC = {"15m": 900, "30m": 1800, "1h": 3600, "1d": 86400, "1w": 604800, "1mo": 2592000}
CANDLE_LIMIT = 120


def tf_seconds(tf: str) -> int:
    return _TF_SEC.get(tf, 3600)


async def get_config(session: AsyncSession) -> MarketConfig:
    cfg = await session.get(MarketConfig, 1)
    if cfg is None:
        cfg = MarketConfig(
            id=1, base_uzs=DEFAULT_PRICE_UZS, target_uzs=DEFAULT_PRICE_UZS
        )
        session.add(cfg)
        await session.flush()
    return cfg


def _glide_price(cfg: MarketConfig) -> int:
    """Текущая цена с учётом плавного доезда к цели админа."""
    base = cfg.base_uzs or DEFAULT_PRICE_UZS
    target = cfg.target_uzs or base
    if target == base or cfg.set_at is None:
        return target or base
    elapsed = (utcnow() - cfg.set_at).total_seconds()
    frac = max(0.0, min(1.0, elapsed / PRICE_GLIDE_SEC))
    return round(base + (target - base) * frac)


async def price_uzs(session: AsyncSession) -> int:
    """Текущий курс: сколько UZS стоит 1 Coin.

    Приоритет — последняя реальная сделка, иначе плавная официальная цена.
    """
    last = (
        await session.execute(select(Trade.price_micro).order_by(Trade.id.desc()).limit(1))
    ).scalar_one_or_none()
    if last is not None:
        return int(last)
    return _glide_price(await get_config(session))


async def official_price_uzs(session: AsyncSession) -> int:
    return _glide_price(await get_config(session))


async def set_official_price(session: AsyncSession, target: int) -> None:
    """Админ ставит цель — цена стартует с текущей и едет к target за 5 минут."""
    cfg = await get_config(session)
    cfg.base_uzs = _glide_price(cfg)
    cfg.target_uzs = max(1, int(target))
    cfg.set_at = utcnow()
    cfg.updated_at = utcnow()


async def change_pct(session: AsyncSession) -> float:
    """Изменение текущей цены к цене ~24ч назад (по сделкам), иначе 0."""
    now = int(ts(utcnow()))
    epoch = cast(func.strftime("%s", Trade.created_at), Integer)
    ago = (
        await session.execute(
            select(Trade.price_micro).where(epoch <= now - 86400).order_by(Trade.id.desc()).limit(1)
        )
    ).scalar_one_or_none()
    cur = await price_uzs(session)
    if ago and ago > 0:
        return round((cur - ago) / ago * 100, 2)
    first = (
        await session.execute(select(Trade.price_micro).order_by(Trade.id.asc()).limit(1))
    ).scalar_one_or_none()
    if first and first > 0:
        return round((cur - first) / first * 100, 2)
    return 0.0


async def candles(session: AsyncSession, tf: str) -> list[dict]:
    """Непрерывные OHLC-свечи из реальных сделок (цена в UZS, целые).

    Пустые интервалы заполняются плоской свечой по предыдущему close. Если сделок
    нет вовсе — одна плоская свеча по официальной цене (график не пустой).
    """
    sec = tf_seconds(tf)
    now_ep = int(ts(utcnow()))
    range_end = now_ep - now_ep % sec
    range_start = range_end - (CANDLE_LIMIT - 1) * sec

    epoch = cast(func.strftime("%s", Trade.created_at), Integer)
    bstart = (epoch - epoch % sec).label("bstart")
    rows = (
        await session.execute(
            select(
                bstart,
                func.min(Trade.price_micro),
                func.max(Trade.price_micro),
                func.min(Trade.id),
                func.max(Trade.id),
                func.coalesce(func.sum(Trade.amount_coins), 0),
            )
            .where(epoch >= range_start)
            .group_by("bstart")
        )
    ).all()
    by_start = {int(b): (lo, hi, fid, lid, vol) for b, lo, hi, fid, lid, vol in rows}

    ids: set[int] = set()
    for _, _, fid, lid, _ in by_start.values():
        ids.add(fid)
        ids.add(lid)
    prices: dict[int, int] = {}
    if ids:
        for tid, pm in (
            await session.execute(select(Trade.id, Trade.price_micro).where(Trade.id.in_(ids)))
        ).all():
            prices[tid] = int(pm)

    prev_close: int | None = None
    older = (
        await session.execute(
            select(Trade.price_micro).where(epoch < range_start).order_by(Trade.id.desc()).limit(1)
        )
    ).scalar_one_or_none()
    if older is not None:
        prev_close = int(older)

    if by_start:
        start = range_start if prev_close is not None else min(by_start)
    elif prev_close is not None:
        start = range_end - 20 * sec
    else:
        p = await official_price_uzs(session)
        return [{"t": range_end, "o": p, "h": p, "l": p, "c": p, "v": 0}]

    out: list[dict] = []
    t = start
    while t <= range_end:
        if t in by_start:
            lo, hi, fid, lid, vol = by_start[t]
            o = prices.get(fid, int(lo))
            c = prices.get(lid, int(hi))
            out.append({"t": t, "o": o, "h": int(hi), "l": int(lo), "c": c, "v": int(vol)})
            prev_close = c
        elif prev_close is not None:
            out.append({"t": t, "o": prev_close, "h": prev_close, "l": prev_close,
                        "c": prev_close, "v": 0})
        t += sec
    return out[-CANDLE_LIMIT:]


async def recent_trades(session: AsyncSession, limit: int = 12) -> list[dict]:
    rows = (
        (await session.execute(select(Trade).order_by(Trade.id.desc()).limit(limit)))
        .scalars()
        .all()
    )
    return [
        {
            "t": ts(tr.created_at),
            "price": int(tr.price_micro),
            "amount": int(tr.amount_coins),
            "total": int(tr.price_micro) * int(tr.amount_coins),
            "side": tr.taker_side,
        }
        for tr in rows
    ]
