from unittest import mock

import pytest

from clearly.utils.env_params import get_env_int, get_env_int_tuple, get_env_tuple, get_env_param, \
    get_env_str


def test_retrieve_correct_var():
    with mock.patch('os.getenv') as mocked_getenv:
        get_env_param('NAME', 1, int)
        mocked_getenv.assert_called_once_with('NAME')


@pytest.mark.parametrize('value, func, expected', [
    ('123', get_env_str, '123'),
    ('123', get_env_int, 123),
    ('123', get_env_tuple, ('123',)),
    ('123', get_env_int_tuple, (123,)),
    ('cool', get_env_str, 'cool'),
    ('cool', get_env_int, None),
    ('cool', get_env_tuple, ('cool',)),
    ('cool', get_env_int_tuple, None),
    ('12 34', get_env_str, '12 34'),
    ('12 34', get_env_int, None),
    ('12 34', get_env_tuple, ('12', '34',)),
    ('12 34', get_env_int_tuple, (12, 34,)),
    ('very cool', get_env_str, 'very cool'),
    ('very cool', get_env_int, None),
    ('very cool', get_env_tuple, ('very', 'cool',)),
    ('very cool', get_env_int_tuple, None),
    (None, get_env_str, None),
    (None, get_env_int, None),
    (None, get_env_tuple, None),
    (None, get_env_int_tuple, None),
])
def test_convert_values(value, func, expected):
    with mock.patch('os.getenv') as mocked_getenv:
        mocked_getenv.return_value = value
        assert func('A_VAR', None) == expected
