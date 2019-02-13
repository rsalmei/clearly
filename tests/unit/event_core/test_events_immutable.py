import copy

import pytest

from clearly.event_core.events import TaskData, WorkerData, immutable_task, immutable_worker


class DummyObject:
    pass


def get_dummy(**kwargs):
    result = DummyObject()
    for k, v in kwargs.items():
        setattr(result, k, v)
    return result


@pytest.fixture(params=(0, 1, 10))
def heartbeats(request):
    yield list(range(request.param))


def test_immutable_task():
    task = get_dummy(name='name', routing_key='routing_key', uuid='uuid', retries='retries',
                     args='args', kwargs='kwargs', result='result', traceback='traceback',
                     timestamp=123.1, state='state')

    data = copy.copy(task.__dict__)
    data.update(state='new_state', pre_state='pre_state', created=True)
    expected = TaskData(**data)

    immutable = immutable_task(task, 'new_state', 'pre_state', True)
    assert immutable == expected
    assert immutable is not expected

    task.state = 'oops'
    assert immutable == expected


def test_immutable_worker(heartbeats):
    worker = get_dummy(hostname='hostname', pid=12000, sw_sys='sw_sys', sw_ident='sw_ident',
                       sw_ver='sw_ver', loadavg='loadavg', processed='processed',
                       alive=True, freq=5, heartbeats=heartbeats)

    data = copy.copy(worker.__dict__)
    data.update(state='new_state', pre_state='pre_state', created=True,
                last_heartbeat=heartbeats[-1] if heartbeats else None)
    del data['heartbeats']
    expected = WorkerData(**data)

    immutable = immutable_worker(worker, 'new_state', 'pre_state', True)
    assert immutable == expected
    assert immutable is not expected

    worker.state = 'oops'
    assert immutable == expected
