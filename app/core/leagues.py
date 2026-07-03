from app.constants import LEAGUES


def league_for(total_earned: int) -> dict:
    current = LEAGUES[0]
    for lg in LEAGUES:
        if total_earned >= lg["min"]:
            current = lg
    return current


def league_progress(total_earned: int) -> dict:
    """Текущая лига + прогресс до следующей (для карточки в топе)."""
    cur = league_for(total_earned)
    idx = next(i for i, lg in enumerate(LEAGUES) if lg["key"] == cur["key"])
    nxt = LEAGUES[idx + 1] if idx + 1 < len(LEAGUES) else None
    if nxt:
        span = nxt["min"] - cur["min"]
        progress = (total_earned - cur["min"]) / span if span else 1.0
    else:
        progress = 1.0
    return {
        "key": cur["key"],
        "name": cur["name"],
        "min": cur["min"],
        "next": {"key": nxt["key"], "name": nxt["name"], "min": nxt["min"]} if nxt else None,
        "progress": round(min(1.0, progress), 4),
    }


def league_bounds(key: str) -> tuple[int, int | None]:
    """[min, max) по total_earned для фильтра лидерборда."""
    for i, lg in enumerate(LEAGUES):
        if lg["key"] == key:
            hi = LEAGUES[i + 1]["min"] if i + 1 < len(LEAGUES) else None
            return lg["min"], hi
    return 0, None
