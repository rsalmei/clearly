import copy
from unittest import mock

import pytest
from celery.events.state import Task, Worker

from clearly.event_core.events import TaskData, WorkerData
from clearly.protos import clearly_pb2
from clearly.protos.clearly_pb2 import RealtimeEventMessage, TaskMessage
from clearly.server import ClearlyServer


@pytest.fixture
def mocked_server():
    # noinspection PyTypeChecker
    yield ClearlyServer(mock.Mock(), mock.MagicMock())


def test_server_capture_realtime(mocked_server):
    request = clearly_pb2.CaptureRequest(
        tasks_capture=clearly_pb2.PatternFilter(pattern='tp', negate=True),
        workers_capture=clearly_pb2.PatternFilter(pattern='wp', negate=False),
    )
    event = 'event'
    msc = mocked_server.dispatcher.streaming_client
    msc.return_value.__enter__.return_value.get.return_value = event
    msc.return_value.__exit__.return_value = None  # this makes the context manager not suppress exception!

    with mock.patch('clearly.server.ClearlyServer._event_to_pb') as mepb:
        mepb.return_value = 'task', TaskMessage()
        gen = mocked_server.capture_realtime(request, None)
        result = next(gen)

    msc.assert_called_once_with('tp', True, 'wp', False)
    mepb.assert_called_once_with(event)
    assert result == RealtimeEventMessage(task=TaskMessage())


T_DATA_PB = dict(name='name', routing_key='routing_key', uuid='uuid', retries=5,
                 args='args', kwargs='kwargs', result='result', traceback='traceback',
                 timestamp=123, state='state')
T_DATA = copy.copy(T_DATA_PB)
T_DATA.update(pre_state='other', created=False)  # miss you py3.5
W_DATA_PB = dict(hostname='hostname', pid=12000, sw_sys='sw_sys', sw_ident='sw_ident',
                 sw_ver='sw_ver', loadavg=[1, 2, 3], processed=789789,
                 freq=5)
W_DATA = copy.copy(W_DATA_PB)
W_DATA.update(state='state', pre_state='other', created=False, alive=True, last_heartbeat=1)  # miss you py3.5


# noinspection PyProtectedMember
@pytest.mark.parametrize('event, key, data', [
    (TaskData(**T_DATA), 'task', T_DATA_PB),
    (Task(**T_DATA_PB), 'task', T_DATA_PB),
    (WorkerData(**W_DATA), 'worker', W_DATA_PB),
    (Worker(**W_DATA_PB), 'worker', W_DATA_PB),
])
def test_server_event_to_pb_valid(event, key, data, mocked_server):
    result_key, result_obj = mocked_server._event_to_pb(event)
    assert result_key == key
    assert all(getattr(result_obj, k) == v
               for k, v in data.items())


# noinspection PyProtectedMember
@pytest.mark.parametrize('event, key', [
    (1, ValueError),
    ('wrong', ValueError),
    ({'wrong': True}, ValueError),
])
def test_server_event_to_pb_invalid(event, key, mocked_server):
    with pytest.raises(key):
        mocked_server._event_to_pb(event)


def test_server_filter_tasks(mocked_server):
    request = clearly_pb2.FilterTasksRequest(
        tasks_filter=clearly_pb2.PatternFilter(pattern='tp', negate=True),
        state_pattern='sp',
    )
    mlmt = mocked_server.listener.memory.tasks_by_time
    task = mock.Mock()
    mlmt.return_value = (('ignore', task),)

    with mock.patch('clearly.server.accepts') as ma, \
            mock.patch('clearly.server.ClearlyServer._event_to_pb') as mepb:
        ma.return_value = True
        mepb.return_value = 'asd', 35
        gen = mocked_server.filter_tasks(request, None)
        result = next(gen)

    mepb.assert_called_once_with(task)
    assert result == 35


def test_server_filter_tasks_empty(mocked_server):
    mlmt = mocked_server.listener.memory.tasks_by_time
    mlmt.return_value = ()

    gen = mocked_server.filter_tasks(clearly_pb2.FilterTasksRequest(), None)
    with pytest.raises(StopIteration):
        next(gen)


def test_server_filter_workers(mocked_server):
    request = clearly_pb2.FilterWorkersRequest(
        workers_filter=clearly_pb2.PatternFilter(pattern='wp', negate=True),
    )
    worker = mock.Mock()
    mocked_server.listener.memory.workers.values.return_value = (worker,)

    with mock.patch('clearly.server.accepts') as ma, \
            mock.patch('clearly.server.ClearlyServer._event_to_pb') as mepb:
        ma.return_value = True
        mepb.return_value = 'asd', 35
        gen = mocked_server.filter_workers(request, None)
        result = next(gen)

    mepb.assert_called_once_with(worker)
    assert result == 35


def test_server_filter_workers_empty(mocked_server):
    mocked_server.listener.memory.workers.values.return_value = ()

    gen = mocked_server.filter_workers(clearly_pb2.FilterWorkersRequest(), None)
    with pytest.raises(StopIteration):
        next(gen)


@pytest.mark.parametrize('task', ['found', None])
def test_server_find_task(task, mocked_server):
    request = clearly_pb2.FindTaskRequest(task_uuid='a_uuid')
    mlmtg = mocked_server.listener.memory.tasks.get
    mlmtg.return_value = task

    with mock.patch('clearly.server.ClearlyServer._event_to_pb') as mepb:
        mepb.return_value = 'asd', 35
        result = mocked_server.find_task(request, None)

    if task:
        mepb.assert_called_once_with(task)
        assert result == 35
    else:
        mepb.assert_not_called()
        assert isinstance(result, clearly_pb2.TaskMessage)


def test_server_seen_tasks(mocked_server):
    expected = ('t1', 't2')
    mlmtt = mocked_server.listener.memory.task_types
    mlmtt.return_value = expected

    result = mocked_server.seen_tasks(clearly_pb2.Empty(), None)

    assert result.task_types == list(expected)


def test_server_reset_tasks(mocked_server):
    mocked_server.reset_tasks(clearly_pb2.Empty(), None)

    mocked_server.listener.memory.clear_tasks.assert_called_once()


def test_server_get_stats(mocked_server):
    mlm = mocked_server.listener.memory
    mlm.task_count = 1
    mlm.event_count = 2
    mlm.tasks.__len__ = mock.Mock(return_value=3)
    mlm.workers.__len__ = mock.Mock(return_value=4)

    result = mocked_server.get_stats(clearly_pb2.Empty(), None)

    assert result.task_count == 1
    assert result.event_count == 2
    assert result.len_tasks == 3
    assert result.len_workers == 4
