from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

engine = create_async_engine(get_settings().database_url, echo=False)
SessionMaker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    from app.constants import (
        BAND_MAX_MULT,
        BAND_MIN_MULT,
        BASE_PRICE_MICRO,
        MARKET_MAKER_ID,
    )
    from app.db import models

    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    # системные строки: маркетмейкер (id 0) и конфиг рынка (id 1)
    async with SessionMaker() as session:
        if await session.get(models.User, MARKET_MAKER_ID) is None:
            session.add(
                models.User(id=MARKET_MAKER_ID, username="market", first_name="Market")
            )
        if await session.get(models.MarketConfig, 1) is None:
            session.add(
                models.MarketConfig(
                    id=1,
                    official_micro=BASE_PRICE_MICRO,
                    day_min_micro=int(BASE_PRICE_MICRO * BAND_MIN_MULT),
                    day_max_micro=int(BASE_PRICE_MICRO * BAND_MAX_MULT),
                )
            )
        await session.commit()
