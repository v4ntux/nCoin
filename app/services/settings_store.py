"""Синглтон настроек: контакты поддержки + конфиг VIP (цены/скидки), из админки."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import VIP_FEE_MULT, VIP_TIERS
from app.db.models import Setting


async def load(session: AsyncSession) -> Setting:
    s = await session.get(Setting, 1)
    if s is None:
        s = Setting(id=1, vip={})
        session.add(s)
        await session.flush()
    return s


def vip_rules(setting: Setting) -> dict[int, dict]:
    """Итоговый конфиг по тирам: name/price/discount(%)/withdraws.

    Значения из настроек админа перекрывают дефолты из constants.
    """
    over = setting.vip or {}
    out: dict[int, dict] = {}
    for tier, info in VIP_TIERS.items():
        o = over.get(str(tier), {})
        default_discount = int(round((1 - VIP_FEE_MULT.get(tier, 1.0)) * 100))
        out[tier] = {
            "tier": tier,
            "name": info["name"],
            "price": float(o.get("price", info["deposit_usd"])),
            "discount": int(o.get("discount", default_discount)),
            "withdraws": int(o.get("withdraws", info["withdraw_per_week"])),
        }
    return out


def discount_mult(rules: dict[int, dict], tier: int) -> float:
    """Множитель комиссии по тиру (1.0 = без скидки, 0.75 = -25%)."""
    return 1 - rules.get(tier, {}).get("discount", 0) / 100


def withdraws_for(rules: dict[int, dict], tier: int) -> int:
    return rules.get(tier, {}).get("withdraws", 0)


def support_view(setting: Setting) -> dict:
    return {
        "tg": setting.support_tg or "",
        "email": setting.support_email or "",
        "text": setting.support_text
        or "Need help? Contact us and we'll get back to you.",
    }
