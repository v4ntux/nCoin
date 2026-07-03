from datetime import datetime


def heat_at(
    heat: float, synced_at: datetime, now: datetime, decay_per_sec: float
) -> float:
    """Heat на момент now: остывает со скоростью decay_per_sec."""
    elapsed = max(0.0, (now - synced_at).total_seconds())
    return max(0.0, heat - elapsed * decay_per_sec)
