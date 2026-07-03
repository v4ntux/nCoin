from dataclasses import dataclass

from app.constants import (
    BASE_CRIT_CHANCE,
    BASE_DOUBLE_CHANCE,
    BASE_ENERGY_MAX,
    BASE_ENERGY_REGEN,
    BASE_HEAT_DECAY,
    BASE_MINE_RATE,
    BASE_REF_SHARE,
    BASE_TAP_POWER,
    LEVEL_INCOME_BONUS,
    MIN_CYCLE_HOURS,
    MINE_CYCLE_HOURS,
    REF_SHARE_CAP,
    UPGRADE_EFFECTS,
    UPGRADES,
)


@dataclass
class Effects:
    """Все производные характеристики юзера из уровней апгрейдов + левела."""

    tap_power: int
    crit_chance: float
    double_chance: float
    energy_max: int
    energy_regen: float
    heat_decay: float
    mine_rate: float      # Coin/час, финальная (farm и income_mult уже внутри)
    cycle_hours: float
    extra_hours: float
    income_mult: float    # уровень + core_boost; применяется к тапам и майнингу
    xp_mult: float
    ref_share: float


def upgrade_cost(upgrade_id: str, level: int) -> int:
    """Цена перехода level → level+1."""
    u = UPGRADES[upgrade_id]
    return int(u["base_cost"] * u["mult"] ** level)


def compute_effects(levels: dict[str, int], user_level: int) -> Effects:
    def lv(uid: str) -> int:
        return levels.get(uid, 0)

    e = UPGRADE_EFFECTS

    income_mult = (1 + LEVEL_INCOME_BONUS * (user_level - 1)) * (
        1 + e["core_boost"] * lv("core_boost")
    )
    mine_rate = (
        (BASE_MINE_RATE + e["cpu"] * lv("cpu"))
        * (1 + e["farm"] * lv("farm"))
        * income_mult
    )
    return Effects(
        tap_power=BASE_TAP_POWER + e["tap_power"] * lv("tap_power"),
        crit_chance=BASE_CRIT_CHANCE + e["crit"] * lv("crit"),
        double_chance=BASE_DOUBLE_CHANCE + e["double_tap"] * lv("double_tap"),
        energy_max=BASE_ENERGY_MAX + e["energy_max"] * lv("energy_max"),
        energy_regen=BASE_ENERGY_REGEN,
        heat_decay=BASE_HEAT_DECAY + e["cooling_decay"] * lv("cooling"),
        mine_rate=mine_rate,
        cycle_hours=max(
            MIN_CYCLE_HOURS, MINE_CYCLE_HOURS - e["cooling_cycle"] * lv("cooling")
        ),
        extra_hours=e["battery"] * lv("battery"),
        income_mult=income_mult,
        xp_mult=1 + e["xp_boost"] * lv("xp_boost"),
        ref_share=min(REF_SHARE_CAP, BASE_REF_SHARE + e["ref_boost"] * lv("ref_boost")),
    )
