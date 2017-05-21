# coding=utf-8
from itertools import chain

from collections import namedtuple

TASK_OWN_FIELDS = ('name', 'routing_key', 'uuid', 'retries', 'args', 'kwargs',
                   'result', 'traceback')
TASK_DYNAMIC_FIELDS = ('state', 'created')
TASK_FIELDS = TASK_OWN_FIELDS + TASK_DYNAMIC_FIELDS

TaskInfo = namedtuple('TaskInfo', TASK_FIELDS)

WORKER_FIELDS = ('hostname', 'pid', 'sw_sys', 'sw_ident', 'sw_ver', 'loadavg',
                 'processed', 'alive', 'freq')
WorkerInfo = namedtuple('WorkerInfo', WORKER_FIELDS)


def serialize_task(task, state, created):
    return TaskInfo._make(chain(
        (getattr(task, f) for f in TASK_OWN_FIELDS),
        (v for v in (state, created))
    ))


def serialize_worker(worker):
    return WorkerInfo._make(getattr(worker, f) for f in WORKER_FIELDS)
