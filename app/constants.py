"""Весь игровой баланс в одном месте. Тюнить экономику — здесь.

Ни один модуль не должен хардкодить игровые числа у себя.
"""

APP_VERSION = "0.6.0"

# ---------------------------------------------------------------- валюта (UZS)
# Единственный баланс — Coin. Цена коина назначается людьми в UZS (целые сумы).
# USD убран: платформа — только эскроу коинов + чат P2P-сделок между людьми.
DEFAULT_PRICE_UZS = 1500        # старт: 1 Coin = 1500 UZS (официальный курс)
PRICE_GLIDE_SEC = 300           # цена доезжает до цели админа за 5 минут
COIN_USD_RATE = 0.0013  # legacy: не используется в UI, оставлено для старого ядра

# ---------------------------------------------------------------- P2P-сделки
P2P_FEE_BP = 100                # комиссия с продажи: 100 бп = 1.00% (из коинов)
P2P_MIN_AD_COINS = 10           # минимум коинов в объявлении
P2P_MAX_ACTIVE_ADS = 6          # максимум активных объявлений на юзера
P2P_PAY_WINDOW_SEC = 900        # окно оплаты покупателя, сек (15 мин) → авто-отмена
# способы оплаты объявления (ключ → человекочитаемое имя)
PAY_METHODS = {
    "card": "Bank card",
    "humo": "HUMO",
    "uzcard": "UZCARD",
    "payme": "Payme",
    "click": "Click",
    "cash": "Cash",
}

# ---------------------------------------------------------------- дневной кап
# Коин зарабатывается ТОЛЬКО за задания/эвенты и не больше кэпа в день —
# чтобы коин был дорог и держал цену. Tap/mining выпилены из продукта.
DAILY_EARN_CAP = 150            # максимум заработанных Coin в день (задания+эвенты)
EARN_CAP_REASONS = {"task", "daily", "event", "mining", "tap", "combo"}

# ---------------------------------------------------------------- тапы
BASE_TAP_POWER = 1
MAX_TAPS_PER_SEC = 12        # анти-чит: кап тапов между батчами
BASE_CRIT_CHANCE = 0.05      # шанс крита
CRIT_MULTIPLIER = 10         # крит = power * 10
BASE_DOUBLE_CHANCE = 0.0     # шанс x2 (открывается апгрейдом)
COMBO_STEP = 50              # каждые N тапов подряд — бонус
COMBO_BONUS_PER_POWER = 8    # бонус = tap_power * 8 (сложнее фармить)
COMBO_RESET_GAP = 6.0        # сек тишины, после которых комбо сгорает

# ---------------------------------------------------------------- энергия
BASE_ENERGY_MAX = 1000
BASE_ENERGY_REGEN = 1 / 6    # ед/сек — медленнее восстановление, реже тапы

# ---------------------------------------------------------------- heat
HEAT_MAX = 100.0
HEAT_PER_TAP = 2.0
BASE_HEAT_DECAY = 3.0        # ед/сек
OVERHEAT_LOCK_SECONDS = 30

# ---------------------------------------------------------------- майнинг
BASE_MINE_RATE = 5.0         # Coin/час — в 4× медленнее пассив
MINE_CYCLE_HOURS = 2.0       # базовый цикл накопления
MIN_CYCLE_HOURS = 0.5        # ниже cooling не уводит

# ---------------------------------------------------------------- уровни
XP_PER_COIN = 0.1            # 1 XP за каждые 10 заработанных Coin
LEVEL_INCOME_BONUS = 0.01    # +1% ко всему доходу за уровень


def xp_to_next(level: int) -> int:
    return int(100 * level**1.35)


# ---------------------------------------------------------------- рефералы
REF_BONUS_NEW = 500          # новичку, пришедшему по ссылке
REF_BONUS_INVITER = 1000     # пригласившему
BASE_REF_SHARE = 0.03        # доля с Collect друга
REF_SHARE_CAP = 0.08

# ---------------------------------------------------------------- daily reward
DAILY_REWARDS = [100, 200, 400, 700, 1200, 2000, 5000]  # день 1..7, дальше день 7

