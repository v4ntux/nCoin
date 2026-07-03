from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import (
    APP_VERSION,
    COIN_USD_RATE,
    COMBO_RESET_GAP,
    HEAT_MAX,
    HEAT_PER_TAP,
    MAX_TAPS_PER_SEC,
    OVERHEAT_LOCK_SECONDS,
    UPGRADES,
    XP_PER_COIN,
    xp_to_next,
)
from app.core.clock import ts, utcnow
from app.core.energy import energy_at
from app.core.heat import heat_at
from app.core.levels import gain_xp
from app.core.mining import mining_view
from app.core.rewards import reward_for_day, streak_status
from app.core.taps import resolve_taps
from app.core.upgrades import Effects, compute_effects, upgrade_cost
from app.core.vip import tier_name
from app.db.models import UpgradeState, User
from app.services import tasks as tasks_service
from app.services.economy import credit
from app.services.errors import GameError


async def load_levels(session: AsyncSession, user_id: int) -> dict[str, int]:
    rows = (
        await session.execute(
            select(UpgradeState).where(UpgradeState.user_id == user_id)
        )
    ).scalars()
    return {r.upgrade_id: r.level for r in rows}


async def effects_for(session: AsyncSession, user: User) -> Effects:
    return compute_effects(await load_levels(session, user.id), user.level)


def _award_xp(user: User, coins: int, eff: Effects) -> int:
    gained = int(coins * XP_PER_COIN * eff.xp_mult)
    if gained > 0:
        user.xp, user.level, _ = gain_xp(user.xp, user.level, gained)
    return gained


async def build_state(session: AsyncSession, user: User) -> dict:
    now = utcnow()
    eff = await effects_for(session, user)
    energy = energy_at(user.energy, user.synced_at, now, eff.energy_max, eff.energy_regen)
    heat = heat_at(user.heat, user.synced_at, now, eff.heat_decay)
    mv = mining_view(
        user.mining_started_at, now, eff.mine_rate, eff.cycle_hours, eff.extra_hours
    )
    can_claim, next_day = streak_status(user.streak_day, user.streak_date, now.date())
    combo = user.combo
    if user.last_tap_at and (now - user.last_tap_at).total_seconds() > COMBO_RESET_GAP:
        combo = 0
    return {
        "version": APP_VERSION,
        "server_time": ts(now),
        "user": {
            "id": user.id,
            "name": user.display_name or user.first_name or user.username or f"Player {user.id}",
            "username": user.username,
            "level": user.level,
            "xp": user.xp,
            "xp_next": xp_to_next(user.level),
            "coins": user.coins,
            "usd": round(user.coins * COIN_USD_RATE, 4),
            "vip": user.vip_tier,
            "vip_name": tier_name(user.vip_tier),
            "ref_count": user.ref_count,
            "streak_day": user.streak_day,
            "daily_available": can_claim,
            "daily_next_reward": reward_for_day(next_day),
            "daily_next_day": next_day,
            "created_at": ts(user.created_at),
        },
        "clicker": {
            "tap_power": eff.tap_power,
            "crit_chance": round(eff.crit_chance, 4),
            "double_chance": round(eff.double_chance, 4),
            "energy": round(energy, 2),
            "energy_max": eff.energy_max,
            "regen": round(eff.energy_regen, 4),
            "heat": round(heat, 2),
            "heat_max": HEAT_MAX,
            "heat_decay": eff.heat_decay,
            "heat_per_tap": HEAT_PER_TAP,
            "combo": combo,
            "overheat_until": ts(user.overheat_until),
        },
        "mining": {
            "rate": round(eff.mine_rate, 1),
            "mined": mv.mined,
            "capacity": mv.capacity,
            "progress": round(mv.progress, 4),
            "ready_in": mv.ready_in_sec,
            "window_hours": round(mv.window_hours, 2),
            "started_at": ts(user.mining_started_at),
        },
        "economy": {
            "usd_rate": COIN_USD_RATE,
            "income_mult": round(eff.income_mult, 3),
        },
    }


