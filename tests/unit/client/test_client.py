import re
from unittest import mock

import grpc
import pytest
from celery.states import EXCEPTION_STATES, PROPAGATE_STATES, SUCCESS

from clearly.client import ClearlyClient, ModeTask, ModeWorker
from clearly.client.client import Modes
from clearly.protos.clearly_pb2 import Null, PatternFilter, RealtimeMessage, SeenTasksMessage, \
    StatsMessage, TaskMessage, WorkerMessage


@pytest.fixture
def mocked_client():
    with mock.patch('grpc.insecure_channel'), \
         mock.patch('clearly.client.client.ClearlyServerStub'):
        yield ClearlyClient()


@pytest.fixture
def mocked_display(mocked_client):
    with mock.patch('clearly.client.ClearlyClient._display_task'), \
         mock.patch('clearly.client.ClearlyClient._display_worker'):
        yield mocked_client


@pytest.fixture
def task_message():
    yield TaskMessage(
        name='name', routing_key='routing_key', uuid='uuid', retries=2,
        args='args', kwargs='kwargs', result='result', traceback='traceback',
        timestamp=123.1, state='ANY', result_meta='meta',
    )


@pytest.fixture
def worker_message():
    yield WorkerMessage(
        hostname='hostname', pid=12000, sw_sys='sw_sys', sw_ident='sw_ident',
        sw_ver='sw_ver', loadavg=[1., 2., 3.], processed=5432, state='state',
        freq=5, heartbeats=[234.2],
    )


# noinspection PyProtectedMember
def test_client_reset(mocked_client):
    mocked_client.reset_tasks()
    mocked_client._stub.reset_tasks.assert_called_once_with(Null())


# noinspection PyProtectedMember
def test_client_seen_tasks_do_print(mocked_client, capsys):
    inner_tasks = ['app{i}.task{i}'.format(i=i) for i in range(3)]
    tasks = SeenTasksMessage()
    tasks.task_types.extend(inner_tasks)
    mocked_client._stub.seen_tasks.return_value = tasks
    mocked_client.seen_tasks()
    generated = filter(None, capsys.readouterr().out.split('\n'))
    assert all(any(re.search(re.escape(t), x) for x in generated) for t in inner_tasks)


# noinspection PyProtectedMember
def test_client_capture_task(task_message, mode_task_type, mocked_display):
    mocked_display._stub.capture_realtime.return_value = \
        (RealtimeMessage(task=task_message),)
    mocked_display.capture(modes=mode_task_type)
    mocked_display._display_task.assert_called_once_with(task_message, mode_task_type)


# noinspection PyProtectedMember
def test_client_capture_ignore_unknown(mocked_display):
    mocked_display._stub.capture_realtime.return_value = (RealtimeMessage(),)
    mocked_display.capture()
    mocked_display._display_task.assert_not_called()
    mocked_display._display_worker.assert_not_called()


# noinspection PyProtectedMember
def test_client_capture_worker(worker_message, mode_worker_type, mocked_display):
    mocked_display._stub.capture_realtime.return_value = \
        (RealtimeMessage(worker=worker_message),)
    mocked_display.capture(modes=mode_worker_type)
    mocked_display._display_worker.assert_called_once_with(worker_message, mode_worker_type)


# noinspection PyProtectedMember
@pytest.mark.parametrize('method, stub', [
    ('capture_tasks', 'capture_realtime'),
    ('capture_workers', 'capture_realtime'),
    ('capture', 'capture_realtime'),
    ('tasks', 'filter_tasks'),
    ('workers', 'filter_workers'),
    ('seen_tasks', 'seen_tasks'),
    ('reset_tasks', 'reset_tasks'),
    ('metrics', 'get_metrics'),
])
def test_client_methods_have_user_friendly_grpc_errors(method, stub, mocked_display, capsys):
    exc = grpc.RpcError()
    exc.code, exc.details = lambda: 'StatusCode', lambda: 'details'
    getattr(mocked_display._stub, stub).side_effect = exc

    with mock.patch.object(mocked_display, '_debug', False):
        getattr(mocked_display, method)()

    generated = capsys.readouterr().out
    assert 'Server communication error' in generated
    assert 'StatusCode' in generated
    assert 'details' in generated


# noinspection PyProtectedMember
@pytest.mark.parametrize('method, stub', [
    ('capture_tasks', 'capture_realtime'),
    ('capture_workers', 'capture_realtime'),
    ('capture', 'capture_realtime'),
    ('tasks', 'filter_tasks'),
    ('workers', 'filter_workers'),
    ('seen_tasks', 'seen_tasks'),
    ('reset_tasks', 'reset_tasks'),
    ('metrics', 'get_metrics'),
])
def test_client_methods_trigger_grpc_errors_when_debugging(method, stub, mocked_client):
    rpc_error = grpc.RpcError()
    rpc_error.details = rpc_error.code = mock.Mock()
    getattr(mocked_client._stub, stub).side_effect = rpc_error
    mocked_client._debug = True

    with mock.patch.object(mocked_client, '_debug', True), pytest.raises(grpc.RpcError):
        getattr(mocked_client, method)()


