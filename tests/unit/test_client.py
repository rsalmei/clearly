# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals

import re

import pytest
from celery import states
from mock import mock

from clearly.client import ClearlyClient
from clearly.protos import clearly_pb2
from clearly.utils import worker_states
from clearly.utils.colors import strip_colors

try:
    # noinspection PyCompatibility
    from queue import Queue
except ImportError:
    # noinspection PyUnresolvedReferences,PyCompatibility
    from Queue import Queue


@pytest.fixture
def mocked_client():
    with mock.patch('clearly.client.grpc.insecure_channel'), \
         mock.patch('clearly.client.clearly_pb2_grpc.ClearlyServerStub'):
        yield ClearlyClient()


@pytest.fixture
def mocked_client_display(mocked_client):
    with mock.patch('clearly.client.ClearlyClient._display_task'), \
         mock.patch('clearly.client.ClearlyClient._display_worker'):
        yield mocked_client


@pytest.fixture(params=(True, False))
def bool1(request):
    yield request.param


@pytest.fixture(params=(True, False))
def bool2(request):
    yield request.param


@pytest.fixture(params=(True, False))
def bool3(request):
    yield request.param


@pytest.fixture(params=(True, False, None))
def tristate(request):
    yield request.param


@pytest.fixture(params=sorted(states.ALL_STATES))
def task_state_type(request):
    yield request.param


@pytest.fixture(params=sorted(worker_states.ALL_STATES))
def worker_state_type(request):
    yield request.param


@pytest.mark.parametrize('method', [
    'reset'
])
def test_client_proxy_methods(method, mocked_client):
    getattr(mocked_client, method)()
    getattr(mocked_client.stub, method).assert_called_once()


def test_client_seen_tasks_do_print(mocked_client, capsys):
    tasks = ['app{i}.task{i}'.format(i=i) for i in range(3)]
    mocked_client.stub.seen_tasks.return_value = tasks
    mocked_client.seen_tasks()
    generated = filter(None, capsys.readouterr().out.split('\n'))
    assert all(any(re.search(re.escape(t), x) for x in generated) for t in tasks)


def test_client_capture_task(tristate, bool1, bool2, mocked_client_display):
    task = clearly_pb2.TaskMessage(name='name', routing_key='routing_key', uuid='uuid', retries=2,
                                   args='args', kwargs='kwargs', result='result', traceback='traceback',
                                   timestamp=123.1, state='ANY', created=False)
    mocked_client_display.stub.capture_realtime.return_value = (clearly_pb2.RealtimeEventMessage(task=task),)
    mocked_client_display.capture(params=tristate, success=bool1, error=bool2)
    mocked_client_display._display_task.assert_called_once_with(task, tristate, bool1, bool2)


def test_client_capture_ignore_unknown(mocked_client_display):
    mocked_client_display.stub.capture_realtime.return_value = (clearly_pb2.RealtimeEventMessage(),)
    mocked_client_display.capture()
    mocked_client_display._display_task.assert_not_called()


def test_client_capture_worker(bool1, mocked_client_display):
    worker = clearly_pb2.WorkerMessage(hostname='hostname', pid=12000, sw_sys='sw_sys', sw_ident='sw_ident',
                                       sw_ver='sw_ver', loadavg=[1.0, 2.0, 3.0], processed=5432, state='state',
                                       alive=True, freq=5, last_heartbeat=234.2)
    mocked_client_display.stub.capture_realtime.return_value = (clearly_pb2.RealtimeEventMessage(worker=worker),)
    mocked_client_display.capture(stats=bool1)
    mocked_client_display._display_worker.assert_called_once_with(worker, bool1)


def test_client_stats_do_print(mocked_client, capsys):
    stats = 1234, 5678, 2244, 333  # task_count, event_count, tasks, workers
    mocked_client.stub.stats.return_value = stats
    mocked_client.stats()
    generated = capsys.readouterr().out
    assert all(re.search(str(x), generated) for x in stats)


def test_client_tasks(tristate, bool1, bool2, mocked_client_display):
    task = clearly_pb2.TaskMessage(name='name', routing_key='routing_key', uuid='uuid', retries=2,
                                   args='args', kwargs='kwargs', result='result', traceback='traceback',
                                   timestamp=123.1, state='ANY', created=False)
    mocked_client_display.stub.filter_tasks.return_value = (task,)
    mocked_client_display.tasks(params=tristate, success=bool1, error=bool2)
    mocked_client_display._display_task.assert_called_once_with(task, tristate, bool1, bool2)


