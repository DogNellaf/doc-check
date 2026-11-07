import shutil

import pytest

from app import config
from app.company import load

HAS_TESSERACT = shutil.which("tesseract") is not None


@pytest.fixture(scope="session")
def company():
    return load(config.COMPANY_DIR)


def example(name: str) -> bytes:
    return (config.EXAMPLES_DIR / name).read_bytes()
