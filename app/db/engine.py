from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

engine = create_async_engine(get_settings().database_url, echo=False)
SessionMaker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    from app.constants import DEFAULT_PRICE_UZS, MARKET_MAKER_ID
    from app.db import models

    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    # системные строки: платформенный аккаунт (id 0, копит комиссии) и курс (id 1)
    async with SessionMaker() as session:
        if await session.get(models.User, MARKET_MAKER_ID) is None:
            session.add(
                models.User(id=MARKET_MAKER_ID, username="platform", first_name="Platform")
            )
        if await session.get(models.MarketConfig, 1) is None:
            session.add(
                models.MarketConfig(
                    id=1, base_uzs=DEFAULT_PRICE_UZS, target_uzs=DEFAULT_PRICE_UZS
                )
            )
        await session.commit()
