from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.constants import BASE_ENERGY_MAX
from app.core.clock import utcnow


class Base(DeclarativeBase):
    pass


class User(Base):
    """id = telegram id. Балансы денормализованы, источник правды — ledger."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    username: Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str] = mapped_column(String(128), default="")

    coins: Mapped[int] = mapped_column(BigInteger, default=0)
    total_earned: Mapped[int] = mapped_column(BigInteger, default=0)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)

    # кликер: energy/heat актуальны на момент synced_at, дальше — ленивый пересчёт
    energy: Mapped[float] = mapped_column(Float, default=float(BASE_ENERGY_MAX))
    heat: Mapped[float] = mapped_column(Float, default=0.0)
    combo: Mapped[int] = mapped_column(Integer, default=0)
    synced_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_tap_at: Mapped[datetime | None] = mapped_column(DateTime)
    overheat_until: Mapped[datetime | None] = mapped_column(DateTime)

    mining_started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    referrer_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), index=True
    )
    ref_count: Mapped[int] = mapped_column(Integer, default=0)

    vip_tier: Mapped[int] = mapped_column(Integer, default=0)
    usd_micro: Mapped[int] = mapped_column(BigInteger, default=0)  # USD * 1e6
    streak_day: Mapped[int] = mapped_column(Integer, default=0)
    streak_date: Mapped[str | None] = mapped_column(String(10))  # YYYY-MM-DD клейма

    banned: Mapped[bool] = mapped_column(Boolean, default=False)
    frozen: Mapped[bool] = mapped_column(Boolean, default=False)  # блок кошелька/биржи
    display_name: Mapped[str | None] = mapped_column(String(32))  # своё имя в профиле
    theme: Mapped[str] = mapped_column(String(16), default="gold")  # фон профиля
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class UpgradeState(Base):
    __tablename__ = "upgrade_states"
    __table_args__ = (UniqueConstraint("user_id", "upgrade_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), index=True
    )
    upgrade_id: Mapped[str] = mapped_column(String(32))
    level: Mapped[int] = mapped_column(Integer, default=0)


class LedgerEntry(Base):
    """Каждое движение Coin. reason: tap, combo, mining, ref_share, ref_bonus,
    task, daily, upgrade, p2p_in, p2p_out, p2p_fee, withdraw_hold, withdraw_refund,
    admin_give, welcome."""

    __tablename__ = "ledger"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), index=True
    )
    amount: Mapped[int] = mapped_column(BigInteger)  # coin: штуки, usd: микро-доллары
    currency: Mapped[str] = mapped_column(String(8), default="coin", index=True)
    reason: Mapped[str] = mapped_column(String(32), index=True)
    meta: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class TaskProgress(Base):
    __tablename__ = "task_progress"
    __table_args__ = (UniqueConstraint("user_id", "task_id", "period_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), index=True
    )
    task_id: Mapped[str] = mapped_column(String(32))
    period_key: Mapped[str] = mapped_column(String(16))  # YYYY-MM-DD | YYYY-Www | all
    progress: Mapped[int] = mapped_column(Integer, default=0)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime)


class WithdrawRequest(Base):
    __tablename__ = "withdraw_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), index=True
    )
    amount_micro: Mapped[int] = mapped_column(BigInteger)  # USD * 1e6 (к выплате)
    fee_micro: Mapped[int] = mapped_column(BigInteger, default=0)
    amount_usd: Mapped[float] = mapped_column(Float)       # для сообщений/истории
    status: Mapped[str] = mapped_column(  # pending | approved | declined
        String(16), default="pending", index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime)


class Order(Base):
    """P2P-ордер биржи. Sell держит Coin в эскроу, Buy — USD (micro)."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), index=True
    )
    side: Mapped[str] = mapped_column(String(4), index=True)  # buy | sell
    price_micro: Mapped[int] = mapped_column(BigInteger)      # микро-USD за 1 Coin
    amount_coins: Mapped[int] = mapped_column(BigInteger)
    filled_coins: Mapped[int] = mapped_column(BigInteger, default=0)
    status: Mapped[str] = mapped_column(  # open | filled | cancelled
        String(16), default="open", index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    buy_order_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("orders.id"))
    sell_order_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("orders.id"))
    buyer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    seller_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    price_micro: Mapped[int] = mapped_column(BigInteger)
    amount_coins: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class MarketConfig(Base):
    """Одна строка (id=1): официальный курс и дневной коридор, задаёт админ."""

    __tablename__ = "market_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    official_micro: Mapped[int] = mapped_column(BigInteger)
    day_min_micro: Mapped[int] = mapped_column(BigInteger)
    day_max_micro: Mapped[int] = mapped_column(BigInteger)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Event(Base):
    """Временный ивент «возьми N Coin», создаёт админ."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(64))
    text: Mapped[str] = mapped_column(String(256), default="")
    reward: Mapped[int] = mapped_column(BigInteger)
    ends_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    max_claims: Mapped[int] = mapped_column(Integer, default=0)  # 0 = без лимита
    claims: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class EventClaim(Base):
    __tablename__ = "event_claims"
    __table_args__ = (UniqueConstraint("event_id", "user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"), index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class DepositRequest(Base):
    __tablename__ = "deposit_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    tier: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(  # pending | approved | declined
        String(16), default="pending", index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime)


class CustomTask(Base):
    """Задание, созданное админом: подписка на канал/соцсети/партнёрка.

    kind: channel | social | link — все honor-based (перешёл → можно забрать).
    Прогресс/клейм хранятся в TaskProgress с task_id = f"custom:{id}", period_key="all".
    """

    __tablename__ = "custom_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(64))
    url: Mapped[str] = mapped_column(String(256), default="")
    reward: Mapped[int] = mapped_column(BigInteger)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    kind: Mapped[str] = mapped_column(String(16), default="link")
    icon: Mapped[str] = mapped_column(String(16), default="news")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort: Mapped[int] = mapped_column(Integer, default=0)
    claims: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
