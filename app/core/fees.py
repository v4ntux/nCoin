from app.constants import P2P_FEE, TRADE_FEE, VIP_FEE_MULT, WITHDRAW_FEE

_BASE = {"trade": TRADE_FEE, "p2p": P2P_FEE, "withdraw": WITHDRAW_FEE}


def fee_rate(kind: str, vip_tier: int) -> float:
    """Комиссия вида kind с учётом VIP-скидки."""
    return _BASE[kind] * VIP_FEE_MULT.get(vip_tier, 1.0)


def fee_amount(amount: int, kind: str, vip_tier: int) -> int:
    """Комиссия в тех же единицах, что и amount (Coin или micro-USD)."""
    return int(amount * fee_rate(kind, vip_tier))
