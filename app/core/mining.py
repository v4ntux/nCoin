from dataclasses import dataclass
from datetime import datetime


@dataclass
class MiningView:
    mined: int          # готово к сбору сейчас
    capacity: int       # максимум за окно (rate * window)
    window_hours: float  # cycle + battery-экстра
    elapsed_hours: float
    progress: float     # 0..1 заполнения окна
    ready_in_sec: int   # 0 = окно заполнено


def mining_view(
    started_at: datetime,
    now: datetime,
    rate_per_hour: float,
    cycle_hours: float,
    extra_hours: float,
) -> MiningView:
    """Линейное накопление от started_at, стоп на границе окна."""
    window = cycle_hours + extra_hours
    elapsed = max(0.0, (now - started_at).total_seconds() / 3600)
    effective = min(elapsed, window)
    mined = int(effective * rate_per_hour)
    capacity = int(window * rate_per_hour)
    return MiningView(
        mined=mined,
        capacity=capacity,
        window_hours=window,
        elapsed_hours=elapsed,
        progress=min(1.0, elapsed / window) if window > 0 else 1.0,
        ready_in_sec=max(0, int((window - elapsed) * 3600)),
    )
