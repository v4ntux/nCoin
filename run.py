"""Точка входа: FastAPI (Web App + API) + aiogram-бот + маркет-кипер в одном процессе."""

import asyncio
import logging

import uvicorn

from app.config import get_settings
from app.db.engine import init_db
from app.web.app import create_app

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger("ncoin")


async def _run_web() -> None:
    """Веб-сервер; занятый порт не валит процесс — бот продолжает работать."""
    settings = get_settings()
    server = uvicorn.Server(
        uvicorn.Config(
            create_app(), host=settings.host, port=settings.port, log_level="info"
        )
    )
    try:
        await server.serve()
    except (SystemExit, OSError):
        log.error(
            "Web server failed to start — port %s is busy. "
            "Close the other process or change PORT in .env. Bot keeps running.",
            settings.port,
        )


async def _run_bot() -> None:
    """Поллинг бота; при падении (плохой токен, сеть) остальное живёт."""
    try:
        from app.bot.factory import create_bot, create_dispatcher

        bot = create_bot()
        dp = create_dispatcher()
        log.info("bot polling started")
        await dp.start_polling(bot)
    except Exception:
        log.exception("bot polling stopped — web keeps running")


async def _market_keeper() -> None:
    """Держит биржевой курс в коридоре админа fake-сделками маркетмейкера."""
    from app.db.engine import SessionMaker
    from app.services.exchange import keep_price_in_band

    while True:
        try:
            async with SessionMaker() as session:
                moved = await keep_price_in_band(session)
                if moved:
                    await session.commit()
        except Exception:
            log.exception("market keeper tick failed")
        await asyncio.sleep(60)


async def main() -> None:
    settings = get_settings()
    await init_db()

    tasks = [
        asyncio.create_task(_run_web(), name="web"),
        asyncio.create_task(_market_keeper(), name="market"),
    ]
    if settings.bot_token:
        tasks.append(asyncio.create_task(_run_bot(), name="bot"))
    else:
        log.warning("BOT_TOKEN is empty — running web only")

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("bye")
