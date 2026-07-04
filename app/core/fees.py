from app.constants import P2P_FEE, TRADE_FEE, VIP_FEE_MULT, WITHDRAW_FEE

_BASE = {"trade": TRADE_FEE, "p2p": P2P_FEE, "withdraw": WITHDRAW_FEE}


def fee_rate(kind: str, vip_tier: int, discount_mult: float | None = None) -> float:
    """Комиссия вида kind с учётом VIP-скидки.

    discount_mult — множитель из настроек админа (напр. 0.75 = -25%). Если None,
    берётся дефолт из constants.VIP_FEE_MULT.
    """
    mult = discount_mult if discount_mult is not None else VIP_FEE_MULT.get(vip_tier, 1.0)
    return _BASE[kind] * mult


def fee_amount(
    amount: int, kind: str, vip_tier: int, discount_mult: float | None = None
) -> int:
    """Комиссия в тех же единицах, что и amount (Coin или micro-USD)."""
    return int(amount * fee_rate(kind, vip_tier, discount_mult))
