from app.constants import xp_to_next


def gain_xp(xp: int, level: int, amount: int) -> tuple[int, int, int]:
    """Возвращает (new_xp, new_level, levels_gained). XP копится внутри уровня."""
    xp += amount
    gained = 0
    while xp >= xp_to_next(level):
        xp -= xp_to_next(level)
        level += 1
        gained += 1
    return xp, level, gained