# ---------------------------------------------------------------- VIP / кошелёк
# Тир = слоты вывода в неделю + скидка на ВСЕ комиссии. Депозит в реальных доллах.
VIP_TIERS = {
    0: {"name": "Free", "deposit_usd": 0, "withdraw_per_week": 0},
    1: {"name": "VIP 1", "deposit_usd": 10, "withdraw_per_week": 1},
    2: {"name": "VIP 2", "deposit_usd": 50, "withdraw_per_week": 2},
    3: {"name": "VIP 3", "deposit_usd": 150, "withdraw_per_week": 4},
}
VIP_FEE_MULT = {0: 1.0, 1: 0.75, 2: 0.5, 3: 0.25}  # множитель комиссий по тиру

# Комиссии (базовые, до VIP-скидки)
TRADE_FEE = 0.02      # биржа: с выручки продавца (USD)
P2P_FEE = 0.02        # перевод Coin
WITHDRAW_FEE = 0.05   # сверх суммы вывода

WITHDRAW_MIN_USD = 0.5          # минимальный вывод, USD
P2P_MIN_COINS = 100
P2P_DAILY_LIMIT_COINS = 300     # анти-слив: дневной кап отправки Coin

# ---------------------------------------------------------------- биржа (P2P Coin↔USD)
# Цены и балансы USD — в микро-доллах (int). 1 USD = 1_000_000 micro.
USD_MICRO = 1_000_000
BASE_PRICE_MICRO = int(COIN_USD_RATE * USD_MICRO)  # 1300 micro = 0.0013 USD
BAND_MIN_MULT = 0.8    # дефолтный дневной коридор вокруг официального курса
BAND_MAX_MULT = 1.2
KEEPER_STEP = 0.25     # доля разрыва, на которую fake-сделка тянет цену к официальной
MARKET_MAKER_ID = 0    # системный юзер маркетмейкера
ORDER_MIN_COINS = 100
ORDER_MIN_TOTAL_MICRO = 50_000  # сделка не меньше 0.05 USD
MAX_OPEN_ORDERS = 8

# ---------------------------------------------------------------- лиги (по total_earned)
LEAGUES = [
    {"key": "bronze",   "name": "Bronze",   "min": 0},
    {"key": "silver",   "name": "Silver",   "min": 10_000},
    {"key": "gold",     "name": "Gold",     "min": 50_000},
    {"key": "platinum", "name": "Platinum", "min": 250_000},
    {"key": "diamond",  "name": "Diamond",  "min": 1_000_000},
    {"key": "legend",   "name": "Legend",   "min": 5_000_000},
]

# ---------------------------------------------------------------- новости / ивенты
NEWS = [
    {
        "id": "exchange", "tag": "NEW", "title": "Exchange is live",
        "text": "Trade Coin for USD with player-set prices. You are the market.",
    },
    {
        "id": "x2mining", "tag": "SOON", "title": "x2 Mining Weekend",
        "text": "Double mining rates for 48 hours. Charge your batteries.",
    },
    {
        "id": "battle", "tag": "SOON", "title": "Battle Mode",
        "text": "PvP tap battles for a Coin pot. Winner takes all.",
    },
]

