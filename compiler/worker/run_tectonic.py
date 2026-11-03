import os
import signal
import subprocess
import tempfile
from pathlib import Path

from worker.errors import CompileFailedError, CompileTimeoutError

TECTONIC = os.environ.get("TECTONIC_BIN", "tectonic")
TIMEOUT_SECONDS = 10  # rule 12
LOG_TAIL_CHARS = 2000
# Fixed so the PDF's creation date does not change between runs (determinism, EX-2).
SOURCE_DATE_EPOCH = "0"


def compile_tex(tex: str, assets: dict[str, bytes]) -> bytes:
    """Compile one document in a throwaway directory and return the PDF bytes."""
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        (work / "main.tex").write_text(tex, encoding="utf-8")
        for path, data in assets.items():
            target = work / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        out = work / "out"
        out.mkdir()
        output = _run(tectonic_command(out), cwd=work)
        pdf = out / "main.pdf"
        if not pdf.is_file():
            raise CompileFailedError(output[-LOG_TAIL_CHARS:])
        return pdf.read_bytes()


def tectonic_command(out: Path) -> list[str]:
    return [
        TECTONIC,
        "--untrusted",  # rule 12: refuses -Z shell-escape and -Z search-path
        "--only-cached",  # rule 12: never fetch packages at compile time
        "-Z",
        "deterministic-mode",
        "--outdir",
        str(out),
        "main.tex",
    ]


def _run(command: list[str], *, cwd: Path) -> str:
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=_environment(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
        start_new_session=True,  # so a timeout can kill Tectonic and anything it started
    )
    try:
        output, _ = process.communicate(timeout=TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        raise CompileTimeoutError from None
    return output


def _environment() -> dict[str, str]:
    keep = ("PATH", "HOME", "XDG_CACHE_HOME")
    env = {k: os.environ[k] for k in keep if k in os.environ}
    env["SOURCE_DATE_EPOCH"] = SOURCE_DATE_EPOCH
    return env


def cache_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "tectonic"


def is_ready() -> bool:
    """Tectonic runs and its package cache is populated, so --only-cached can work."""
    try:
        subprocess.run([TECTONIC, "--version"], capture_output=True, timeout=5, check=True)
    except (OSError, subprocess.SubprocessError):
        return False
    cache = cache_dir()
    return cache.is_dir() and any(cache.iterdir())
