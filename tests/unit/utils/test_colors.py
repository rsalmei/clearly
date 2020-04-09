import re

import pytest

from clearly.utils.colors import Colors


@pytest.fixture(scope='session', params=('', 'Tests are fun!', 'rogério'))
def text(request):
    yield request.param


@pytest.fixture(scope='session', params=(f for f in Colors.__dict__ if not f.startswith('_')))
def color_func(request):
    yield getattr(Colors, request.param)


def test_escape_color(color_func, text):
    assert re.match(r'\033\[.+?m{}\033\[0m'.format(text), color_func(text))
