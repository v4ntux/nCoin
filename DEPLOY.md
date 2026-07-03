# Деплой nCoin на Railway

Пошагово: GitHub → Railway → подключение Web App к боту.

---

## 0. Что понадобится

- Токен бота от [@BotFather](https://t.me/BotFather) (`/newbot` или `/token`).
- Твой Telegram **user id** для админки (узнать: [@userinfobot](https://t.me/userinfobot)).
- Аккаунт [github.com](https://github.com) и [railway.com](https://railway.com).

> ⚠️ **Безопасность.** Токен, который светился в переписке, лучше перевыпустить:
> в @BotFather → `/revoke` → получить новый. `.env` в репозиторий НЕ попадёт
> (он в `.gitignore`), токен зададим переменной окружения прямо в Railway.

---

## 1. Залить код на GitHub

`gh` CLI не установлен, поэтому репозиторий создаём руками на сайте:

1. Открой https://github.com/new
2. Repository name: `ncoin` (или любое). Visibility: **Private** (рекомендую — это продукт с ботом).
   **Не** ставь галочки «Add README / .gitignore / license» — они уже есть в проекте.
3. Нажми **Create repository** и скопируй адрес вида `https://github.com/USERNAME/ncoin.git`.

Затем в папке проекта (я уже сделал `git init` и первый коммит):

```bash
git remote add origin https://github.com/USERNAME/ncoin.git
git branch -M main
git push -u origin main
```

---

## 2. Создать проект на Railway

1. Открой https://railway.com/new → **Deploy from GitHub repo**.
2. Дай Railway доступ к своему GitHub, выбери репозиторий `ncoin`.
3. Railway сам увидит Python (Nixpacks), поставит зависимости из `requirements.txt`
   и запустит `python run.py` (это прописано в `railway.json`).

---

## 3. Переменные окружения (Railway → проект → Variables)

Добавь:

| Ключ | Значение | Зачем |
|---|---|---|
| `BOT_TOKEN` | токен от BotFather | бот |
| `ADMIN_IDS` | твой id (напр. `5939110751`) | доступ к админке |
| `DEV_MODE` | `false` | **ОБЯЗАТЕЛЬНО** — иначе любой сможет войти как админ |
| `DATABASE_URL` | `sqlite+aiosqlite:////data/ncoin.db` | БД на volume (см. шаг 5) |
| `CHANNEL_URL` | `https://t.me/твойканал` | ссылка в задании «подписка» (опц.) |
| `WEBAPP_URL` | пока пусто, заполним в шаге 4 | кнопка Play в боте |

`PORT` и `HOST` задавать НЕ нужно — Railway сам подставит порт, приложение его читает.

---

## 4. Публичный домен → подключить к боту

1. Railway → проект → **Settings → Networking → Generate Domain**.
   Получишь адрес вида `https://ncoin-production.up.railway.app`.
2. Впиши его в переменную `WEBAPP_URL` (шаг 3) и сохрани — Railway передеплоит.
3. Привяжи Web App к боту в **@BotFather**:
   - `/setmenubutton` → выбери бота → пришли URL домена → задай текст кнопки (напр. «Play»).
   - (Опц.) `/newapp` — оформить полноценное Telegram Mini App.
4. Проверка: открой бота, `/start` → кнопка «🚀 Play nCoin».
   Админка: `/panel` в чате бота → откроется `/admin.html`.

---

## 5. Чтобы данные не пропадали при передеплое (volume)

SQLite на Railway по умолчанию лежит в контейнере и **обнуляется при каждом
передеплое**. Чтобы сохранять игроков/баланс:

1. Railway → проект → сервис → **Settings → Volumes → New Volume**.
2. Mount path: `/data`.
3. Убедись, что `DATABASE_URL = sqlite+aiosqlite:////data/ncoin.db` (4 слэша = абсолютный путь).

> Позже, при росте, лучше перейти на Postgres (Railway → New → Database → PostgreSQL,
> и `DATABASE_URL = postgresql+asyncpg://...`; в коде поменять драйвер и добавить `asyncpg`).
> Для старта SQLite на volume достаточно.

---

## 6. Локальный запуск (для разработки)

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env             # заполнить BOT_TOKEN, ADMIN_IDS; DEV_MODE=true для теста в браузере
python run.py
```

Веб: http://localhost:8000 · Админка: http://localhost:8000/admin.html
(в `DEV_MODE=true` браузер входит как dev-юзер, админка — под id из `ADMIN_IDS`).

---

## Частые проблемы

- **Бот не отвечает / 409 Conflict** — запущено два процесса с одним токеном
  (напр. локально + на Railway). Оставь один. `numReplicas` в `railway.json` = 1.
- **Кнопка Play не появилась** — не задан `WEBAPP_URL` или он не `https://`.
- **Админка «Admins only»** — твой id не в `ADMIN_IDS`, либо `DEV_MODE` не тот.
- **Данные пропали после деплоя** — не подключён volume (шаг 5).
- **Build упал на Python** — проверь, что есть `.python-version` (3.12) и `requirements.txt`.
