from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import xp_to_next
from app.core.clock import ts, utcnow
from app.core.vip import tier_name
from app.db.models import LedgerEntry, TaskProgress, User


EARN_REASONS = ("tap", "combo", "mining", "ref_share", "ref_bonus", "task", "daily")


async def _sum_reason(session: AsyncSession, user_id: int, *reasons: str) -> int:
    return (
        await session.execute(
            select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(
                LedgerEntry.user_id == user_id, LedgerEntry.reason.in_(reasons)
            )
        )
    ).scalar_one()


async def _earned_between(
    session: AsyncSession, user_id: int, start, end
) -> int:
    return (
        await session.execute(
            select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(
                LedgerEntry.user_id == user_id,
                LedgerEntry.currency == "coin",
                LedgerEntry.reason.in_(EARN_REASONS),
                LedgerEntry.amount > 0,
                LedgerEntry.created_at >= start,
                LedgerEntry.created_at < end,
            )
        )
    ).scalar_one()


async def profile_view(session: AsyncSession, user: User) -> dict:
    mined = await _sum_reason(session, user.id, "mining")
    tapped = await _sum_reason(session, user.id, "tap", "combo")
    ref_income = await _sum_reason(session, user.id, "ref_share", "ref_bonus")
    tasks_done = (
        await session.execute(
            select(func.count(TaskProgress.id)).where(
                TaskProgress.user_id == user.id,
                TaskProgress.claimed_at.is_not(None),
            )
        )
    ).scalar_one()
    days = max(1, (utcnow() - user.created_at).days + 1)

    from datetime import timedelta

    day_start = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today = await _earned_between(session, user.id, day_start, utcnow() + timedelta(1))
    yesterday = await _earned_between(
        session, user.id, day_start - timedelta(days=1), day_start
    )
    change_pct = round((today - yesterday) / yesterday * 100, 1) if yesterday else None
    return {
        "usd": round(user.usd_micro / 1_000_000, 4),
        "earned_today": today,
        "earned_yesterday": yesterday,
        "change_pct": change_pct,
        "id": user.id,
        "name": user.display_name or user.first_name or user.username or f"Player {user.id}",
        "username": user.username,
        "theme": user.theme,
        "level": user.level,
        "xp": user.xp,
        "xp_next": xp_to_next(user.level),
        "coins": user.coins,
        "total_earned": user.total_earned,
        "vip": user.vip_tier,
        "vip_name": tier_name(user.vip_tier),
        "ref_count": user.ref_count,
        "created_at": ts(user.created_at),
        "days_in_game": days,
        "stats": {
            "mined": mined,
            "tapped": tapped,
            "ref_income": ref_income,
            "tasks_done": tasks_done,
        },
    }
