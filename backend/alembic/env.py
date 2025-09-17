import asyncio
from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config
from app.config import settings
from app.db import Base
from app import models  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)
target_metadata = Base.metadata

def offline():
    context.configure(url=settings.database_url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction(): context.run_migrations()

async def online():
    engine = async_engine_from_config(config.get_section(config.config_ini_section), prefix="sqlalchemy.")
    async with engine.connect() as connection:
        def run_migrations(sync_connection):
            context.configure(connection=sync_connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()

        await connection.run_sync(run_migrations)
    await engine.dispose()

if context.is_offline_mode(): offline()
else: asyncio.run(online())
