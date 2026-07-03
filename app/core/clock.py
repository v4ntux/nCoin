from datetime import datetime, timezone


def utcnow() -> datetime:
    """Naive UTC — единый формат времени во всём проекте (SQLite хранит naive)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def ts(dt: datetime | None) -> float:
    """datetime → epoch-секунды для отдачи клиенту."""
    return dt.replace(tzinfo=timezone.utc).timestamp() if dt else 0.0
