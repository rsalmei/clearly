from itertools import chain
from queue import Queue
from unittest import mock
from unittest.mock import DEFAULT, PropertyMock, call

import pytest
from celery.events.state import Task, Worker
from celery.states import PENDING, SUCCESS

from clearly.protos.clearly_pb2 import TaskMessage, WorkerMessage
from clearly.server.event_listener import EventListener
from clearly.utils import worker_states


@pytest.fixture
def listener():
    with mock.patch('threading.Thread'), \
         mock.patch('threading.Event'), \
         mock.patch('clearly.server.event_listener.Celery'):
        # noinspection PyTypeChecker
        yield EventListener('', Queue(), Queue(), mock.Mock())


def test_listener_process_event_task(listener):
    with mock.patch.multiple(listener, _set_task_event=DEFAULT,
                             _set_worker_event=DEFAULT, _set_custom_event=DEFAULT) as mtw, \
            mock.patch('clearly.server.event_listener.obj_to_message') as otm:
        mtw['_set_task_event'].return_value = (x for x in chain(('obj',), 'abc'))

        # noinspection PyProtectedMember
        listener._process_event(dict(type='task-anything'))

    mtw['_set_task_event'].assert_called_once_with(dict(type='task-anything'))
    for k in '_set_worker_event', '_set_custom_event':
        mtw[k].assert_not_called()
    assert listener.queue_tasks.qsize() == 3
    assert listener.queue_workers.qsize() == 0
    assert otm.call_args_list == [
        call('obj', TaskMessage, state='a'),
        call('obj', TaskMessage, state='b'),
        call('obj', TaskMessage, state='c'),
    ]


def test_listener_process_event_worker(listener):
    with mock.patch.multiple(listener, _set_task_event=DEFAULT,
                             _set_worker_event=DEFAULT, _set_custom_event=DEFAULT) as mtw, \
            mock.patch('clearly.server.event_listener.obj_to_message') as otm:
        mtw['_set_worker_event'].return_value = (x for x in ('obj', 'ok'))

        # noinspection PyProtectedMember
        listener._process_event(dict(type='worker-anything'))

    mtw['_set_worker_event'].assert_called_once_with(dict(type='worker-anything'))
    for k in '_set_task_event', '_set_custom_event':
        mtw[k].assert_not_called()
    assert listener.queue_workers.qsize() == 1
    assert listener.queue_tasks.qsize() == 0
    assert otm.call_args_list == [
        call('obj', WorkerMessage, state='ok'),
    ]


def test_listener_process_event_custom(listener):
    with mock.patch.multiple(listener, _set_task_event=DEFAULT,
                             _set_worker_event=DEFAULT, _set_custom_event=DEFAULT) as mtw:
        # noinspection PyProtectedMember
        listener._process_event(dict(type='cool-event'))

    mtw['_set_custom_event'].assert_called_once_with(dict(type='cool-event'))
    for k in '_set_task_event', '_set_worker_event':
        mtw[k].assert_not_called()


def test_listener_set_task_event(task_state_type, bool1, listener):
    with mock.patch.object(listener, '_derive_task_result') as mock_dtr:
        mock_dtr.return_value = 1, 2
        listener.memory.tasks.get.return_value = Task('uuid', state='pre_state') if bool1 else None
        task = Task('uuid', state=task_state_type)
        listener.memory.event.return_value = (task, ''), ''

        # noinspection PyProtectedMember
        gen = listener._set_task_event(dict(uuid='uuid'))
        assert task == next(gen)

    listener.memory.event.assert_called_once_with(dict(uuid='uuid'))
    if task_state_type == SUCCESS:
        mock_dtr.assert_called_once_with(task)

    with mock.patch.object(listener, 'gen_task_states') as ts_through:
        ts_through.states_through.return_value = (x for x in 'abc')

        states = list(gen)
        if not bool1:
            if task_state_type == PENDING:
                assert states == ['']
            else:
                assert states == [task_state_type]
        else:
            ts_through.states_through.assert_called_once_with('pre_state', task_state_type)
            assert states == ['a', 'b', 'c']


def test_listener_set_worker_event(worker_event_type, listener):
    worker = Worker('hostname')
    listener.memory.event.return_value = (worker, ''), ''

    # noinspection PyProtectedMember
    gen = listener._set_worker_event(dict(type=worker_event_type))
    assert worker == next(gen)
    listener.memory.event.assert_called_once_with(dict(type=worker_event_type))
    assert worker.state == next(gen)
    assert worker.state == worker_states.TYPES[worker_event_type]


@pytest.mark.parametrize('compile_res, use_rb, result_backend, expected', [
    ('ok', None, None, ('event', 'ok')),
    (SyntaxError, False, None, ('no-backend', 'original')),
    (SyntaxError, True, 'ok', ('backend', "'ok'")),
    (SyntaxError, True, Exception, ('fetch-failed', 'original')),
    (Exception, False, None, ('compile-failed', 'original')),
    (Exception, True, 'ok', ('backend', "'ok'")),
    (Exception, True, Exception, ('fetch-failed', 'original')),
])
def test_listener_derive_task_result(compile_res, use_rb, result_backend, expected, listener):
    with mock.patch('clearly.server.event_listener.EventListener.compile_task_result') as ctr, \
            mock.patch.object(listener, 'use_result_backend', use_rb):
        ctr.side_effect = (compile_res,)
        type(listener.app.AsyncResult()).result = PropertyMock(side_effect=(result_backend,))

        task = Task(result='original')
        # noinspection PyProtectedMember
        result = listener._derive_task_result(task)

    assert result == expected


@pytest.mark.parametrize('worker_version, num_calls, expected', [
    ('3.nice', 2, 'a'),
    ('4.cool', 1, 'x'),
])
def test_listener_celery_version_result_compiler(worker_version, num_calls, expected):
    task = mock.Mock()
    task.result = 'x'
    task.worker.sw_ver = worker_version

    with mock.patch('clearly.server.event_listener.safe_compile_text') as msc:
        msc.side_effect = ('a', 'b')
        result = EventListener.compile_task_result(task)

    assert msc.call_count == num_calls
    assert result == expected
