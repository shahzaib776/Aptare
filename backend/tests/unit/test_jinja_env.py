from pathlib import Path

import pytest
from jinja2.exceptions import SecurityError

from app.services.render.jinja_env import make_environment


def test_latex_delimiters_are_used_and_curly_braces_are_left_alone(tmp_path: Path) -> None:
    env = make_environment(tmp_path)

    out = env.from_string(r"\textbf{\VAR{name}} {{ not a variable }}").render(name="Ada")

    assert out == r"\textbf{Ada} {{ not a variable }}"


def test_a_template_cannot_reach_python_internals(tmp_path: Path) -> None:
    env = make_environment(tmp_path)

    with pytest.raises(SecurityError):
        env.from_string(r"\VAR{ ''.__class__.__mro__ }").render()
