# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals

import re

import mock
import pytest

from clearly.event_core.events import TaskData, WorkerData
from clearly.event_core.streaming_dispatcher import CapturingClient, StreamingDispatcher

try:
    # noinspection PyCompatibility
    from queue import Queue, Empty
except ImportError:  # pragma: no cover
    # noinspection PyUnresolvedReferences,PyCompatibility
    from Queue import Queue, Empty


@pytest.fixture
def dispatcher():
    with mock.patch('threading.Thread'):
        yield StreamingDispatcher(Queue())


@pytest.fixture(params=(False, True))
def bool1(request):
    return request.param


@pytest.fixture(params=(False, True))
def bool2(request):
    return request.param


def test_dispatcher_new_streaming_client(dispatcher, bool1, bool2):
    with dispatcher.streaming_client('tasks_regex', bool1,
                                     'workers_regex', bool2) as q_client:
        assert dispatcher.observers[-1].queue == q_client
        assert dispatcher.observers[-1].task_regex == re.compile('tasks_regex')
        assert dispatcher.observers[-1].worker_regex == re.compile('workers_regex')
        assert dispatcher.observers[-1].task_negate == bool1
        assert dispatcher.observers[-1].worker_negate == bool2


@pytest.mark.parametrize('event_data, path, change, accepts_params', [
    (TaskData(name='name', routing_key='routing_key', uuid='uuid', retries=5,
              args='args', kwargs='kwargs', result='result', traceback='traceback',
              timestamp=123.1, state='state', pre_state='other', created=False),
     'task_states', dict(uuid='roger'), ('task_regexp', 35, 'name', 'routing_key')),
    (WorkerData(hostname='hostname', pid=12000, sw_sys='sw_sys', sw_ident='sw_ident',
                sw_ver='sw_ver', loadavg='loadavg', processed='processed',
                alive=True, freq=5, last_heartbeat=1, state='state', pre_state='other', created=False),
     'worker_states', dict(pid=6700), ('worker_regexp', 47, 'hostname')),
])
def test_dispatcher_dispatch(event_data, path, change, accepts_params, bool1, dispatcher):
    q = Queue()
    cc = CapturingClient(q, 'task_regexp', 35, 'worker_regexp', 47)
    dispatcher.observers.append(cc)

    with mock.patch('clearly.event_core.streaming_dispatcher.StreamingDispatcher.generate_states') as gs, \
            mock.patch('clearly.event_core.streaming_dispatcher.accepts') as acc:
        gs.return_value = (change,)
        acc.return_value = bool1

        dispatcher._dispatch(event_data)

    acc.assert_called_once_with(*accepts_params)
    if bool1:  # accepted or not
        gs.assert_called_once_with(event_data, getattr(dispatcher, path))
        to_client = q.get_nowait()
        assert all(getattr(to_client, k) == v for k, v in change.items())
    else:
        gs.assert_not_called()


def test_dispatcher_generate_states(bool1, dispatcher):
    event_data = TaskData(created=bool1, name='name', routing_key='routing_key', uuid='uuid', retries=5,
                          args='args', kwargs='kwargs', result='result', traceback='traceback',
                          timestamp=123.1, state='state', pre_state='other')
    with mock.patch.object(dispatcher.task_states, 'states_through') as st:
        st.return_value = ('middle',)
        gen = StreamingDispatcher.generate_states(event_data, dispatcher.task_states)
        if bool1:
            assert next(gen)['state'] == '-'
        assert next(gen)['state'] == 'middle'
        with pytest.raises(StopIteration):
            next(gen)
