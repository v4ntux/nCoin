from collections.abc import AsyncIterator

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.engine import SessionMaker
from app.db.models import User
from app.services.users import get_or_create_user
from app.web.auth import validate_init_data


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionMaker() as session:
        yield session


async def current_user(
    request: Request, session: AsyncSession = Depends(get_session)
) -> User:
    settings = get_settings()

    init_data = request.headers.get("X-Init-Data")
    if init_data and settings.bot_token:
        data = validate_init_data(init_data, settings.bot_token)
        if not data:
            raise HTTPException(401, "Invalid initData")
        tg = data["user"]
        referrer_id = None
        sp = data.get("start_param") or ""
        if sp.isdigit():
            referrer_id = int(sp)
        user, _ = await get_or_create_user(
            session,
            tg["id"],
            tg.get("username"),
            tg.get("first_name", ""),
            referrer_id=referrer_id,
        )
    elif settings.dev_mode and request.headers.get("X-Dev-User"):
        uid = int(request.headers["X-Dev-User"])
        user, _ = await get_or_create_user(session, uid, f"dev{uid}", f"Dev {uid}")
    else:
        raise HTTPException(401, "Auth required")

    if user.banned:
        raise HTTPException(403, "Banned")
    return user
