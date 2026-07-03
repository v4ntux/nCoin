from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.services import tasks as tasks_service
from app.services.game import effects_for
from app.web.deps import current_user, get_session

router = APIRouter()


class ClaimBody(BaseModel):
    id: str


@router.get("/tasks")
async def tasks(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    items = await tasks_service.view(session, user)
    await session.commit()
    return {"items": items}


@router.post("/tasks/claim")
async def claim(
    body: ClaimBody,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    eff = await effects_for(session, user)
    result = await tasks_service.claim(session, user, body.id, eff.xp_mult)
    await session.commit()
    return {**result, "coins": user.coins, "xp": user.xp, "level": user.level}
