import re
from queue import Queue
from unittest import mock
from unittest.mock import DEFAULT, call

import pytest

from clearly.protos.clearly_pb2 import TaskMessage, WorkerMessage
from clearly.protos.clearly_pb2 import PatternFilter
from clearly.server.streaming_dispatcher import StreamingDispatcher, Role


@pytest.fixture(params=Role.__members__.values())
def dispatcher(request):
    with mock.patch('threading.Thread'):
        yield StreamingDispatcher(Queue(), request.param)


def test_dispatcher_new_streaming_client(dispatcher, bool1):
    q = Queue()
    with dispatcher.streaming_capture(PatternFilter(pattern='regex', negate=bool1), q):
        assert dispatcher.observers[0] == (q, re.compile('regex'), bool1)
    assert dispatcher.observers == []


def test_dispatcher_streaming_client_dont_leak(dispatcher):
    q = Queue()
    try:
        with dispatcher.streaming_capture(PatternFilter(pattern='regex', negate=False), q):
            1 / 0
    except:
        pass
    assert dispatcher.observers == []


@pytest.fixture
def task_message():
    with mock.patch('clearly.utils.data.TASK_OP'):
        yield TaskMessage(name='name', routing_key='routing_key', uuid='uuid', retries=5,
                          args='args', kwargs='kwargs', result='result', traceback='traceback',
                          timestamp=123.1, state='state')


@pytest.fixture
def worker_message():
    with mock.patch('clearly.utils.data.WORKER_OP'):
        yield WorkerMessage(hostname='hostname', pid=12000, sw_sys='sw_sys', sw_ident='sw_ident',
                            sw_ver='sw_ver', loadavg=[1., 2., 3.], processed=123,
                            freq=5, timestamp=123.1, state='state', heartbeats=[1])


def test_dispatcher_dispatch(task_message, worker_message, dispatcher):
    from clearly.utils.data import TASK_OP, WORKER_OP
    message, op = (task_message, TASK_OP) if dispatcher.role == Role.TASKS \
        else (worker_message, WORKER_OP)
    q = Queue()
    observer = q, 'compiled', False
    dispatcher.observers.append(observer)

    with mock.patch('clearly.utils.data._accept') as mock_accept:
        mock_accept.return_value = False
        # noinspection PyProtectedMember
        dispatcher._dispatch('not cool')

        mock_accept.return_value = True
        # noinspection PyProtectedMember
        dispatcher._dispatch(message)

    assert mock_accept.call_args == call('compiled', False, op())
    assert q.get_nowait() == message
