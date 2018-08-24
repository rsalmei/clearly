# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals

from collections import namedtuple

from itertools import chain

# direct fields come directly from method call.
DIRECT_FIELDS = ('state', 'pre_state', 'created')

# own fields are retrieved directly from the original object.
TASK_OWN_FIELDS = ('name', 'routing_key', 'uuid', 'retries', 'args', 'kwargs',
                   'result', 'traceback', 'timestamp')
WORKER_OWN_FIELDS = ('hostname', 'pid', 'sw_sys', 'sw_ident', 'sw_ver',
                     'loadavg', 'processed', 'freq', 'alive')

TaskData = namedtuple('TaskData', TASK_OWN_FIELDS + DIRECT_FIELDS)
WorkerData = namedtuple('WorkerData', WORKER_OWN_FIELDS + DIRECT_FIELDS + ('last_heartbeat',))


def immutable_task(task, state, pre_state, created):
    """Converts to an immutable slots class to handle internally."""
    # noinspection PyUnresolvedReferences,PyProtectedMember
    return TaskData._make(chain(
        (getattr(task, f) for f in TASK_OWN_FIELDS),
        (state, pre_state, created),
    ))


def immutable_worker(worker, state, pre_state, created):
    """Converts to an immutable slots class to handle internally."""
    # noinspection PyUnresolvedReferences,PyProtectedMember
    return WorkerData._make(chain(
        (getattr(worker, f) for f in WORKER_OWN_FIELDS),
        (state, pre_state, created),
        (worker.heartbeats[-1] if worker.heartbeats else None,),
    ))
