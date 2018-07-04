from __future__ import absolute_import, print_function, unicode_literals

import re

import pytest

from clearly.utils.colors import colors


@pytest.fixture(scope='session', params=('a', 'A', 'Tests are fun!'))
def text(request):
    yield request.param


@pytest.fixture(scope='session', params=(f for f in colors.__dict__ if not f.startswith('_')))
def color_func(request):
    yield getattr(colors, request.param)


def test_escape_color(color_func, text):
    assert re.match(r'\033\[.+?m{}\033\[0m'.format(text), color_func(text))
