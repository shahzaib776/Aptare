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
        sqlite = connection.dialect.name == "sqlite"
        if sqlite:
            # Batch mode rebuilds a table by dropping it, and with foreign keys on that deletes
            # (cascades to) the rows of every table pointing at it. The pragma is ignored once a
            # transaction has started, so it must come before everything else.
            connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
            connection.commit()  # end the transaction SQLAlchemy opened for the pragma
        # SQLite can't ALTER most things in place; batch mode rebuilds the table instead.
        context.configure(
            connection=connection, target_metadata=target_metadata, render_as_batch=True
        )
        try:
            with context.begin_transaction():
                context.run_migrations()
        finally:
            if sqlite:
                connection.exec_driver_sql("PRAGMA foreign_keys=ON")
                connection.commit()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
