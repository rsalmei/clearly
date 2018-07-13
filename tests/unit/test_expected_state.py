# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals

import pytest
from celery.events.state import Task, Worker
from celery.states import FAILURE, PENDING, RECEIVED, REJECTED, RETRY, REVOKED, STARTED, SUCCESS
from mock import mock

from clearly.expected_state import setup_task_states, setup_worker_states


@pytest.mark.parametrize('state_initial, state, expected', [
    (False, False, []),
    (False, True, [True]),
    (True, True, []),
    (True, False, [False]),
])
def test_expected_states_worker(state_initial, state, expected):
    with mock.patch('celery.events.state.Worker.alive', new_callable=mock.PropertyMock) as m_alive:
        m_alive.side_effect = (state_initial, state)
        worker, states = Worker(), setup_worker_states()
        with states.track_changes(worker):
            pass
    assert list(states.states_through()) == expected


@pytest.mark.parametrize('state_initial, state, expected', [
    (PENDING, PENDING, []),
    (PENDING, RECEIVED, [RECEIVED]),
    (PENDING, STARTED, [RECEIVED, STARTED]),
    (PENDING, SUCCESS, [RECEIVED, STARTED, SUCCESS]),
    (PENDING, FAILURE, [RECEIVED, STARTED, FAILURE]),
    (PENDING, REJECTED, [RECEIVED, STARTED, REJECTED]),
    (PENDING, REVOKED, [RECEIVED, STARTED, REVOKED]),
    (PENDING, RETRY, [RECEIVED, STARTED, RETRY]),
    (RECEIVED, PENDING, ValueError),
    (RECEIVED, RECEIVED, []),
    (RECEIVED, STARTED, [STARTED]),
    (RECEIVED, SUCCESS, [STARTED, SUCCESS]),
    (RECEIVED, FAILURE, [STARTED, FAILURE]),
    (RECEIVED, REJECTED, [STARTED, REJECTED]),
    (RECEIVED, REVOKED, [STARTED, REVOKED]),
    (RECEIVED, RETRY, [STARTED, RETRY]),
    (STARTED, PENDING, ValueError),
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
    (RETRY, PENDING, ValueError),
    (RETRY, RECEIVED, [RECEIVED]),
    (RETRY, STARTED, [RECEIVED, STARTED]),
    (RETRY, SUCCESS, [RECEIVED, STARTED, SUCCESS]),
    (RETRY, FAILURE, [RECEIVED, STARTED, FAILURE]),
    (RETRY, REJECTED, [RECEIVED, STARTED, REJECTED]),
    (RETRY, REVOKED, [RECEIVED, STARTED, REVOKED]),
    (RETRY, RETRY, []),
])
def test_expected_states_task(state_initial, state, expected):
    with mock.patch('celery.events.state.Task.state', new_callable=mock.PropertyMock) as m_state:
        m_state.side_effect = (state_initial, state)
        task, states = Task(), setup_task_states()
        with states.track_changes(task):
            pass

    if isinstance(expected, list):
        assert list(states.states_through()) == expected
    else:
        with pytest.raises(expected):
            list(states.states_through())
