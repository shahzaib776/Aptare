from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from jinja2.sandbox import SandboxedEnvironment

from app.services.render.escape import href_target


def make_environment(templates_dir: Path) -> Environment:
    """A Jinja environment whose delimiters cannot clash with LaTeX."""
    # Sandboxed because TP-9 will load user-written templates inside the API process.
    env = SandboxedEnvironment(
        loader=FileSystemLoader(templates_dir),
        block_start_string=r"\BLOCK{",
        block_end_string="}",
        variable_start_string=r"\VAR{",
        variable_end_string="}",
        comment_start_string=r"\#{",
        comment_end_string="}",
        line_statement_prefix="%%",
        line_comment_prefix="%#",
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        # TP-6: text is escaped once, in escape.py; Jinja autoescape would escape it twice.
        autoescape=False,
        undefined=StrictUndefined,
    )
    env.filters["href"] = href_target
    return env