async def tap(session: AsyncSession, user: User, count: int) -> dict:
    if count < 1:
        raise GameError("bad_count", "Nothing to tap")
    count = min(count, 600)
    now = utcnow()

    if user.overheat_until and user.overheat_until > now:
        raise GameError("overheat", "System overheated")

    eff = await effects_for(session, user)
    energy = energy_at(user.energy, user.synced_at, now, eff.energy_max, eff.energy_regen)
    heat = heat_at(user.heat, user.synced_at, now, eff.heat_decay)

    # анти-чит: кап тапов по времени с прошлого батча
    if user.last_tap_at:
        elapsed = max(0.0, (now - user.last_tap_at).total_seconds())
        count = min(count, int(elapsed * MAX_TAPS_PER_SEC) + MAX_TAPS_PER_SEC)

    taps = min(count, int(energy))
    if taps <= 0:
        raise GameError("no_energy", "No energy")

    combo = user.combo
    if user.last_tap_at and (now - user.last_tap_at).total_seconds() > COMBO_RESET_GAP:
        combo = 0

    result = resolve_taps(
        taps, eff.tap_power, eff.crit_chance, eff.double_chance, combo, eff.income_mult
    )

    overheated = False
    heat += taps * HEAT_PER_TAP
    if heat >= HEAT_MAX:
        heat = HEAT_MAX
        user.overheat_until = now + timedelta(seconds=OVERHEAT_LOCK_SECONDS)
        overheated = True
        result.combo = 0

    user.energy = energy - taps
    user.heat = heat
    user.combo = result.combo
    user.synced_at = now
    user.last_tap_at = now

    await credit(session, user, result.coins, "tap", {"taps": taps, "crits": result.crits})
    if result.combo_bonus:
        await credit(session, user, result.combo_bonus, "combo")
    xp = _award_xp(user, result.coins + result.combo_bonus, eff)

    await tasks_service.bump(session, user, "taps", taps)
    await tasks_service.bump(session, user, "earn", result.coins + result.combo_bonus)

    return {
        "taps": taps,
        "coins_added": result.coins + result.combo_bonus,
        "crits": result.crits,
        "doubles": result.doubles,
        "combo": result.combo,
        "combo_bonus": result.combo_bonus,
        "overheated": overheated,
        "xp_added": xp,
        "coins": user.coins,
        "usd": round(user.coins * COIN_USD_RATE, 4),
        "energy": round(user.energy, 2),
        "heat": round(user.heat, 2),
        "overheat_until": ts(user.overheat_until),
        "level": user.level,
        "xp": user.xp,
        "xp_next": xp_to_next(user.level),
    }


async def collect(session: AsyncSession, user: User) -> dict:
    now = utcnow()
    eff = await effects_for(session, user)
    mv = mining_view(
        user.mining_started_at, now, eff.mine_rate, eff.cycle_hours, eff.extra_hours
    )
    if mv.mined <= 0:
        raise GameError("nothing_mined", "Nothing to collect yet")

    await credit(session, user, mv.mined, "mining")
    xp = _award_xp(user, mv.mined, eff)
    user.mining_started_at = now

    # реферальная доля начисляется универсально в economy.credit()
    await tasks_service.bump(session, user, "collect", 1)
    await tasks_service.bump(session, user, "earn", mv.mined)

    return {
        "collected": mv.mined,
        "xp_added": xp,
        "coins": user.coins,
        "usd": round(user.coins * COIN_USD_RATE, 4),
        "level": user.level,
        "xp": user.xp,
        "xp_next": xp_to_next(user.level),
    }


async def upgrades_view(session: AsyncSession, user: User) -> list[dict]:
    levels = await load_levels(session, user.id)
    out = []
    for uid, u in UPGRADES.items():
        level = levels.get(uid, 0)
        maxed = level >= u["max_level"]
        out.append(
            {
                "id": uid,
                "branch": u["branch"],
                "name": u["name"],
                "emoji": u["emoji"],
                "desc": u["desc"],
                "level": level,
                "max_level": u["max_level"],
                "cost": None if maxed else upgrade_cost(uid, level),
                "maxed": maxed,
            }
        )
    return out


async def buy_upgrade(session: AsyncSession, user: User, upgrade_id: str) -> dict:
    u = UPGRADES.get(upgrade_id)
    if not u:
        raise GameError("unknown_upgrade", "Unknown upgrade")
    row = (
        await session.execute(
            select(UpgradeState).where(
                UpgradeState.user_id == user.id,
                UpgradeState.upgrade_id == upgrade_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        row = UpgradeState(user_id=user.id, upgrade_id=upgrade_id, level=0)
        session.add(row)
    if row.level >= u["max_level"]:
        raise GameError("maxed", "Upgrade is maxed out")
    cost = upgrade_cost(upgrade_id, row.level)
    if user.coins < cost:
        raise GameError("not_enough", "Not enough Coin")

    await credit(session, user, -cost, "upgrade", {"upgrade": upgrade_id})
    row.level += 1
    return {
        "id": upgrade_id,
        "level": row.level,
        "coins": user.coins,
        "next_cost": None
        if row.level >= u["max_level"]
        else upgrade_cost(upgrade_id, row.level),
    }


async def claim_daily(session: AsyncSession, user: User) -> dict:
    now = utcnow()
    can_claim, day = streak_status(user.streak_day, user.streak_date, now.date())
    if not can_claim:
        raise GameError("already_claimed", "Come back tomorrow")
    reward = reward_for_day(day)
    user.streak_day = day
    user.streak_date = now.date().isoformat()
    await credit(session, user, reward, "daily", {"day": day})
    eff = await effects_for(session, user)
    xp = _award_xp(user, reward, eff)
    return {
        "day": day,
        "reward": reward,
        "xp_added": xp,
        "coins": user.coins,
        "streak_day": user.streak_day,
    }
