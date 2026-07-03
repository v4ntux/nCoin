from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.services import game as game_service
from app.web.deps import current_user, get_session

router = APIRouter()


class TapBody(BaseModel):
    count: int = Field(ge=1, le=600)


class BuyBody(BaseModel):
    id: str


@router.post("/tap")
async def tap(
    body: TapBody,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await game_service.tap(session, user, body.count)
    await session.commit()
    return result


@router.post("/collect")
async def collect(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await game_service.collect(session, user)
    await session.commit()
    return result


@router.get("/upgrades")
async def upgrades(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    items = await game_service.upgrades_view(session, user)
    await session.commit()
    return {"coins": user.coins, "items": items}


@router.post("/upgrades/buy")
async def buy(
    body: BuyBody,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await game_service.buy_upgrade(session, user, body.id)
    await session.commit()
    return result


@router.post("/daily/claim")
async def daily_claim(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await game_service.claim_daily(session, user)
    await session.commit()
    return result
