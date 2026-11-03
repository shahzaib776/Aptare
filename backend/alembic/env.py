from alembic import context
from app.config import Settings
from app.db import make_engine
from app.models.base import Base

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=Settings().db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = make_engine(Settings().db_url)
    with engine.connect() as connection:
        # SQLite can't ALTER most things in place; batch mode rebuilds the table instead.
        context.configure(
            connection=connection, target_metadata=target_metadata, render_as_batch=True
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
