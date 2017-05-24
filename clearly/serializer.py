# coding=utf-8
from collections import namedtuple
from itertools import chain

TASK_OWN_FIELDS = ('name', 'routing_key', 'uuid', 'retries', 'args', 'kwargs',
                   'result', 'traceback', 'timestamp')
TASK_DYNAMIC_FIELDS = ('state', 'created')
TASK_FIELDS = TASK_OWN_FIELDS + TASK_DYNAMIC_FIELDS

TaskInfo = namedtuple('TaskInfo', TASK_FIELDS)

WORKER_OWN_FIELDS = ('hostname', 'pid', 'sw_sys', 'sw_ident', 'sw_ver',
                     'loadavg', 'processed', 'alive', 'freq')
WORKER_DYNAMIC_FIELDS = ('heartbeat',)
WORKER_FIELDS = WORKER_OWN_FIELDS + WORKER_DYNAMIC_FIELDS

WorkerInfo = namedtuple('WorkerInfo', WORKER_FIELDS)


def serialize_task(task, state, created):
    return TaskInfo._make(chain(
        (getattr(task, f) for f in TASK_OWN_FIELDS),
        (state, created)
    ))


def serialize_worker(worker):
    return WorkerInfo._make(chain(
        (getattr(worker, f) for f in WORKER_OWN_FIELDS),
        (worker.heartbeats[-1] if worker.heartbeats else None,)
    ))
