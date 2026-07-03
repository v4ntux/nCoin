from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.services import tasks as tasks_service
from app.services.game import build_state
from app.services.profile import profile_view
from app.web.deps import current_user, get_session

router = APIRouter()

THEMES = {"gold", "violet", "cyan", "crimson", "emerald", "mono"}


class ProfileUpdate(BaseModel):
    name: str | None = Field(None, max_length=32)
    theme: str | None = None


@router.post("/profile/update")
async def profile_update(
    body: ProfileUpdate,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    if body.name is not None:
        clean = body.name.strip()[:32]
        user.display_name = clean or None
    if body.theme and body.theme in THEMES:
        user.theme = body.theme
    await session.commit()
    return {
        "name": user.display_name or user.first_name or f"Player {user.id}",
        "theme": user.theme,
    }


@router.post("/auth")
async def auth(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Вход в приложение: регистрирует, двигает задачу «open», отдаёт стейт."""
    await tasks_service.bump(session, user, "open")
    state = await build_state(session, user)
    await session.commit()
    return state


@router.get("/state")
async def state(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await build_state(session, user)
    await session.commit()  # get_or_create мог обновить last_seen/имя
    return result


@router.get("/news")
async def news() -> dict:
    from app.constants import NEWS

    return {"items": NEWS}


@router.get("/events")
async def events(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    from app.services import events as events_service

    items = await events_service.active_for(session, user)
    await session.commit()
    return {"items": items}


@router.post("/events/claim")
async def claim_event(
    body: dict,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    from app.services import events as events_service

    result = await events_service.claim(session, user, int(body.get("id", 0)))
    await session.commit()
    return result


@router.get("/profile")
async def profile(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await profile_view(session, user)
    await session.commit()
    return result
