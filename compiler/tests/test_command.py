from pathlib import Path

from worker.run_tectonic import tectonic_command


def test_command_keeps_the_sandbox_flags() -> None:
    """Rule 12. Removing --untrusted changes no compile result, so only this test notices."""
    command = tectonic_command(Path("/work/out"))
    assert "--untrusted" in command
    assert "--only-cached" in command
    assert command[command.index("-Z") + 1] == "deterministic-mode"
    assert not any("shell-escape" in part for part in command)
