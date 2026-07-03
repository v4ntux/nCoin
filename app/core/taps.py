import random
from dataclasses import dataclass

from app.constants import COMBO_BONUS_PER_POWER, COMBO_STEP, CRIT_MULTIPLIER


@dataclass
class TapResult:
    taps: int
    coins: int         # уже с учётом income_mult, без combo_bonus
    crits: int
    doubles: int
    combo: int         # новое значение комбо-счётчика
    combo_bonus: int   # отдельной строкой в леджер


def resolve_taps(
    taps: int,
    power: int,
    crit_chance: float,
    double_chance: float,
    combo: int,
    income_mult: float,
    rng: random.Random | None = None,
) -> TapResult:
    """Считает батч тапов на сервере. Клиент присылает только количество."""
    r = rng or random
    coins = 0
    crits = 0
    doubles = 0
    for _ in range(taps):
        roll = r.random()
        if roll < crit_chance:
            coins += power * CRIT_MULTIPLIER
            crits += 1
        elif roll < crit_chance + double_chance:
            coins += power * 2
            doubles += 1
        else:
            coins += power

    new_combo = combo + taps
    crossed = new_combo // COMBO_STEP - combo // COMBO_STEP
    bonus = crossed * power * COMBO_BONUS_PER_POWER if crossed > 0 else 0

    return TapResult(
        taps=taps,
        coins=int(coins * income_mult),
        crits=crits,
        doubles=doubles,
        combo=new_combo,
        combo_bonus=int(bonus * income_mult),
    )