# ---------------------------------------------------------------- апгрейды
# effect_per_level интерпретирует app/core/upgrades.py по id.
UPGRADES: dict[str, dict] = {
    # ── ветка Tap ──
    "tap_power": {
        "branch": "tap", "name": "Tap Power", "emoji": "👆",
        "desc": "+1 Coin за тап", "base_cost": 200, "mult": 1.6, "max_level": 50,
    },
    "crit": {
        "branch": "tap", "name": "Critical", "emoji": "⚡",
        "desc": "+1% шанс крита x10", "base_cost": 600, "mult": 1.8, "max_level": 15,
    },
    "double_tap": {
        "branch": "tap", "name": "Double Tap", "emoji": "✌️",
        "desc": "+2% шанс двойного тапа", "base_cost": 800, "mult": 1.9, "max_level": 15,
    },
    "energy_max": {
        "branch": "tap", "name": "Energy Cell", "emoji": "🔋",
        "desc": "+250 к запасу энергии", "base_cost": 500, "mult": 1.7, "max_level": 20,
    },
    # ── ветка Mining ──
    "cpu": {
        "branch": "mining", "name": "CPU", "emoji": "🖥",
        "desc": "+5 Coin/час майнинга", "base_cost": 300, "mult": 1.55, "max_level": 40,
    },
    "battery": {
        "branch": "mining", "name": "Battery", "emoji": "🪫",
        "desc": "+30 мин накопления сверх цикла", "base_cost": 700, "mult": 1.75, "max_level": 12,
    },
    "cooling": {
        "branch": "mining", "name": "Cooling", "emoji": "❄️",
        "desc": "-5 мин цикла, +0.5/с распад Heat", "base_cost": 900, "mult": 1.8, "max_level": 12,
    },
    "farm": {
        "branch": "mining", "name": "Farm", "emoji": "🏭",
        "desc": "+25% ко всему майнингу", "base_cost": 5000, "mult": 2.2, "max_level": 8,
    },
    # ── ветка Global ──
    "core_boost": {
        "branch": "global", "name": "Core Boost", "emoji": "🌐",
        "desc": "+2% ко всему доходу", "base_cost": 2000, "mult": 2.0, "max_level": 20,
    },
    "xp_boost": {
        "branch": "global", "name": "XP Boost", "emoji": "✨",
        "desc": "+10% XP", "base_cost": 1500, "mult": 1.9, "max_level": 10,
    },
    "ref_boost": {
        "branch": "global", "name": "Ref Boost", "emoji": "🤝",
        "desc": "+0.5% доля с майнинга друзей", "base_cost": 2500, "mult": 2.0, "max_level": 10,
    },
}

# Эффекты на уровень (числа, которые применяет core/upgrades.py)
UPGRADE_EFFECTS = {
    "tap_power": 1,        # +Coin за тап
    "crit": 0.01,          # +шанс крита
    "double_tap": 0.02,    # +шанс x2
    "energy_max": 250,     # +энергия
    "cpu": 5.0,            # +Coin/час
    "battery": 0.5,        # +часов накопления сверх цикла
    "cooling_cycle": 5 / 60,   # -часов цикла
    "cooling_decay": 0.5,      # +распад heat/сек
    "farm": 0.25,          # +25% майнинг
    "core_boost": 0.02,    # +2% всё
    "xp_boost": 0.10,      # +10% xp
    "ref_boost": 0.005,    # +0.5% реф. доля
}

# ---------------------------------------------------------------- задания
# kind: open | taps | collect | earn | invite | link
TASKS: dict[str, dict] = {
    "d_open": {
        "cat": "daily", "name": "Open the app", "emoji": "📲",
        "goal": 1, "reward": 50, "xp": 10, "kind": "open",
    },
    "d_collect3": {
        "cat": "daily", "name": "Collect 3 times", "emoji": "⛏",
        "goal": 3, "reward": 150, "xp": 30, "kind": "collect",
    },
    "d_taps500": {
        "cat": "daily", "name": "Make 500 taps", "emoji": "👆",
        "goal": 500, "reward": 100, "xp": 20, "kind": "taps",
    },
    "d_invite": {
        "cat": "daily", "name": "Invite a friend", "emoji": "👥",
        "goal": 1, "reward": 300, "xp": 50, "kind": "invite",
    },
    "w_coins3000": {
        "cat": "weekly", "name": "Earn 3 000 Coin", "emoji": "🪙",
        "goal": 3000, "reward": 1000, "xp": 150, "kind": "earn",
    },
    "w_invite5": {
        "cat": "weekly", "name": "Invite 5 friends", "emoji": "🤝",
        "goal": 5, "reward": 2500, "xp": 300, "kind": "invite",
    },
    "w_collect20": {
        "cat": "weekly", "name": "Collect 20 times", "emoji": "🏭",
        "goal": 20, "reward": 800, "xp": 120, "kind": "collect",
    },
    "s_channel": {
        "cat": "special", "name": "Join our channel", "emoji": "📢",
        "goal": 1, "reward": 500, "xp": 100, "kind": "link", "url": "",
    },
    "s_partner": {
        "cat": "special", "name": "Partner quest", "emoji": "🎁",
        "goal": 1, "reward": 1000, "xp": 150, "kind": "link", "url": "https://telegram.org",
    },
}
