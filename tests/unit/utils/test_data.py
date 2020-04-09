import re
from unittest import mock

import pytest
from celery.events.state import Task, Worker

from clearly.protos.clearly_pb2 import TaskMessage, WorkerMessage
# noinspection PyProtectedMember
from clearly.utils.data import _accept, accept_task, accept_worker, obj_to_message

TASK = dict(name='name', routing_key='routing_key', uuid='uuid', retries=5, args='args',
            kwargs='kwargs', result='result', traceback='traceback', result_meta='meta')

WORKER = dict(hostname='hostname', pid=12000, sw_sys='sw_sys', sw_ident='sw_ident',
              sw_ver='sw_ver', loadavg=[1., 2., 3.], processed=789789, freq=5, heartbeats=[1])


@pytest.mark.parametrize('obj, to_type, data', [
    (Task(**TASK), TaskMessage, TASK),
    (Worker(**WORKER), WorkerMessage, WORKER),
])
def test_server_obj_to_message_valid(obj, to_type, data):
    obj.timestamp, obj.state = 123.1, 'state'
    message = obj_to_message(obj, to_type)
    assert all(getattr(message, k) == v for k, v in data.items())


@pytest.mark.parametrize('obj, to_type', [
    (1, TaskMessage),
    (1, WorkerMessage),
    ('wrong', TaskMessage),
    ('wrong', WorkerMessage),
    ({'wrong': True}, TaskMessage),
    ({'wrong': True}, WorkerMessage),
    (Task(**TASK), WorkerMessage),
    (Worker(**WORKER), TaskMessage),
])
def test_server_obj_to_message_invalid(obj, to_type):
    with pytest.raises(AttributeError):
        obj_to_message(obj, to_type)


@pytest.fixture(params=(True, False))
def negate(request):
    yield request.param


@pytest.mark.parametrize('regex, values, expected', [
    (r'.', ('a',), True),
    (r'.', ('agagfsa', ''), True),
    (r'.', ('', 'ggfdagfds'), True),
    (r'.', ('',), False),
    (r'.', ('', '', ''), False),
    (r'a', ('a',), True),
    (r'a', ('b',), False),
    (r'a', ('', 'zxc', 'qwe', 'bab'), True),
    (r'a', ('bbbbbb', ''), False),
    (r'a', ('', 'bbbabbb', ''), True),
    (r'a', ('',), False),
    (r'ab|ac', ('bbbbaaaa',), False),
    (r'ab|ac', ('bbbbaaaab',), True),
    (r'ab|ac', ('', 'a'), False),
    (r'ab|ac', ('', 'aaaaaa'), False),
    (r'ab|ac', ('aabb', ''), True),
    (r'ab|ac', ('aabb', 'aacc'), True),
    (r'ab|ac', ('aaaa', 'aacc'), True),
    (r'ab|ac', ('aaaa', 'bbbb'), False),
])
def test_data_client_accepts(regex, values, expected, negate):
    assert _accept(re.compile(regex), negate, values) == (expected ^ negate)


def test_accept_tasks():
    pattern = re.compile('pattern')
    with mock.patch('clearly.utils.data._accept') as mock_accept, \
            mock.patch('clearly.utils.data.TASK_OP') as mock_op:
        accept_task(pattern, True, Task(**TASK))
    mock_accept.assert_called_once_with(pattern, True, mock_op())


def test_accept_workers():
    pattern = re.compile('pattern')
    with mock.patch('clearly.utils.data._accept') as mock_accept, \
            mock.patch('clearly.utils.data.WORKER_OP') as mock_op:
        accept_worker(pattern, True, Task(**TASK))
    mock_accept.assert_called_once_with(pattern, True, mock_op())
