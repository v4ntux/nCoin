from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import BASE_REF_SHARE, REF_SHARE_CAP, UPGRADE_EFFECTS
from app.db.models import LedgerEntry, UpgradeState, User

# заработки, с которых реферер получает свою долю (без каскада: ref_share не тут)
REF_EARN_REASONS = {"tap", "combo", "mining", "task", "daily", "event"}


async def credit(
    session: AsyncSession,
    user: User,
    amount: int,
    reason: str,
    meta: dict | None = None,
    count_earned: bool = True,
) -> None:
    """Единственная точка изменения Coin-баланса. amount < 0 — списание.

    count_earned=False для переводов/возвратов, чтобы не читерить задачи
    «заработай N», total_earned и лиги.
    """
    user.coins += amount
    if amount > 0 and count_earned:
        user.total_earned += amount
    session.add(
        LedgerEntry(
            user_id=user.id, amount=amount, currency="coin", reason=reason, meta=meta
        )
    )

    # реферер получает долю со ВСЕХ заработков приглашённого
    if amount > 0 and reason in REF_EARN_REASONS and user.referrer_id:
        ref = await session.get(User, user.referrer_id)
        if ref is not None and not ref.banned:
            lvl = (
                await session.execute(
                    select(UpgradeState.level).where(
                        UpgradeState.user_id == ref.id,
                        UpgradeState.upgrade_id == "ref_boost",
                    )
                )
            ).scalar_one_or_none() or 0
            share = min(
                REF_SHARE_CAP, BASE_REF_SHARE + UPGRADE_EFFECTS["ref_boost"] * lvl
            )
            cut = int(amount * share)
            if cut > 0:
                ref.coins += cut
                ref.total_earned += cut
                session.add(
                    LedgerEntry(
                        user_id=ref.id,
                        amount=cut,
                        currency="coin",
                        reason="ref_share",
                        meta={"from": user.id},
                    )
                )


async def credit_usd(
    session: AsyncSession,
    user: User,
    micro: int,
    reason: str,
    meta: dict | None = None,
) -> None:
    """Движение USD-баланса (микро-доллы, int). micro < 0 — списание."""
    user.usd_micro += micro
    session.add(
        LedgerEntry(
            user_id=user.id, amount=micro, currency="usd", reason=reason, meta=meta
        )
    )
