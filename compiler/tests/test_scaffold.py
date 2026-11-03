import worker


def test_package_imports() -> None:
    assert worker.__name__ == "worker"
