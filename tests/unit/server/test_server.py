from unittest import mock

import pytest

from clearly.protos.clearly_pb2 import CaptureRequest, FilterTasksRequest, FilterWorkersRequest, \
    Null, PatternFilter, RealtimeMessage, TaskMessage, WorkerMessage
from clearly.server.server import RPCService


@pytest.fixture
def mocked_rpc():
    with mock.patch('clearly.server.server.RPCService._log_request'):
        yield RPCService(mock.Mock(), mock.MagicMock(), mock.MagicMock())


def test_server_capture_realtime(tristate, mocked_rpc):
    capture_data, queue_data = {}, []
    if tristate is not True:  # enters in False and None
        capture_data.update(tasks_capture=PatternFilter(pattern='tp', negate=True))
        queue_data.append(TaskMessage(timestamp=123.1))
    if tristate is not False:  # enters in True and None
        capture_data.update(workers_capture=PatternFilter(pattern='wp', negate=False))
        queue_data.append(WorkerMessage(timestamp=123.2))
    request = CaptureRequest(**capture_data)

    mdt = mocked_rpc.dispatcher_tasks.streaming_capture
    mdw = mocked_rpc.dispatcher_workers.streaming_capture

    with mock.patch('queue.Queue.get') as mqg:
        mqg.side_effect = queue_data
        gen = mocked_rpc.capture_realtime(request, None)

        if tristate is not True:
            result = next(gen)
            mdt.assert_called_once_with(PatternFilter(pattern='tp', negate=True), mock.ANY)
            assert result == RealtimeMessage(task=TaskMessage(timestamp=123.1))
        if tristate is not False:
            result = next(gen)
            mdw.assert_called_once_with(PatternFilter(pattern='wp', negate=False), mock.ANY)
            assert result == RealtimeMessage(worker=WorkerMessage(timestamp=123.2))


def test_server_filter_tasks(mocked_rpc):
    request = FilterTasksRequest(tasks_filter=PatternFilter(pattern='tp', negate=True))
    task = mock.Mock()
    mocked_rpc.memory.tasks_by_time.return_value = (('_', task),)

    with mock.patch('clearly.server.server.accept_task') as ma, \
            mock.patch('clearly.server.server.obj_to_message') as otm:
        ma.return_value = True
        otm.return_value = 'asd'
        gen = mocked_rpc.filter_tasks(request, None)
        result = next(gen)

    otm.assert_called_once_with(task, TaskMessage)
    assert result == 'asd'


def test_server_filter_tasks_empty(mocked_rpc):
    mlmt = mocked_rpc.memory.tasks_by_time
    mlmt.return_value = ()

    gen = mocked_rpc.filter_tasks(FilterTasksRequest(), None)
    with pytest.raises(StopIteration):
        next(gen)


def test_server_filter_workers(mocked_rpc):
    request = FilterWorkersRequest(workers_filter=PatternFilter(pattern='wp', negate=True))
    worker = mock.Mock()
    mocked_rpc.memory.workers.values.return_value = (worker,)

    with mock.patch('clearly.server.server.accept_worker') as ma, \
            mock.patch('clearly.server.server.obj_to_message') as otm:
        ma.return_value = True
        otm.return_value = 'asd'
        gen = mocked_rpc.filter_workers(request, None)
        result = next(gen)

    otm.assert_called_once_with(worker, WorkerMessage)
    assert result == 'asd'


def test_server_filter_workers_empty(mocked_rpc):
    mocked_rpc.memory.workers.values.return_value = ()

    gen = mocked_rpc.filter_workers(FilterWorkersRequest(), None)
    with pytest.raises(StopIteration):
        next(gen)


def test_server_seen_tasks(mocked_rpc):
    expected = ('t1', 't2')
    mlmtt = mocked_rpc.memory.task_types
    mlmtt.return_value = expected

    result = mocked_rpc.seen_tasks(Null(), None)

    assert result.task_types == list(expected)


def test_server_reset_tasks(mocked_rpc):
    mocked_rpc.reset_tasks(Null(), None)

    assert mocked_rpc.memory.clear_tasks.call_count == 1


def test_server_get_stats(mocked_rpc):
    mlm = mocked_rpc.memory
    mlm.task_count = 1
    mlm.event_count = 2
    mlm.tasks.__len__ = mock.Mock(return_value=3)
    mlm.workers.__len__ = mock.Mock(return_value=4)

    result = mocked_rpc.get_metrics(Null(), None)

    assert result.task_count == 1
    assert result.event_count == 2
    assert result.len_tasks == 3
    assert result.len_workers == 4
