# nCoin — Telegram tap & mine game (v0.1.0)

Гибрид кликера и пассивного майнинга: aiogram 3 бот + FastAPI + Telegram Web App.
Архитектура и экономика — в [docs/DESIGN.md](docs/DESIGN.md).

## Запуск

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env           # заполнить BOT_TOKEN, ADMIN_IDS
python run.py
```

Веб поднимется на `http://HOST:PORT`, бот — на polling (если задан `BOT_TOKEN`).

## Web App в Telegram

Telegram требует HTTPS. Для теста:

```bash
ngrok http 8000       # или cloudflared tunnel --url http://localhost:8000
```

Полученный `https://…` адрес → в `.env` → `WEBAPP_URL=`, перезапустить.
Кнопка «Play nCoin» появится в /start.

## Локальная разработка без Telegram

`DEV_MODE=true` в `.env` — фронт в обычном браузере сам входит как dev-юзер
(заголовок `X-Dev-User`). В проде обязательно `DEV_MODE=false`.

## Админка (в чате бота)

- `/admin` — список команд
- `/stats` — юзеры, монеты, ожидающие выводы
- `/give <id> <amount>` — начислить Coin
- `/setvip <id> <0-3>` — выдать VIP после депозита
- Заявки на вывод приходят с кнопками Approve / Decline

## Структура

```
run.py            — bot + web в одном процессе
app/constants.py  — весь игровой баланс
app/core/         — чистая игровая логика
app/services/     — транзакции, леджер, задачи
app/web/          — REST API + auth initData
app/bot/          — aiogram-бот
webapp/           — фронт (vanilla, iOS glass)
```
