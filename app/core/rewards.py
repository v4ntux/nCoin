from datetime import date, timedelta

from app.constants import DAILY_REWARDS


def streak_status(
    streak_day: int, streak_date: str | None, today: date
) -> tuple[bool, int]:
    """(можно ли клеймить сегодня, каким днём стрика будет клейм).

    Пропустил день — стрик сгорает и начинается с 1.
    """
    if streak_date == today.isoformat():
        return False, streak_day
    if streak_date == (today - timedelta(days=1)).isoformat():
        return True, streak_day + 1
    return True, 1


def reward_for_day(day: int) -> int:
    """День 1..7 по таблице, дальше — награда 7-го дня."""
    return DAILY_REWARDS[min(day, len(DAILY_REWARDS)) - 1]
