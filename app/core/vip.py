from app.constants import VIP_TIERS


def withdraw_per_week(tier: int) -> int:
    return VIP_TIERS.get(tier, VIP_TIERS[0])["withdraw_per_week"]


def tier_name(tier: int) -> str:
    return VIP_TIERS.get(tier, VIP_TIERS[0])["name"]


def tier_for_deposit(total_usd: float) -> int:
    """Максимальный тир, который покрывает суммарный депозит."""
    best = 0
    for tier, info in VIP_TIERS.items():
        if total_usd >= info["deposit_usd"] and info["deposit_usd"] > 0:
            best = max(best, tier)
    return best
