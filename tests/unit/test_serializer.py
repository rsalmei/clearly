from __future__ import absolute_import, print_function, unicode_literals

import pytest

from clearly.serializer import TASK_OWN_FIELDS, WORKER_OWN_FIELDS, serialize_task, serialize_worker


class DummyObject:
    pass


def get_dummy(params):
    result = DummyObject()
    for k in params:
        setattr(result, k, k)
    return result


@pytest.fixture
def task():
    yield get_dummy(TASK_OWN_FIELDS)


@pytest.fixture(params=(0, 1, 10))
def worker(request):
    result = get_dummy(WORKER_OWN_FIELDS)
    result.heartbeats = list(range(request.param))
    yield result


def test_serialize_task(task):
    serialized = serialize_task(task, 'a_state', 'a_date')
    assert serialized == TASK_OWN_FIELDS + ('a_state', 'a_date')


def test_serialize_worker(worker):
    serialized = serialize_worker(worker)
    last = worker.heartbeats[-1] if worker.heartbeats else None
    assert serialized == WORKER_OWN_FIELDS + (last,)
