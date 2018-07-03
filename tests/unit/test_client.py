import re
from Queue import Queue

import pytest
from celery import states
from mock import mock

from clearly.client import ClearlyClient
from clearly.serializer import TaskInfo, WorkerInfo


@pytest.fixture
def mocked_client():
    with mock.patch('clearly.server.ClearlyServer'):
        yield ClearlyClient()


@pytest.fixture
def mocked_client_display():
    with mock.patch('clearly.server.ClearlyServer'), \
         mock.patch('clearly.client.ClearlyClient._display_task'), \
         mock.patch('clearly.client.ClearlyClient._display_worker'):
        yield ClearlyClient()


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


@pytest.fixture(params=(True, False))
def success(request):
    yield request.param


@pytest.fixture(params=(True, False))
def error(request):
    yield request.param


@pytest.mark.parametrize('state', [
    states.PENDING, states.SUCCESS, states.FAILURE,
])
def test_client_capture_task(state, success, error, mocked_client_display):
    task = TaskInfo('name', 'routing_key', 'uuid', 'retries', 'args', 'kwargs',
                    'result', 'traceback', 123.1, state, 'created')
    _prepare_capture(mocked_client_display, task)
    mocked_client_display.capture(success=success, error=error)
    show_result = (state == states.SUCCESS and success) or (state == states.FAILURE and error)
    mocked_client_display._display_task.assert_called_once_with(task, False, show_result)


def test_client_capture_worker(mocked_client_display):
    worker = WorkerInfo('hostname', 'pid', 'sw_sys', 'sw_ident', 'sw_ver',
                        'loadavg', 'processed', 'alive', 'freq', 234.2)
    _prepare_capture(mocked_client_display, worker)
    mocked_client_display.capture()
    mocked_client_display._display_worker.assert_called_once_with(worker, True)
