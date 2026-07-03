from datetime import datetime


def energy_at(
    energy: float,
    synced_at: datetime,
    now: datetime,
    energy_max: float,
    regen_per_sec: float,
) -> float:
    """Энергия на момент now при ленивом пересчёте от synced_at."""
    elapsed = max(0.0, (now - synced_at).total_seconds())
    return min(energy_max, energy + elapsed * regen_per_sec)
