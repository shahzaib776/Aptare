import os
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("args", [["upgrade", "head"], ["downgrade", "base"]])
def test_the_alembic_cli_runs_cleanly(tmp_path: Path, args: list[str]) -> None:
    # The console script, not `python -m alembic`: only the script lacks the cwd on sys.path.
    env = {**os.environ, "DB_URL": f"sqlite:///{tmp_path / 'cli.db'}"}
    env.pop("PYTHONPATH", None)

    result = subprocess.run(
        [str(Path(sys.executable).parent / "alembic"), *args],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_upgrade_creates_a_missing_database_directory(tmp_path: Path) -> None:
    env = {**os.environ, "DB_URL": f"sqlite:///{tmp_path / 'not' / 'yet' / 'here.db'}"}
    env.pop("PYTHONPATH", None)

    result = subprocess.run(
        [str(Path(sys.executable).parent / "alembic"), "upgrade", "head"],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
