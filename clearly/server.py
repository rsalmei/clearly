# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals

import operator
import re
# noinspection PyCompatibility
from concurrent import futures

import grpc
from celery import Celery
from celery.events.state import Task, Worker

from event_core.events import WorkerData
from .event_core.event_listener import EventListener
from .event_core.events import TaskData
from .event_core.streaming_dispatcher import StreamingDispatcher
from .protos import clearly_pb2, clearly_pb2_grpc
from .utils.data import accepts

try:
    # noinspection PyCompatibility
    from queue import Queue, Empty
except:
    # noinspection PyCompatibility
    from Queue import Queue, Empty



class ClearlyServer(object):
    """Simple and real-time monitor for celery.
    Server object, to capture events and handle tasks and workers.
    
    """

        """Constructs a server instance.
        
        Args:
        """

        """



        """


    @contextmanager
    def client_connect(self, pattern=None, negate=False,
                       workers=None, negate_workers=True):
        """Connects a client to this server, filtering the tasks that are sent
        to it.

        Args:
            pattern (Optional[str]): a pattern to filter tasks to capture.
                ex.: '^dispatch|^email' to filter names starting with that
                      or 'dispatch.*123456' to filter that exact name and number
                      or even '123456' to filter that exact number anywhere.
            negate (bool): if True, finds tasks that do not match criteria
            workers (Optional[str]): a pattern to filter workers to capture.
                ex.: 'service|priority' to filter names containing that
            negate_workers (bool): if True, finds workers that do not match criteria

        """

        self._client_regex = re.compile(pattern or '.')
        self._client_negate = negate
        self._client_workers_regex = re.compile(workers or '.')
        self._client_workers_negate = negate_workers

        with self._background_lock:
            self._client_queue = Queue()
            yield self._client_queue
            self._client_queue = None


    def tasks(self, pattern=None, state=None, negate=False):
        """Filters captured tasks.
        
        Args:
            pattern (Optional[str]): any part of the task name or routing key
            state (Optional[str]): a state to filter tasks
            negate (bool): if True, finds tasks that do not match criteria

        """
        pcondition = scondition = lambda task: True
        if pattern:
            regex = re.compile(pattern)
            pcondition = lambda task: \
                regex.search(task.name or '') or \
                regex.search(task.routing_key or '')
        if state:
            scondition = lambda task: task.state == state

        found_tasks = islice(
            (task for _, task in self._memory.itertasks()
             if bool(pcondition(task) and scondition(task)) ^ negate
             ), 0, None)
        for task in found_tasks:  # type:Task
            yield serialize_task(task, task.state, False)

    def workers(self, pattern=None, negate=False):
        """Filters known workers and prints their current status.
        
        Args:
            pattern (Optional[str]): any part of the task name or routing key
            negate (bool): if True, finds tasks that do not match criteria

        """
        regex = re.compile(pattern or '.')
        found_workers = islice(
            (worker for worker in map(lambda w: self._memory.workers[w],
                                      sorted(self._memory.workers))
             if bool(regex.search(worker.hostname)) ^ negate
             ), 0, None)
        for worker in found_workers:  # type:Worker
            yield serialize_worker(worker)

    def task(self, task_uuid):
        """Finds one specific task.

        Args:
            task_uuid (str): any part of the task name or routing key

        """
        task = self._memory.tasks.get(task_uuid)
        if task:
            return serialize_task(task, task.state, False)

    def seen_tasks(self):
        return self._memory.task_types()

    def reset(self):
        """Resets all captured tasks.
        
        """
        self._memory.clear_tasks()

    def stats(self):
        m = self._memory
        return m.task_count, m.event_count, len(m.tasks), len(m.workers)


