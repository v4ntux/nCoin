from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.leagues import league_bounds, league_for, league_progress
from app.db.models import User

_METRICS = {
    "coins": User.total_earned,
    "referrals": User.ref_count,
    "level": User.level,
}


async def top(
    session: AsyncSession, by: str, me: User, league: str | None = None, limit: int = 100
) -> dict:
    by = by if by in _METRICS else "coins"
    col = _METRICS[by]

    conds = [User.banned.is_(False)]
    if league:
        lo, hi = league_bounds(league)
        conds.append(User.total_earned >= lo)
        if hi is not None:
            conds.append(User.total_earned < hi)

    rows = (
        (
            await session.execute(
                select(User)
                .where(*conds)
                .order_by(col.desc(), User.created_at.asc())
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )

    my_metric = {"coins": me.total_earned, "referrals": me.ref_count, "level": me.level}[by]
    my_rank = (
        await session.execute(
            select(func.count(User.id)).where(*conds, col > my_metric)
        )
    ).scalar_one() + 1

    def value(u: User) -> int:
        return {"coins": u.total_earned, "referrals": u.ref_count, "level": u.level}[by]

    return {
        "by": by,
        "league": league,
        "my_league": league_progress(me.total_earned),
        "me": {"rank": my_rank, "value": my_metric},
        "top": [
            {
                "rank": i + 1,
                "id": u.id,
                "name": u.first_name or u.username or f"Player {u.id}",
                "level": u.level,
                "league": league_for(u.total_earned)["key"],
                "value": value(u),
            }
            for i, u in enumerate(rows)
        ],
    }
