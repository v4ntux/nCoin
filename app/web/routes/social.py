from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import REF_BONUS_INVITER, REF_BONUS_NEW
from app.db.models import User
from app.services import leaderboard as lb_service
from app.services.game import effects_for
from app.web.deps import current_user, get_session

router = APIRouter()


@router.get("/friends")
async def friends(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    from app.bot import instance

    rows = (
        (
            await session.execute(
                select(User)
                .where(User.referrer_id == user.id)
                .order_by(User.total_earned.desc())
                .limit(100)
            )
        )
        .scalars()
        .all()
    )
    eff = await effects_for(session, user)
    bot_username = instance.bot_username or "bot"
    await session.commit()
    return {
        "link": f"https://t.me/{bot_username}?start={user.id}",
        "bonus_inviter": REF_BONUS_INVITER,
        "bonus_friend": REF_BONUS_NEW,
        "share_percent": round(eff.ref_share * 100, 1),
        "count": user.ref_count,
        "friends": [
            {
                "id": f.id,
                "name": f.first_name or f.username or f"Player {f.id}",
                "level": f.level,
                "earned": f.total_earned,
            }
            for f in rows
        ],
    }


@router.get("/leaderboard")
async def leaderboard(
    by: str = Query("coins"),
    league: str | None = Query(None),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await lb_service.top(session, by, user, league=league)
    await session.commit()
    return result
