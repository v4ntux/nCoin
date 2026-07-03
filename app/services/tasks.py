from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.constants import TASKS
from app.core.clock import utcnow
from app.core.levels import gain_xp
from app.core.periods import period_key
from app.db.models import CustomTask, TaskProgress, User
from app.services.economy import credit
from app.services.errors import GameError


async def _active_custom(session: AsyncSession) -> list[CustomTask]:
    return list(
        (
            await session.execute(
                select(CustomTask)
                .where(CustomTask.active.is_(True))
                .order_by(CustomTask.sort, CustomTask.id)
            )
        )
        .scalars()
        .all()
    )


async def _row(
    session: AsyncSession, user_id: int, task_id: str, cat: str
) -> TaskProgress:
    key = period_key(cat, utcnow())
    row = (
        await session.execute(
            select(TaskProgress).where(
                TaskProgress.user_id == user_id,
                TaskProgress.task_id == task_id,
                TaskProgress.period_key == key,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        row = TaskProgress(
            user_id=user_id, task_id=task_id, period_key=key, progress=0
        )
        session.add(row)
    return row


async def bump(session: AsyncSession, user: User, kind: str, amount: int = 1) -> None:
    """Двигает прогресс всех незаклеймленных задач данного вида."""
    for task_id, t in TASKS.items():
        if t["kind"] != kind:
            continue
        row = await _row(session, user.id, task_id, t["cat"])
        if row.claimed_at is None and row.progress < t["goal"]:
            row.progress = min(t["goal"], row.progress + amount)


async def view(session: AsyncSession, user: User) -> list[dict]:
    settings = get_settings()
    out = []
    for task_id, t in TASKS.items():
        row = await _row(session, user.id, task_id, t["cat"])
        url = t.get("url") or ""
        if task_id == "s_channel":
            url = settings.channel_url or url
        out.append(
            {
                "id": task_id,
                "cat": t["cat"],
                "name": t["name"],
                "emoji": t["emoji"],
                "goal": t["goal"],
                "reward": t["reward"],
                "xp": t["xp"],
                "kind": t["kind"],
                "url": url,
                "progress": row.progress,
                "claimed": row.claimed_at is not None,
            }
        )

    # задания, созданные админом (подписки/соцсети/партнёрка) — в Special
    for ct in await _active_custom(session):
        cid = f"custom:{ct.id}"
        row = await _row(session, user.id, cid, "special")
        out.append(
            {
                "id": cid,
                "cat": "special",
                "name": ct.title,
                "icon": ct.icon,
                "goal": 1,
                "reward": ct.reward,
                "xp": ct.xp,
                "kind": ct.kind,
                "url": ct.url,
                "progress": row.progress,
                "claimed": row.claimed_at is not None,
            }
        )
    return out


async def claim(session: AsyncSession, user: User, task_id: str, xp_mult: float) -> dict:
    # админские задания (custom:<id>) — honor-based
    if task_id.startswith("custom:"):
        ct = await session.get(CustomTask, int(task_id.split(":", 1)[1]))
        if not ct or not ct.active:
            raise GameError("unknown_task", "Task is no longer available")
        row = await _row(session, user.id, task_id, "special")
        if row.claimed_at is not None:
            raise GameError("already_claimed", "Already claimed")
        row.progress = 1
        row.claimed_at = utcnow()
        ct.claims += 1
        await credit(session, user, ct.reward, "task", {"task": task_id})
        xp_gain = int(ct.xp * xp_mult)
        user.xp, user.level, _ = gain_xp(user.xp, user.level, xp_gain)
        return {"reward": ct.reward, "xp": xp_gain}

    t = TASKS.get(task_id)
    if not t:
        raise GameError("unknown_task", "Unknown task")
    row = await _row(session, user.id, task_id, t["cat"])
    if row.claimed_at is not None:
        raise GameError("already_claimed", "Already claimed")
    if t["kind"] == "link":
        row.progress = t["goal"]  # v0.1: переход по ссылке = выполнено
    if row.progress < t["goal"]:
        raise GameError("not_done", "Task is not completed yet")

    row.claimed_at = utcnow()
    await credit(session, user, t["reward"], "task", {"task": task_id})
    xp_gain = int(t["xp"] * xp_mult)
    user.xp, user.level, _ = gain_xp(user.xp, user.level, xp_gain)
    return {"reward": t["reward"], "xp": xp_gain}
