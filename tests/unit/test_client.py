# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals

import re
from datetime import datetime

try:
    # noinspection PyCompatibility
    from queue import Queue
except ImportError:
    # noinspection PyUnresolvedReferences,PyCompatibility
    from Queue import Queue

import pytest
from celery import states
from mock import mock

from clearly.client import ClearlyClient
from clearly.serializer import TaskInfo, WorkerInfo
from clearly.utils.colors import strip_colors


@pytest.fixture
def mocked_client():
    with mock.patch('clearly.server.ClearlyServer') as mocked_server:
        yield ClearlyClient(mocked_server)


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


@pytest.fixture(params=(True, False, None))
def tristate(request):
    yield request.param


@pytest.fixture(params=(states.PENDING, states.SUCCESS, states.FAILURE, states.RETRY))
def state_type(request):
    # contains a transient state, a successfully finished, and a failure.
    yield request.param


@pytest.mark.parametrize('method', [
    'start', 'stop', 'reset'
])
def test_client_proxy_methods(method, mocked_client):
    getattr(mocked_client, method)()
    getattr(mocked_client._clearly_server, method).assert_called_once()


def test_client_seen_tasks_do_print(mocked_client, capsys):
    tasks = ['app{i}.task{i}'.format(i=i) for i in range(3)]
    mocked_client._clearly_server.seen_tasks.return_value = tasks
    mocked_client.seen_tasks()
    generated = filter(None, capsys.readouterr().out.split('\n'))
    assert all(any(re.search(re.escape(t), x) for x in generated) for t in tasks)


def _prepare_capture(mocked_client, obj):
    q = Queue()
    q.put_nowait(obj)
    q.put_nowait(None)
    mocked_client._clearly_server.client_connect.return_value.__enter__.return_value = q


def test_client_capture_task(state_type, bool1, bool2, mocked_client_display):
    task = TaskInfo('name', 'routing_key', 'uuid', 'retries', 'args', 'kwargs',
                    'result', 'traceback', 123.1, state_type, 'created')
    _prepare_capture(mocked_client_display, task)
    mocked_client_display.capture(success=bool1, error=bool2)
    show_result = (state_type == states.SUCCESS and bool1) \
                  or (state_type in (states.FAILURE, states.RETRY) and bool2)
    mocked_client_display._display_task.assert_called_once_with(task, False, show_result)


def test_client_capture_ignore_unknown(mocked_client_display):
    unknown = 'what?'
    _prepare_capture(mocked_client_display, unknown)
    mocked_client_display.capture()
    mocked_client_display._display_task.assert_not_called()


def test_client_capture_worker(mocked_client_display):
    worker = WorkerInfo('hostname', 'pid', 'sw_sys', 'sw_ident', 'sw_ver',
                        'loadavg', 'processed', 'alive', 'freq', 234.2)
    _prepare_capture(mocked_client_display, worker)
    mocked_client_display.capture()
    mocked_client_display._display_worker.assert_called_once_with(worker, True)


def test_client_stats_do_print(mocked_client, capsys):
    stats = 1234, 5678, 2244, 333  # task_count, event_count, tasks, workers
    mocked_client._clearly_server.stats.return_value = stats
    mocked_client.stats()
    generated = capsys.readouterr().out
    assert all(re.search(str(x), generated) for x in stats)


def test_client_tasks(state_type, bool1, bool2, tristate, mocked_client_display):
    task = TaskInfo('name', 'routing_key', 'uuid', 'retries', 'args', 'kwargs',
                    'result', 'traceback', 123.1, state_type, 'created')
    mocked_client_display._clearly_server.tasks.return_value = (task,)
    mocked_client_display.tasks(success=bool1, error=bool2, params=tristate)
    show_result = (state_type == states.SUCCESS and bool1) \
                  or (state_type in (states.FAILURE, states.RETRY) and bool2)
    show_params = tristate if tristate is not None else show_result
    mocked_client_display._display_task.assert_called_once_with(task, show_params, show_result)


def test_client_workers(bool1, mocked_client_display):
    worker = WorkerInfo('hostname', 'pid', 'sw_sys', 'sw_ident', 'sw_ver',
                        'loadavg', 'processed', 'alive', 'freq', 234.2)
    mocked_client_display._clearly_server.workers.return_value = (worker,)
    mocked_client_display.workers(stats=bool1)
    mocked_client_display._display_worker.assert_called_once_with(worker, bool1)


def test_client_task(bool1, mocked_client_display):
    task = TaskInfo('name', 'routing_key', 'uuid', 'retries', 'args', 'kwargs',
                    'result', 'traceback', 123.1, 'state', 'created')
    mocked_client_display._clearly_server.task.return_value = task if bool1 else None
    mocked_client_display.task('uuid')
    if bool1:
        mocked_client_display._display_task.assert_called_once_with(task, True, True)
    else:
        mocked_client_display._display_task.assert_not_called()


@pytest.fixture(params=[
    (None, None),
    (False, 'False'),
    (0, '0'),
    ('nice', "'nice'"),
], ids=lambda x: str(x[0]))
def task_result_expected(request):
    yield request.param


@pytest.fixture(params=(None, datetime(2018, 1, 1)))
def task_created(request):
    yield request.param


@pytest.fixture(params=(None, 'traceback'))
def task_tb(request):
    yield request.param


def test_client_display_task(bool1, bool2, task_result_expected, task_created,
                             task_tb, mocked_client, capsys):
    task_result, task_expected = task_result_expected
    task = TaskInfo('name', 'routing_key', 'uuid', 'retries', 'abc123', 'def456',
                    task_result, task_tb, 123.1, 'state', task_created)

    with mock.patch('clearly.client.ClearlyClient._task_state') as m_task_state:
        mocked_client._display_task(task, params=bool1, result=bool2)
    generated = strip_colors(capsys.readouterr().out)

    assert task.name in generated
    assert task.uuid in generated

    if task_created:
        assert task.routing_key in generated
        m_task_state.assert_not_called()
    else:
        m_task_state.assert_called_once_with(task.state)

    # params
    assert bool1 == (task.args in generated)
    assert bool1 == (task.kwargs in generated)

    # result
    if bool2:
        assert '==> ' + (task_expected or task_tb or ':)') in generated


@pytest.fixture(params=(None, 123456789))
def worker_heartbeat(request):
    yield request.param


def test_client_display_worker(bool1, bool2, worker_heartbeat, mocked_client, capsys):
    worker = WorkerInfo('hostname', 'pid', 'sw_sys', 'sw_ident', 'sw_ver',
                        'loadavg', 'processed', bool2, 'freq', worker_heartbeat)

    with mock.patch('clearly.client.ClearlyClient._worker_state') as m_worker_state:
        mocked_client._display_worker(worker, stats=bool1)
    generated = strip_colors(capsys.readouterr().out)

    m_worker_state.assert_called_once_with(bool2)
    assert worker.hostname in generated
    assert worker.pid in generated

    # stats
    assert bool1 == ('sw_sys' in generated)
    assert bool1 == ('sw_ident' in generated)
    assert bool1 == ('sw_ver' in generated)
    assert bool1 == ('loadavg' in generated)

    # alive
    assert (bool1 and bool2) == ('heartbeat:' in generated)


def test_client_task_state(state_type, mocked_client):
    result = mocked_client._task_state(state_type)
    assert state_type in result


def test_client_worker_state(bool1, mocked_client):
    result = mocked_client._worker_state(bool1)
    assert bool1 and 'ONLINE' or 'OFFLINE' in result
