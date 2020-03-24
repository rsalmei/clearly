from unittest import mock

import pytest

from clearly.utils import logo


@pytest.mark.parametrize('system', [
    'client', 'server'
])
def test_logo_has_version(system):
    with mock.patch('clearly.__init__') as mock_init:
        mock_init.__version__ = 'cool'

        assert 'cool' in logo.render(system)
