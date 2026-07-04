from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import User
from app.services import admin as admin_service
from app.web.deps import current_user, get_session

router = APIRouter(prefix="/admin")


async def current_admin(user: User = Depends(current_user)) -> User:
    if user.id not in get_settings().admin_id_list:
        raise HTTPException(403, "Admins only")
    return user


@router.get("/stats")
async def stats(
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await admin_service.stats(session)
    await session.commit()
    return result


@router.get("/chart")
async def chart(
    kind: str = Query("price"),
    tf: str = Query("month"),
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    points = await admin_service.chart(session, kind, tf)
    await session.commit()
    return {"kind": kind, "tf": tf, "points": points}


@router.get("/users")
async def users(
    q: str = Query(""),
    offset: int = Query(0, ge=0),
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await admin_service.users_list(session, q, offset)
    await session.commit()
    return result


@router.get("/users/{uid}")
async def user_detail(
    uid: int,
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await admin_service.user_detail(session, uid)
    await session.commit()
    return result


class ActionBody(BaseModel):
    action: str
    value: float | None = None


@router.post("/users/{uid}/action")
async def user_action(
    uid: int,
    body: ActionBody,
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await admin_service.user_action(session, uid, body.action, body.value)
    await session.commit()
    return result


@router.get("/requests")
async def requests(
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await admin_service.requests_view(session)
    await session.commit()
    return result


class DecideBody(BaseModel):
    id: int
    approve: bool


@router.post("/requests/withdraw")
async def decide_withdraw(
    body: DecideBody,
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    note = await admin_service.decide_withdraw(session, body.id, body.approve)
    await session.commit()
    return {"note": note}


@router.post("/requests/deposit")
async def decide_deposit(
    body: DecideBody,
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    note = await admin_service.decide_deposit(session, body.id, body.approve)
    await session.commit()
    return {"note": note}


@router.get("/events")
async def events(
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    items = await admin_service.events_admin_list(session)
    await session.commit()
    return {"items": items}


class EventBody(BaseModel):
    title: str = Field(min_length=1, max_length=64)
    text: str = Field("", max_length=256)
    reward: int = Field(gt=0)
    minutes: int = Field(gt=0, le=10080)
    max_claims: int = Field(0, ge=0)


@router.post("/events")
async def event_create(
    body: EventBody,
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await admin_service.event_create(
        session, body.title, body.text, body.reward, body.minutes, body.max_claims
    )
    await session.commit()
    return result


class ToggleBody(BaseModel):
    id: int
    active: bool


@router.post("/events/toggle")
async def event_toggle(
    body: ToggleBody,
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await admin_service.event_toggle(session, body.id, body.active)
    await session.commit()
    return result


@router.get("/market")
async def market(
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await admin_service.market_admin_view(session)
    await session.commit()
    return result


class MarketBody(BaseModel):
    target_uzs: float = Field(gt=0)


@router.post("/market")
async def market_set(
    body: MarketBody,
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await admin_service.market_set(session, body.target_uzs)
    await session.commit()
    return result


@router.get("/tasks")
async def tasks(
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    items = await admin_service.tasks_admin_list(session)
    await session.commit()
    return {"items": items}


class TaskBody(BaseModel):
    title: str = Field(min_length=1, max_length=64)
    url: str = Field("", max_length=256)
    reward: int = Field(gt=0)
    xp: int = Field(0, ge=0)
    kind: str = Field("link")


@router.post("/tasks")
async def task_create(
    body: TaskBody,
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await admin_service.task_create(
        session, body.title, body.url, body.reward, body.xp, body.kind
    )
    await session.commit()
    return result


@router.post("/tasks/toggle")
async def task_toggle(
    body: ToggleBody,
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await admin_service.task_toggle(session, body.id, body.active)
    await session.commit()
    return result


class TaskDeleteBody(BaseModel):
    id: int


@router.post("/tasks/delete")
async def task_delete(
    body: TaskDeleteBody,
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await admin_service.task_delete(session, body.id)
    await session.commit()
    return result


# ── news ──
@router.get("/news")
async def news(
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    items = await admin_service.news_admin_list(session)
    await session.commit()
    return {"items": items}


class NewsBody(BaseModel):
    tag: str = Field("NEW", max_length=12)
    title: str = Field(min_length=1, max_length=64)
    text: str = Field("", max_length=256)
    sort: int = Field(0)


@router.post("/news")
async def news_create(
    body: NewsBody,
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await admin_service.news_create(session, body.tag, body.title, body.text, body.sort)
    await session.commit()
    return result


@router.post("/news/toggle")
async def news_toggle(
    body: ToggleBody,
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await admin_service.news_toggle(session, body.id, body.active)
    await session.commit()
    return result


@router.post("/news/delete")
async def news_delete(
    body: TaskDeleteBody,
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await admin_service.news_delete(session, body.id)
    await session.commit()
    return result


# ── settings (support + VIP) ──
@router.get("/settings")
async def settings_get(
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await admin_service.settings_view(session)
    await session.commit()
    return result


class SettingsBody(BaseModel):
    support_tg: str = Field("", max_length=64)
    support_email: str = Field("", max_length=64)
    support_text: str = Field("", max_length=256)
    vip: list[dict] = Field(default_factory=list)


@router.post("/settings")
async def settings_save(
    body: SettingsBody,
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await admin_service.settings_save(
        session, body.support_tg, body.support_email, body.support_text, body.vip
    )
    await session.commit()
    return result