# noinspection PyProtectedMember
@pytest.mark.parametrize('method', [
    'capture_tasks', 'capture_workers', 'capture', 'tasks', 'workers'
])
def test_client_methods_have_user_friendly_warnings(method, mocked_display, capsys):
    with mock.patch('clearly.client.ClearlyClient._parse_pattern') as mock_parse:
        mock_parse.return_value = None
        getattr(mocked_display, method)()

    generated = capsys.readouterr().out
    assert 'Nothing would be selected.' in generated


def test_client_capture_tasks(mocked_client):
    with mock.patch.object(mocked_client, 'capture') as mocked_capture:
        mocked_client.capture_tasks()
        mocked_capture.assert_called_once_with(
            tasks=mock.ANY, modes=mock.ANY,
            workers='!',
        )


def test_client_capture_workers(mocked_client):
    with mock.patch.object(mocked_client, 'capture') as mocked_capture:
        mocked_client.capture_workers()
        mocked_capture.assert_called_once_with(
            workers=mock.ANY, modes=mock.ANY,
            tasks='!',
        )


# noinspection PyProtectedMember
def test_client_metrics_do_print(mocked_client, capsys):
    data = dict(task_count=1234, event_count=5678, len_tasks=2244, len_workers=333)
    mocked_client._stub.get_metrics.return_value = StatsMessage(**data)
    mocked_client.metrics()
    generated = capsys.readouterr().out
    assert all(re.search(str(x), generated) for x in data.values())


# noinspection PyProtectedMember
def test_client_tasks(task_message, mode_task_type, mocked_display):
    mocked_display._stub.filter_tasks.return_value = (task_message,)
    mocked_display.tasks(mode=mode_task_type)
    mocked_display._display_task.assert_called_once_with(task_message, mode_task_type)


# noinspection PyProtectedMember
def test_client_workers(worker_message, mode_worker_type, mocked_display):
    mocked_display._stub.filter_workers.return_value = (worker_message,)
    mocked_display.workers(mode=mode_worker_type)
    mocked_display._display_worker.assert_called_once_with(worker_message, mode_worker_type)


# noinspection PyProtectedMember
def test_client_display_task(task_message, mode_task_type, mocked_client,
                             task_state_plus_2, capsys, strip_colors):
    if task_state_plus_2 == '?1':
        task_state_type = task_message.state = ''
    elif task_state_plus_2 == '?2':
        task_state_type = task_message.state = SUCCESS
        task_message.result = str(None)
    else:
        task_state_type = task_message.state = task_state_plus_2

    mocked_client._display_task(task_message, mode_task_type)
    generated = strip_colors(capsys.readouterr().out)

    assert task_message.name in generated
    assert task_message.uuid in generated

    if not task_state_type:
        assert task_message.routing_key in generated
    else:
        assert task_state_type in generated

    params, success, error = mode_task_type.spec
    show_outcome = (task_message.state in PROPAGATE_STATES and error) \
        or (task_message.state == SUCCESS and success)

    # params
    first_seen = bool(params) and not task_state_type
    params_outcome = params is not False and show_outcome
    show_params = first_seen or params_outcome
    assert show_params == (task_message.args in generated)
    assert show_params == (task_message.kwargs in generated)

    # outcome
    if show_outcome:
        if task_state_type == SUCCESS:
            if task_message.result == str(None):
                assert '==> <meta> :)' in generated
            else:
                assert '==> <meta> \'result\'' in generated
        elif task_state_type in EXCEPTION_STATES:
            assert '==> traceback' in generated
    else:
        assert '==>' not in generated


# noinspection PyProtectedMember
def test_client_display_worker(worker_message, mode_worker_type, worker_state_type,
                               bool1, bool2, mocked_client, capsys, strip_colors):
    worker_message.state = worker_state_type
    if bool1:
        worker_message.heartbeats.pop()
    if bool2:
        worker_message.timestamp = 123.1

    with mock.patch('clearly.client.ClearlyClient._worker_state') as m_worker_state:
        mocked_client._display_worker(worker_message, mode_worker_type)
    generated = strip_colors(capsys.readouterr().out)

    m_worker_state.assert_called_once_with(worker_state_type)
    assert worker_message.hostname in generated
    assert str(worker_message.pid) in generated

    stats, = mode_worker_type.spec
    if stats:
        assert 'sw_sys' in generated
        assert 'sw_ident' in generated
        assert 'sw_ver' in generated
        assert '[1.0, 2.0, 3.0]' in generated
        assert 'heartb:' in generated


