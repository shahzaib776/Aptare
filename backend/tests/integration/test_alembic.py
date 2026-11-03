import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[2]


def alembic(db: Path, *args: str) -> subprocess.CompletedProcess[str]:
    # The console script, not `python -m alembic`: only the script lacks the cwd on sys.path.
    env = {**os.environ, "DB_URL": f"sqlite:///{db}"}
    env.pop("PYTHONPATH", None)
    return subprocess.run(
        [str(Path(sys.executable).parent / "alembic"), *args],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
    )


def tables(db: Path) -> set[str]:
    with sqlite3.connect(db) as connection:
        rows = connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return {name for (name,) in rows}


@pytest.mark.parametrize("args", [["upgrade", "head"], ["downgrade", "base"]])
def test_the_alembic_cli_runs_cleanly(tmp_path: Path, args: list[str]) -> None:
    result = alembic(tmp_path / "cli.db", *args)

    assert result.returncode == 0, result.stderr


def test_upgrade_creates_a_missing_database_directory(tmp_path: Path) -> None:
    result = alembic(tmp_path / "not" / "yet" / "here.db", "upgrade", "head")

    assert result.returncode == 0, result.stderr


def test_upgrade_creates_compile_results_and_downgrade_removes_it(tmp_path: Path) -> None:
    db = tmp_path / "up.db"

    assert alembic(db, "upgrade", "head").returncode == 0
    assert "compile_results" in tables(db)

    assert alembic(db, "downgrade", "base").returncode == 0
    assert "compile_results" not in tables(db)


def test_the_migration_matches_the_models(tmp_path: Path) -> None:
    db = tmp_path / "check.db"
    assert alembic(db, "upgrade", "head").returncode == 0

    result = alembic(db, "check")

    assert result.returncode == 0, result.stdout + result.stderr


def test_rebuilding_a_table_keeps_the_rows_of_tables_that_reference_it(tmp_path: Path) -> None:
    """SQLite rebuilds a table by dropping it; with foreign keys on, that cascades to children."""
    work = tmp_path / "work"
    (work / "alembic" / "versions").mkdir(parents=True)
    shutil.copy(BACKEND / "alembic.ini", work)
    shutil.copy(BACKEND / "alembic" / "env.py", work / "alembic")
    shutil.copy(BACKEND / "alembic" / "script.py.mako", work / "alembic")
    versions = work / "alembic" / "versions"
    (versions / "a001.py").write_text(CREATE_PARENT_AND_CHILD)
    (versions / "a002.py").write_text(REBUILD_PARENT)
    db = tmp_path / "fk.db"
    env = {**os.environ, "DB_URL": f"sqlite:///{db}", "PYTHONPATH": str(BACKEND)}

    result = subprocess.run(
        [
            str(Path(sys.executable).parent / "alembic"),
            "-c",
            str(work / "alembic.ini"),
            "upgrade",
            "head",
        ],
        cwd=work,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    with sqlite3.connect(db) as connection:
        assert connection.execute("SELECT COUNT(*) FROM child_rows").fetchone() == (2,)


CREATE_PARENT_AND_CHILD = """
import sqlalchemy as sa
from alembic import op

revision = "a001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("parent_rows", sa.Column("id", sa.Integer(), primary_key=True))
    op.create_table(
        "child_rows",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("parent_rows.id", ondelete="CASCADE")),
    )
    op.execute("INSERT INTO parent_rows (id) VALUES (1)")
    op.execute("INSERT INTO child_rows (id, parent_id) VALUES (1, 1), (2, 1)")


def downgrade() -> None:
    op.drop_table("child_rows")
    op.drop_table("parent_rows")
"""

REBUILD_PARENT = """
import sqlalchemy as sa
from alembic import op

revision = "a002"
down_revision = "a001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("parent_rows", recreate="always") as batch:
        batch.add_column(sa.Column("note", sa.String(), nullable=True))


def downgrade() -> None:
    pass
"""
