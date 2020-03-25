import re
from typing import Callable

import pytest


@pytest.fixture
def strip_colors() -> Callable[[str], str]:
    def actual(text: str) -> str:
        return re.sub(r'\033\[.+?m', '', text)

    return actual
