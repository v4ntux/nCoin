from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import REF_BONUS_INVITER, REF_BONUS_NEW
from app.core.clock import utcnow
from app.db.models import User
from app.services import tasks as tasks_service
from app.services.economy import credit


async def get_or_create_user(
    session: AsyncSession,
    tg_id: int,
    username: str | None = None,
    first_name: str = "",
    referrer_id: int | None = None,
) -> tuple[User, bool]:
    """Возвращает (user, created). Рефералка срабатывает только при создании."""
    user = await session.get(User, tg_id)
    if user:
        if username and user.username != username:
            user.username = username
        if first_name and user.first_name != first_name:
            user.first_name = first_name
        user.last_seen_at = utcnow()
        return user, False

    user = User(id=tg_id, username=username, first_name=first_name)
    session.add(user)
    # flush применяет дефолты колонок (coins=0 и т.д.) до первого чтения полей
    await session.flush()

    if referrer_id and referrer_id != tg_id:
        ref = await session.get(User, referrer_id)
        if ref:
            user.referrer_id = ref.id
            ref.ref_count += 1
            await credit(session, user, REF_BONUS_NEW, "ref_bonus", {"from": ref.id})
            await credit(
                session, ref, REF_BONUS_INVITER, "ref_bonus", {"invited": tg_id}
            )
            await tasks_service.bump(session, ref, "invite", 1)
    return user, True