# noinspection PyProtectedMember
def test_client_task_state(task_state_type, mocked_client):
    result = mocked_client._task_state(task_state_type)
    assert task_state_type in result


# noinspection PyProtectedMember
def test_client_worker_state(worker_state_type, mocked_client):
    result = mocked_client._worker_state(worker_state_type)
    assert worker_state_type in result


# noinspection PyProtectedMember
@pytest.mark.parametrize('value', [
    True, 1, object()
])
def test_parse_pattern_error(value, mocked_client):
    with pytest.raises(UserWarning):
        mocked_client._parse_pattern(value)


# noinspection PyProtectedMember
@pytest.mark.parametrize('value, expected', [
    (None, PatternFilter(pattern='.', negate=False)),
    (' ', PatternFilter(pattern='.', negate=False)),
    ('pattern', PatternFilter(pattern='pattern', negate=False)),
    ('  pattern   ', PatternFilter(pattern='pattern', negate=False)),
    ('!pattern', PatternFilter(pattern='pattern', negate=True)),
    ('! pattern', PatternFilter(pattern='pattern', negate=True)),
    ('!', None),
    ('!.', None),
    ('! .  ', None),
])
def test_parse_pattern(value, expected, mocked_client):
    assert mocked_client._parse_pattern(value) == expected


def test_display_modes_task_indicator(mode_task_type, mocked_client, capsys):
    mocked_client._modes = Modes(mode_task_type, ModeWorker.WORKER)
    mocked_client.display_modes()
    assert '* ' + mode_task_type.name in capsys.readouterr().out


def test_display_modes_worker_indicator(mode_worker_type, mocked_client, capsys):
    mocked_client._modes = Modes(ModeTask.TASK, mode_worker_type)
    mocked_client.display_modes()
    assert '* ' + mode_worker_type.name in capsys.readouterr().out


def test_display_modes_set_params(mocked_client):
    with mock.patch.object(mocked_client, '_get_display_modes') as mock_gdm:
        mocked_client.display_modes(1)
    mock_gdm.assert_called_once_with((1,))
    # noinspection PyProtectedMember
    assert mocked_client._modes == mock_gdm()


@pytest.mark.parametrize('modes', [
    (ModeTask.SENT, ModeTask.TASK),
    (ModeWorker.STATS, ModeWorker.WORKER),
    (ModeTask.SENT, ModeWorker.STATS, ModeWorker.STATS),
])
def test_get_display_modes_error(modes, mocked_client):
    with mock.patch('clearly.client.client.find_mode') as mock_find_mode, \
            pytest.raises(UserWarning):
        mock_find_mode.side_effect = lambda x: x
        # noinspection PyProtectedMember
        mocked_client._get_display_modes(modes)


@pytest.mark.parametrize('modes, expected', [
    (None, (ModeTask.TASK, ModeWorker.WORKER)),
    ((None,), (ModeTask.TASK, ModeWorker.WORKER)),
    ((None, None), (ModeTask.TASK, ModeWorker.WORKER)),
    (ModeTask.SENT, (ModeTask.SENT, ModeWorker.WORKER)),
    ((ModeTask.SENT,), (ModeTask.SENT, ModeWorker.WORKER)),
    ((ModeTask.SENT, None), (ModeTask.SENT, ModeWorker.WORKER)),
    ((None, ModeTask.SENT), (ModeTask.SENT, ModeWorker.WORKER)),
    (ModeWorker.STATS, (ModeTask.TASK, ModeWorker.STATS)),
    ((ModeWorker.STATS,), (ModeTask.TASK, ModeWorker.STATS)),
    ((ModeWorker.STATS, None), (ModeTask.TASK, ModeWorker.STATS)),
    ((None, ModeWorker.STATS), (ModeTask.TASK, ModeWorker.STATS)),
    ((ModeTask.SENT, ModeWorker.STATS), (ModeTask.SENT, ModeWorker.STATS)),
    ((ModeWorker.STATS, ModeTask.SENT), (ModeTask.SENT, ModeWorker.STATS)),
])
def test_get_display_modes_ok(modes, expected, mocked_client):
    mocked_client._modes = Modes(ModeTask.TASK, ModeWorker.WORKER)  # known defaults.
    with mock.patch('clearly.client.client.find_mode') as mock_find_mode:
        mock_find_mode.side_effect = lambda x: x
        # noinspection PyProtectedMember
        assert mocked_client._get_display_modes(modes) == expected
