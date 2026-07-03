"""Временные ивенты «возьми N Coin, пока не закончилось время/призы»."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import utcnow
from app.db.models import Event, EventClaim, User
from app.services.economy import credit
from app.services.errors import GameError


async def active_for(session: AsyncSession, user: User) -> list[dict]:
    now = utcnow()
    events = (
        (
            await session.execute(
                select(Event)
                .where(Event.active.is_(True), Event.ends_at > now)
                .order_by(Event.ends_at)
            )
        )
        .scalars()
        .all()
    )
    if not events:
        return []
    claimed = set(
        (
            await session.execute(
                select(EventClaim.event_id).where(
                    EventClaim.user_id == user.id,
                    EventClaim.event_id.in_([e.id for e in events]),
                )
            )
        ).scalars()
    )
    return [
        {
            "id": e.id,
            "title": e.title,
            "text": e.text,
            "reward": e.reward,
            "ends_in": max(0, int((e.ends_at - now).total_seconds())),
            "left": None if e.max_claims == 0 else max(0, e.max_claims - e.claims),
            "claimed": e.id in claimed,
        }
        for e in events
    ]


async def claim(session: AsyncSession, user: User, event_id: int) -> dict:
    now = utcnow()
    ev = await session.get(Event, event_id)
    if not ev or not ev.active or ev.ends_at <= now:
        raise GameError("no_event", "Event is over")
    if ev.max_claims and ev.claims >= ev.max_claims:
        raise GameError("sold_out", "All prizes are taken")
    exists = (
        await session.execute(
            select(EventClaim.id).where(
                EventClaim.event_id == ev.id, EventClaim.user_id == user.id
            )
        )
    ).scalar_one_or_none()
    if exists:
        raise GameError("already_claimed", "Already claimed")

    session.add(EventClaim(event_id=ev.id, user_id=user.id))
    ev.claims += 1
    await credit(session, user, ev.reward, "event", {"event": ev.id})
    return {"reward": ev.reward, "coins": user.coins}
