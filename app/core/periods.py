from datetime import datetime


def period_key(cat: str, now: datetime) -> str:
    """Ключ периода прогресса задач: daily — день, weekly — ISO-неделя, special — all."""
    if cat == "daily":
        return now.strftime("%Y-%m-%d")
    if cat == "weekly":
        iso = now.isocalendar()
        return f"{iso.year}-W{iso.week:02d}"
    return "all"
