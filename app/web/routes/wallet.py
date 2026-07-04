from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.services import wallet as wallet_service
from app.web.deps import current_user, get_session

router = APIRouter()


class TransferBody(BaseModel):
    to: str = Field(min_length=1, max_length=64)
    amount: int = Field(ge=1)


class WithdrawBody(BaseModel):
    amount_usd: float = Field(gt=0)
    method: str = Field(min_length=1, max_length=16)
    details: str = Field(min_length=1, max_length=128)


class DepositBody(BaseModel):
    tier: int = Field(ge=1, le=3)


@router.get("/wallet")
async def wallet(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await wallet_service.wallet_view(session, user)
    await session.commit()
    return result


@router.post("/wallet/transfer")
async def transfer(
    body: TransferBody,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await wallet_service.transfer(session, user, body.to, body.amount)
    await session.commit()
    return result


@router.post("/wallet/withdraw")
async def withdraw(
    body: WithdrawBody,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await wallet_service.request_withdraw(
        session, user, body.amount_usd, body.method, body.details
    )
    await session.commit()
    return result


@router.post("/wallet/deposit")
async def deposit(
    body: DepositBody,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await wallet_service.request_deposit(session, user, body.tier)
    await session.commit()
    return result


class TopupBody(BaseModel):
    method: str = Field(min_length=1, max_length=16)
    amount_usd: float = Field(gt=0)


@router.post("/wallet/topup")
async def topup(
    body: TopupBody,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await wallet_service.request_topup(session, user, body.method, body.amount_usd)
    await session.commit()
    return result
