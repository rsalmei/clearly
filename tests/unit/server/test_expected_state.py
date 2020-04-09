import pytest
# noinspection PyProtectedMember
from celery.states import FAILURE, PENDING, RECEIVED, REJECTED, RETRY, REVOKED, STARTED, SUCCESS

from clearly.server.expected_state import setup_task_states


@pytest.mark.parametrize('state_initial, state, expected', [
    (STARTED, 'orange', ValueError),
    ('banana', RECEIVED, ValueError),
    ('banana', 'orange', ValueError),
    (PENDING, PENDING, []),
    (PENDING, RECEIVED, [RECEIVED]),
    (PENDING, STARTED, [RECEIVED, STARTED]),
    (PENDING, SUCCESS, [RECEIVED, STARTED, SUCCESS]),
    (PENDING, FAILURE, [RECEIVED, STARTED, FAILURE]),
    (PENDING, REJECTED, [RECEIVED, STARTED, REJECTED]),
    (PENDING, REVOKED, [RECEIVED, STARTED, REVOKED]),
    (PENDING, RETRY, [RECEIVED, STARTED, RETRY]),
    (RECEIVED, PENDING, [STARTED, RETRY, PENDING]),
    (RECEIVED, RECEIVED, []),
    (RECEIVED, STARTED, [STARTED]),
    (RECEIVED, SUCCESS, [STARTED, SUCCESS]),
    (RECEIVED, FAILURE, [STARTED, FAILURE]),
    (RECEIVED, REJECTED, [STARTED, REJECTED]),
    (RECEIVED, REVOKED, [STARTED, REVOKED]),
    (RECEIVED, RETRY, [STARTED, RETRY]),
    (STARTED, PENDING, [RETRY, PENDING]),
    (STARTED, RECEIVED, [RETRY, RECEIVED]),
    (STARTED, STARTED, []),
    (STARTED, SUCCESS, [SUCCESS]),
    (STARTED, FAILURE, [FAILURE]),
    (STARTED, REJECTED, [REJECTED]),
    (STARTED, REVOKED, [REVOKED]),
    (STARTED, RETRY, [RETRY]),
    (SUCCESS, PENDING, UserWarning),
    (SUCCESS, RECEIVED, UserWarning),
    (SUCCESS, STARTED, UserWarning),
    (SUCCESS, SUCCESS, []),
    (SUCCESS, FAILURE, UserWarning),
    (SUCCESS, REJECTED, UserWarning),
    (SUCCESS, REVOKED, UserWarning),
    (SUCCESS, RETRY, UserWarning),
    (FAILURE, PENDING, UserWarning),
    (FAILURE, RECEIVED, UserWarning),
    (FAILURE, STARTED, UserWarning),
    (FAILURE, SUCCESS, UserWarning),
    (FAILURE, FAILURE, []),
    (FAILURE, REJECTED, UserWarning),
    (FAILURE, REVOKED, UserWarning),
    (FAILURE, RETRY, UserWarning),
    (REJECTED, PENDING, UserWarning),
    (REJECTED, RECEIVED, UserWarning),
    (REJECTED, STARTED, UserWarning),
    (REJECTED, SUCCESS, UserWarning),
    (REJECTED, FAILURE, UserWarning),
    (REJECTED, REJECTED, []),
    (REJECTED, REVOKED, UserWarning),
    (REJECTED, RETRY, UserWarning),
    (REVOKED, PENDING, UserWarning),
    (REVOKED, RECEIVED, UserWarning),
    (REVOKED, STARTED, UserWarning),
    (REVOKED, SUCCESS, UserWarning),
    (REVOKED, FAILURE, UserWarning),
    (REVOKED, REJECTED, UserWarning),
    (REVOKED, REVOKED, []),
    (REVOKED, RETRY, UserWarning),
    (RETRY, PENDING, [PENDING]),
    (RETRY, RECEIVED, [RECEIVED]),
    (RETRY, STARTED, [RECEIVED, STARTED]),
    (RETRY, SUCCESS, [RECEIVED, STARTED, SUCCESS]),
    (RETRY, FAILURE, [RECEIVED, STARTED, FAILURE]),
    (RETRY, REJECTED, [RECEIVED, STARTED, REJECTED]),
    (RETRY, REVOKED, [RECEIVED, STARTED, REVOKED]),
    (RETRY, RETRY, []),
])
def test_expected_states_task(state_initial, state, expected):
    states = setup_task_states()

    if isinstance(expected, list):
        assert list(states.states_through(state_initial, state)) == expected
    else:
        with pytest.raises(expected):
            list(states.states_through(state_initial, state))
