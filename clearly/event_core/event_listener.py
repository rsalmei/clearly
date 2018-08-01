# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals

import logging
import signal
import threading

from celery import Celery, __version__ as CELERY_VERSION, states
from celery.backends.base import DisabledBackend
from celery.events import EventReceiver
from celery.events.state import State
from kombu import log as kombu_log

from .events import immutable_task, immutable_worker
from ..safe_compiler import safe_compile_text
from ..utils import worker_states

try:
    # noinspection PyCompatibility
    from queue import Queue
except ImportError:  # pragma: no cover
    # noinspection PyUnresolvedReferences,PyCompatibility
    from Queue import Queue

kombu_log.get_logger('').setLevel(logging.ERROR)


def compile_task_result4(result):
    # celery 4 sends results converted as strings, sometimes truncated (...)
    safe_compile_text(result, raises=True)
    # if compilable, returns the same, as the clients will be able to too.
    return result


def compile_task_result3(result):
    # celery 3 tasks' results are converted twice.
    compatible = safe_compile_text(result, raises=True)
    # compile with `raises`, to detect truncated results.
    safe_compile_text(compatible, raises=True)
    # if compilable, returns the same, as the clients will be able to too.
    return compatible


class EventListener(object):
    """Listens for celery events.

    Server object, to capture events and handle tasks and workers.

    Attributes:
        app (Celery): a configured celery app instance
        queue_output (Queue): to send to streaming dispatcher
        memory (State): LRU storage object to keep tasks and workers
        use_result_backend (bool): if True, it can fetch results from the actual result backend
    """

    def __init__(self, app, queue_output, use_result_backend=True,
                 max_tasks_in_memory=10000, max_workers_in_memory=100):
        """Constructs an event listener instance.

        Args:
            app (Celery): a configured celery app instance
            queue_output (Queue): to send to streaming dispatcher.
            use_result_backend (bool): if True, it can fetch results from the actual result backend
            max_tasks_in_memory (int): max tasks stored
            max_workers_in_memory (int): max workers stored
        """
        self.app = app
        self.queue_output = queue_output

        if isinstance(app.backend, DisabledBackend):  # pragma: no cover
            use_result_backend = False
        self.use_result_backend = use_result_backend

        # events handling: storage and filling missing states.
        self.memory = State(
            max_tasks_in_memory=max_tasks_in_memory,
            max_workers_in_memory=max_workers_in_memory,
        )  # type: State

        # running engine (should be asyncio in the future)
        self.listener_thread = None  # type:threading.Thread
        self.celery_receiver = None  # type:EventReceiver

        # concurrency control
        self.wait_event = threading.Event()

        # detect shutdown.
        def sigterm_handler(_signo, _stack_frame):  # pragma: no cover
            self.__stop()

        signal.signal(signal.SIGTERM, sigterm_handler)
        self.__start()

    def __start(self):  # pragma: no cover
        """Starts the real-time engine that captures events."""

        assert not self.listener_thread

        self.listener_thread = threading.Thread(target=self.__run_listener,
                                                name='clearly-listener')
        self.listener_thread.daemon = True
        self.listener_thread.start()
        self.wait_event.wait()
        self.wait_event.clear()

    def __stop(self):  # pragma: no cover
        """Stops the background engine."""

        if not self.listener_thread:
            return

        print('Stopping listener')
        self.celery_receiver.should_stop = True
        self.listener_thread.join()
        self.listener_thread = self.celery_receiver = None

    def __run_listener(self):  # pragma: no cover
        import sys
        print('Starting listener', threading.current_thread())
        sys.stdout.flush()

        with self.app.connection() as connection:
            self.celery_receiver = self.app.events.Receiver(
                connection, handlers={
                    '*': self._process_event,
                })  # type: EventReceiver
            self.wait_event.set()
            self.celery_receiver.capture(limit=None, timeout=None, wakeup=True)

        print('Listener stopped', threading.current_thread())
        sys.stdout.flush()

    def _process_event(self, event):
        event_type = event['type']
        if event_type.startswith('task'):
            data = self._process_task_event(event)
        elif event_type.startswith('worker'):
            data = self._process_worker_event(event)
        else:
            print('unknown event:', event)
            return

        self.queue_output.put(data)

    def _process_task_event(self, event):
        task = self.memory.tasks.get(event['uuid'])
        pre_state, created = (task.state, False) if task else (states.PENDING, True)
        (task, _), _ = self.memory.event(event)  # the `created` is broken in celery.
        if task.state == states.SUCCESS:
            try:
                # verify if the celery task result is truncated.
                task.result = EventListener.compile_task_result(task.result)
            except SyntaxError:
                # use result backend as fallback if allowed and available.
                if self.use_result_backend:
                    task.result = repr(self.app.AsyncResult(task.uuid).result)
        return immutable_task(task, task.state, pre_state, created)

    def _process_worker_event(self, event):
        worker = self.memory.workers.get(event['hostname'])
        pre_state, created = (worker.status_string, False) \
            if worker else (worker_states.OFFLINE, True)
        (worker, _), _ = self.memory.event(event)
        return immutable_worker(worker, worker.status_string, pre_state, created)

    if CELERY_VERSION >= '4':  # pragma: no cover
        compile_task_result = staticmethod(compile_task_result4)
    else:  # pragma: no cover
        compile_task_result = staticmethod(compile_task_result3)