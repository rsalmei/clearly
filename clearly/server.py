# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals

import logging
import re
import signal
import threading
from Queue import Queue
from contextlib import contextmanager
from itertools import islice

from celery import Celery, states
from celery.backends.base import DisabledBackend
from celery.events import EventReceiver
from celery.events.state import State, Task, Worker
from kombu import log as kombu_log

from clearly.safe_compiler import safe_compile_text
from .expected_state import ExpectedStateHandler, setup_task_states, \
    setup_worker_states
from .serializer import serialize_task, serialize_worker

kombu_log.get_logger('').setLevel(logging.ERROR)


class ClearlyServer(object):
    """Simple and real-time monitor for celery.
    Server object, to capture events and handle tasks and workers.
    
        Attributes:
            _app: Celery
            _memory: celery.events.State
            _task_states: ExpectedStateHandler
            _worker_states: ExpectedStateHandler
    """

    def __init__(self, app=None, ignore_result_backend=False,
                 max_tasks_in_memory=1000, max_workers_in_memory=100):
        """Constructs a server instance.
        
        Args:
            app (Celery): a configured celery app instance
            ignore_result_backend (bool): if True, do not fetch results from the actual result backend
            max_tasks_in_memory (int): max tasks stored
            max_workers_in_memory (int): max workers stored

        """
        if isinstance(app.backend, DisabledBackend):
            ignore_result_backend = True

        self._app = app
        self._ignore_result_backend = ignore_result_backend

        self._memory = self._app.events.State(
            max_tasks_in_memory=max_tasks_in_memory,
            max_workers_in_memory=max_workers_in_memory,
        )  # type: State
        self._task_states = setup_task_states()  # type: ExpectedStateHandler
        self._worker_states = setup_worker_states()  # type: ExpectedStateHandler

        # concurrency control
        self._background_lock = threading.RLock()
        self._background_connected = threading.Event()

        # running engine
        self._background_thread = None  # type:threading.Thread
        self._background_receiver = None  # type:EventReceiver

        # connected client
        self._client_queue = None  # type:Queue
        self._client_regex = None
        self._client_negate = None
        self._client_workers_regex = None
        self._client_workers_negate = None

        # detect shutdown.
        def sigterm_handler(_signo, _stack_frame):
            self.stop()

        signal.signal(signal.SIGTERM, sigterm_handler)

    def start(self):
        """Starts the real-time engine that captures tasks.

        """

        with self._background_lock:
            if self._background_thread:
                return
            self._background_thread = threading.Thread(
                target=self.__run_server, name='clearly-agent')
            self._background_thread.daemon = True

            self._background_connected.clear()
            self._background_thread.start()
            self._background_connected.wait()

    def stop(self):
        """Stops the background engine, without losing anything already 
        captured.
    
        """

        with self._background_lock:
            if not self._background_thread:
                return
            print('Stopping server')
            self._background_receiver.should_stop = True
            while self._background_thread.is_alive():
                self._background_thread.join()
            self._background_thread = None
            self._background_receiver = None

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

    def __run_server(self):
        import sys
        print('Starting server', threading.current_thread())
        sys.stdout.flush()

        def maybe_publish(func, regex, negate, *values):
            if not self._client_queue:
                return
            if any(v and regex.search(v) for v in values) == negate:
                return

            obj = func()
            try:
                self._client_queue.put(obj)
            except AttributeError:
                # the capture is not synced with terminal anymore.
                # no problem.
                pass

        def process_event(event):
            event_type = event['type']
            if event_type.startswith('task'):
                for task, state, created in process_task_event(event):
                    maybe_publish(lambda: serialize_task(task, state, created),
                                  self._client_regex, self._client_negate,
                                  task.name, task.routing_key)

            elif event_type.startswith('worker'):
                for worker in process_worker_event(event):
                    maybe_publish(lambda: serialize_worker(worker),
                                  self._client_workers_regex, self._client_workers_negate,
                                  worker.hostname)

            else:
                print('unknown event:', event)

        def process_task_event(event):
            task, created = self._memory.get_or_create_task(event['uuid'])
            with self._task_states.track_changes(task):
                (_, _), subject = self._memory.event(event)
            if task.state == states.SUCCESS:
                try:
                    # celery tasks' results are escaped, so we must compile them.
                    task.result = safe_compile_text(task.result, raises=True)
                except SyntaxError:
                    # celery must have truncated task result.
                    # use result backend as fallback if allowed and available.
                    if not self._ignore_result_backend:
                        task.result = self._app.AsyncResult(task.uuid).result
            if created:
                yield task, '-', True
            for state in self._task_states.states_through():
                yield task, state, False

        def process_worker_event(event):
            worker, _ = self._memory.get_or_create_worker(event['hostname'])
            with self._worker_states.track_changes(worker):
                (_, _), subject = self._memory.event(event)
            for _ in self._worker_states.states_through():
                yield worker

        with self._app.connection() as connection:
            self._background_receiver = self._app.events.Receiver(
                connection, handlers={
                    '*': process_event,
                })  # type: EventReceiver
            self._background_connected.set()
            self._background_receiver.capture(limit=None, timeout=None, wakeup=True)

        print('Server stopped', threading.current_thread())
        sys.stdout.flush()

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
