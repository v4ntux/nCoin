# nCoin — Design v0.1.0

Гибрид кликера и пассивного майнинга в Telegram Web App. Цель v0.1.0 — чистая,
расширяемая база: вся экономика через леджер, весь баланс в одном файле,
чистое ядро без I/O.

## Стек

- **Бот:** Python, aiogram 3.x (polling)
- **API:** FastAPI + uvicorn (тот же процесс, что и бот)
- **БД:** SQLite через SQLAlchemy 2.0 async (`create_all` на старте; alembic — позже)
- **Фронт:** статический Web App (vanilla ES-modules, без сборки), стиль iOS 26
  liquid glass: тёмная тема, полупрозрачные карточки, backdrop-blur, неоновое ядро

## Архитектура

```
run.py                 — точка входа: bot polling + uvicorn в одном asyncio-цикле
app/
  config.py            — настройки из .env (pydantic-settings)
  constants.py         — ВЕСЬ игровой баланс (единственный файл для тюнинга)
  db/                  — модели + engine
  core/                — чистая игровая логика, без I/O (легко тестировать)
  services/            — оркестрация core + db (транзакции, события задач)
  bot/                 — aiogram: /start, рефералка, админка, аппрув выводов
  web/                 — FastAPI: auth (initData HMAC), REST для Web App
webapp/                — фронт (index.html + css + js)
```

## Экономика

- **Coin** — целое число, единственная майнящаяся валюта.
- **Dollar** — производная: `usd = coins * COIN_USD_RATE`. Не хранится, только отображается.
- **Леджер:** каждое движение Coin — строка в `ledger` (amount ±, reason, meta).
  Балансы на User денормализованы для скорости, леджер — источник правды и
  фундамент для депозитов/выводов/P2P/биржи.

## Механики v0.1.0

| Механика | Как работает |
|---|---|
| Tap | батчи тапов с клиента; сервер клампит по энергии, катает криты, ведёт комбо |
| Energy | max 1000 базово, реген 1/3с; лениво пересчитывается из таймстампов |
| Heat | +2/тап, распад со временем; 100 → OVERHEAT, тапы заблокированы на N сек |
| Mining | цикл 2ч, линейное накопление, Collect; Battery продлевает накопление сверх цикла |
| Upgrades | 3 ветки: Tap / Mining / Global; цена = base * mult^level |
| Levels | XP за доход и задачи; +1% ко всему доходу за уровень |
| Referrals | стартовый бонус обоим + 3% (апгрейдится) с каждого Collect друга |
| Tasks | Daily / Weekly / Special; period_key (день/ISO-неделя/all), прогресс событиями |
| Daily reward | стрик 7 дней, растущие награды, сброс при пропуске |
| VIP | депозит → тир; слоты вывода в неделю: free 0 / VIP1 1 / VIP2 2 / VIP3 4 |
| P2P | перевод Coin юзеру по id, комиссия 2% |
| Withdraw | заявка → админу в бот с кнопками Approve/Decline, монеты в эскроу |

## Не в v0.1.0 (заложено схемой/леджером, включим позже)

Boost-магазин (x2 mining, auto-collect), TON Keeper, Marketplace, Staking,
Exchange, PvP, Clan, NFT, Battle Pass, Events, push-уведомления «майнинг готов»
(нужен scheduler), мультиязычность фронта.

## Анти-чит (минимум для v0.1)

- Все начисления считает сервер; клиент шлёт только количество тапов.
- Батч тапов клампится по энергии, накопленной по серверному времени.
- Кап тапов в секунду (`MAX_TAPS_PER_SEC`) между батчами.
- Heat — экономический тормоз автокликеров.

## API (все под /api, auth = заголовок X-Init-Data, в dev — X-Dev-User)

```
POST /api/auth            регистрация/логин, полный стейт
GET  /api/state           снапшот (энергия/жар/майнинг пересчитаны)
POST /api/tap             {count} → начислено, криты, комбо
POST /api/collect         сбор майнинга (+ доля рефереру)
GET  /api/upgrades        каталог с ценами/уровнями
POST /api/upgrades/buy    {id}
GET  /api/tasks           задачи с прогрессом
POST /api/tasks/claim     {id}
POST /api/daily/claim     дневная награда (стрик)
GET  /api/friends         рефералы + ссылка
GET  /api/leaderboard     ?by=coins|referrals|level
GET  /api/wallet          VIP, слоты вывода, курс
POST /api/wallet/transfer {to, amount}  P2P
POST /api/wallet/withdraw {amount_coins}
GET  /api/profile         статистика из леджера
```
