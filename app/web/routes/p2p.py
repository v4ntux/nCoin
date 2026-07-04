"""P2P REST: объявления, сделки, чат (текст+фото), разбор споров админом."""

import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.constants import PAY_METHODS
from app.db.models import User
from app.services import market, p2p
from app.web.deps import current_user, get_session

router = APIRouter()

MEDIA_DIR = Path(__file__).resolve().parents[3] / "media" / "deals"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXT = {"jpg", "jpeg", "png", "gif", "webp"}


def _is_staff(user: User) -> bool:
    return user.is_operator or user.id in get_settings().admin_id_list


class AdBody(BaseModel):
    price_uzs: int = Field(gt=0)
    amount: int = Field(ge=1)
    pay_method: str
    pay_details: str = Field(max_length=128)


class DealBody(BaseModel):
    ad_id: int
    amount: int = Field(ge=1)


class IdBody(BaseModel):
    id: int


class MsgBody(BaseModel):
    deal_id: int
    body: str = Field(max_length=1024)


class ResolveBody(BaseModel):
    deal_id: int
    action: str = Field(pattern="^(release|refund)$")
    ban_buyer: bool = False
    ban_seller: bool = False


# ---------------------------------------------------------------- рынок / курс


@router.get("/market")
async def market_view(
    user: User = Depends(current_user), session: AsyncSession = Depends(get_session)
) -> dict:
    price = await market.price_uzs(session)
    result = {
        "price": price,
        "change_pct": await market.change_pct(session),
        "coins": user.coins,
        "frozen": user.frozen,
        "fee_pct": round(p2p.P2P_FEE_BP / 100, 2),
        "pay_methods": PAY_METHODS,
        "ads": await p2p.list_ads(session, user.id),
        "my_ads": await p2p.my_ads(session, user),
        "my_deals": await p2p.my_deals(session, user),
        "trades": await market.recent_trades(session),
    }
    await session.commit()
    return result


@router.get("/market/chart")
async def chart(
    tf: str = Query("1h"),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    tf = tf if tf in ("15m", "30m", "1h", "1d", "1w", "1mo") else "1h"
    candles = await market.candles(session, tf)
    return {"tf": tf, "sec": market.tf_seconds(tf), "candles": candles}


# ---------------------------------------------------------------- объявления


@router.post("/p2p/ad")
async def create_ad(
    body: AdBody, user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    r = await p2p.create_ad(session, user, body.price_uzs, body.amount,
                            body.pay_method, body.pay_details)
    await session.commit()
    return r


@router.post("/p2p/ad/close")
async def close_ad(
    body: IdBody, user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    r = await p2p.close_ad(session, user, body.id)
    await session.commit()
    return r


# ---------------------------------------------------------------- сделки


@router.post("/p2p/deal")
async def open_deal(
    body: DealBody, user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    r = await p2p.open_deal(session, user, body.ad_id, body.amount)
    await session.commit()
    return r


@router.get("/p2p/deal/{deal_id}")
async def deal_view(
    deal_id: int, user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    r = await p2p.deal_view(session, user, deal_id)
    await session.commit()
    return r


async def _act(action, session, user, deal_id):
    fn = getattr(p2p, action)
    r = await fn(session, user, deal_id)
    await session.commit()
    return r


@router.post("/p2p/deal/paid")
async def deal_paid(body: IdBody, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict:
    return await _act("mark_paid", session, user, body.id)


@router.post("/p2p/deal/release")
async def deal_release(body: IdBody, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict:
    return await _act("release", session, user, body.id)


@router.post("/p2p/deal/reject")
async def deal_reject(body: IdBody, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict:
    return await _act("reject", session, user, body.id)


@router.post("/p2p/deal/cancel")
async def deal_cancel(body: IdBody, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict:
    return await _act("cancel", session, user, body.id)


@router.post("/p2p/deal/dispute")
async def deal_dispute(body: IdBody, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict:
    return await _act("open_dispute", session, user, body.id)


# ---------------------------------------------------------------- чат


@router.get("/p2p/deal/{deal_id}/messages")
async def deal_messages(
    deal_id: int, after: int = Query(0, ge=0),
    user: User = Depends(current_user), session: AsyncSession = Depends(get_session),
) -> dict:
    r = await p2p.messages(session, user, deal_id, after)
    await session.commit()
    return r


@router.post("/p2p/deal/message")
async def deal_send(
    body: MsgBody, user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    r = await p2p.send_message(session, user, body.deal_id, body.body)
    await session.commit()
    return r


@router.post("/p2p/deal/{deal_id}/photo")
async def deal_photo(
    deal_id: int, file: UploadFile = File(...),
    user: User = Depends(current_user), session: AsyncSession = Depends(get_session),
) -> dict:
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, "Unsupported image type")
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(400, "Image too large (max 5MB)")
    fname = f"{deal_id}_{secrets.token_hex(8)}.{ext}"
    (MEDIA_DIR / fname).write_bytes(data)
    r = await p2p.send_message(session, user, deal_id, "", kind="photo",
                               media_path=f"deals/{fname}")
    await session.commit()
    return r


# ---------------------------------------------------------------- админ/операторы


@router.get("/p2p/disputes")
async def disputes(
    user: User = Depends(current_user), session: AsyncSession = Depends(get_session)
) -> dict:
    if not _is_staff(user):
        raise HTTPException(403, "Staff only")
    return {"items": await p2p.list_disputes(session)}


@router.post("/p2p/resolve")
async def resolve(
    body: ResolveBody, user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    if not _is_staff(user):
        raise HTTPException(403, "Staff only")
    r = await p2p.resolve(session, body.deal_id, body.action, body.ban_buyer, body.ban_seller)
    await session.commit()
    return r
