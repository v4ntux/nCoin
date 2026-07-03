from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import USD_MICRO
from app.db.models import User
from app.services import exchange as ex_service
from app.web.deps import current_user, get_session

router = APIRouter()


class OrderBody(BaseModel):
    side: str = Field(pattern="^(buy|sell)$")
    price_usd: float = Field(gt=0)
    amount: int = Field(ge=1)


class CancelBody(BaseModel):
    id: int


@router.get("/exchange")
async def market(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await ex_service.market_view(session, user)
    await session.commit()
    return result


@router.get("/exchange/chart")
async def chart(
    tf: str = Query("day"),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    tf = tf if tf in ("day", "month", "all") else "day"
    points = await ex_service.chart(session, tf)
    await session.commit()
    return {"tf": tf, "points": points}


@router.post("/exchange/order")
async def place(
    body: OrderBody,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    price_micro = round(body.price_usd * USD_MICRO)
    result = await ex_service.place_order(
        session, user, body.side, price_micro, body.amount
    )
    await session.commit()
    return result


@router.post("/exchange/cancel")
async def cancel(
    body: CancelBody,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await ex_service.cancel_order(session, user, body.id)
    await session.commit()
    return result