def test_client_workers(bool1, mocked_client_display):
    worker = clearly_pb2.WorkerMessage(hostname='hostname', pid=12000, sw_sys='sw_sys', sw_ident='sw_ident',
                                       sw_ver='sw_ver', loadavg=[1.0, 2.0, 3.0], processed=5432, state='state',
                                       alive=True, freq=5, last_heartbeat=234.2)
    mocked_client_display.stub.filter_workers.return_value = (worker,)
    mocked_client_display.workers(stats=bool1)
    mocked_client_display._display_worker.assert_called_once_with(worker, bool1)


def test_client_task(bool1, mocked_client_display):
    task = clearly_pb2.TaskMessage(name='name', routing_key='routing_key', uuid='uuid', retries=2,
                                   args='args', kwargs='kwargs', result='result', traceback='traceback',
                                   timestamp=123.1, state='state', created=False)
    mocked_client_display.stub.find_task.return_value = task if bool1 else None
    mocked_client_display.task('uuid')
    if bool1:
        mocked_client_display._display_task.assert_called_once_with(task, True, True, True)
    else:
        mocked_client_display._display_task.assert_not_called()


@pytest.fixture(params=(None, 'traceback'))
def task_tb(request):
    yield request.param


@pytest.fixture(params=(None, '', 'False', '0', "'nice'"))
def task_result(request):
    yield request.param


def test_client_display_task(task_result, tristate, bool1, bool2, bool3,
                             task_state_type, task_tb, mocked_client, capsys):
    task = clearly_pb2.TaskMessage(name='name', routing_key='routing_key', uuid='uuid', retries=2,
                                   args='args123', kwargs='kwargs', result=task_result, traceback=task_tb,
                                   timestamp=123.1, state=task_state_type, created=bool3)

    with mock.patch('clearly.client.ClearlyClient._task_state') as m_task_state:
        mocked_client._display_task(task, params=tristate, success=bool1, error=bool2)
    generated = strip_colors(capsys.readouterr().out)

    assert task.name in generated
    assert task.uuid in generated

    if bool3:
        assert task.routing_key in generated
        m_task_state.assert_not_called()
    else:
        m_task_state.assert_called_once_with(task.state)

    show_result = (task.state in states.EXCEPTION_STATES and bool2) \
                  or (task.state == states.SUCCESS and bool1)

    # params
    first_seen = bool(tristate) and task.created
    result = tristate != False and (task.state in states.READY_STATES) and show_result
    tristate = first_seen or result
    assert tristate == (task.args in generated)
    assert tristate == (task.kwargs in generated)

    # result
    if show_result:
        assert '==> ' + (task_result or task_tb or ':)') in generated


@pytest.fixture(params=(None, 123456789))
def worker_heartbeat(request):
    yield request.param


def test_client_display_worker(bool1, bool2, worker_state_type, worker_heartbeat,
                               mocked_client, capsys):
    worker = clearly_pb2.WorkerMessage(hostname='hostname', pid=12000, sw_sys='sw_sys', sw_ident='sw_ident',
                                       sw_ver='sw_ver', loadavg=[1.0, 2.0, 3.0], processed=5432, alive=bool2,
                                       state=worker_state_type, freq=5, last_heartbeat=worker_heartbeat)

    with mock.patch('clearly.client.ClearlyClient._worker_state') as m_worker_state:
        mocked_client._display_worker(worker, stats=bool1)
    generated = strip_colors(capsys.readouterr().out)

    m_worker_state.assert_called_once_with(worker_state_type)
    assert worker.hostname in generated
    assert str(worker.pid) in generated

    # stats
    assert bool1 == ('sw_sys' in generated)
    assert bool1 == ('sw_ident' in generated)
    assert bool1 == ('sw_ver' in generated)
    assert bool1 == ('[1.0, 2.0, 3.0]' in generated)

    # alive
    assert (bool1 and bool2) == ('heartbeat:' in generated)


def test_client_task_state(task_state_type, mocked_client):
    result = mocked_client._task_state(task_state_type)
    assert task_state_type in result


def test_client_worker_state(worker_state_type, mocked_client):
    result = mocked_client._worker_state(worker_state_type)
    assert worker_state_type in result
