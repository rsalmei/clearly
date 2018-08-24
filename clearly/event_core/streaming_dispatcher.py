# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals

import logging
import operator
import re
import signal
import threading
from collections import namedtuple
from contextlib import contextmanager

from .events import TaskData
from ..expected_state import ExpectedStateHandler, setup_task_states, setup_worker_states
from ..utils.data import accepts

try:
    # noinspection PyCompatibility
    from queue import Queue, Empty
except ImportError:  # pragma: no cover
    # noinspection PyUnresolvedReferences,PyCompatibility
    from Queue import Queue, Empty

logger = logging.getLogger('clearly.core.streaming_dispatcher')

CapturingClient = namedtuple('CapturingClient', 'queue task_regex task_negate worker_regex worker_negate')
TASK_OP = operator.attrgetter('queue', 'task_regex', 'task_negate')
WORKER_OP = operator.attrgetter('queue', 'worker_regex', 'worker_negate')


class StreamingDispatcher(object):
    """Dispatches events to connected clients.

    Server object, gets cleaned tasks and workers and send them to interested parties.
    
    Attributes:
        queue_input (Queue): to receive from event listener
        observers (list): currently connected clients, receiving real-time events
        task_states (ExpectedStateHandler): object that fills missing tasks' states
        worker_states (ExpectedStateHandler): object that fills missing workers' states
    """

    def __init__(self, queue_input):
        """Constructs a client dispatcher instance.
        
        Args:
            queue_input (Queue): to receive from event listener
        """
        logger.info('Creating %s', StreamingDispatcher.__name__)

        self.queue_input = queue_input
        self.observers = []  # should not need any lock, thanks to GIL
        self.task_states = setup_task_states()  # type: ExpectedStateHandler
        self.worker_states = setup_worker_states()  # type: ExpectedStateHandler

        # running engine (should be asyncio in the future)
        self.dispatcher_thread = None  # type:threading.Thread

        # detect shutdown.
        def sigterm_handler(_signo, _stack_frame):  # pragma: no cover
            self.__stop()

        signal.signal(signal.SIGTERM, sigterm_handler)
        self.__start()

    def __start(self):  # pragma: no cover
        """Starts the real-time engine that captures tasks."""

        assert not self.dispatcher_thread

        self.dispatcher_thread = threading.Thread(target=self.__run_dispatcher,
                                                  name='clearly-dispatcher')
        self.dispatcher_thread.daemon = True
        self.running = True  # graceful shutdown
        self.dispatcher_thread.start()

    def __stop(self):  # pragma: no cover
        """Stops the background engine."""

        if not self.dispatcher_thread:
            return

        logger.info('Stopping dispatcher')
        self.running = False  # graceful shutdown
        self.dispatcher_thread.join()
        self.dispatcher_thread = None

    @contextmanager
    def streaming_client(self, tasks_regex, tasks_negate, workers_regex, workers_negate):
        """Connects a client to the streaming capture, filtering the events that are sent
        to it.

        Args:
            tasks_regex (str): a pattern to filter tasks to capture.
                ex.: '^dispatch|^email' to filter names starting with that
                      or 'dispatch.*123456' to filter that exact name and number
                      or even '123456' to filter that exact number anywhere.
            tasks_negate (bool): if True, finds tasks that do not match criteria
            workers_regex (str): a pattern to filter workers to capture.
                ex.: 'service|priority' to filter names containing that
            workers_negate (bool): if True, finds workers that do not match criteria
        """

        cc = CapturingClient(Queue(),
                             re.compile(tasks_regex), tasks_negate,
                             re.compile(workers_regex), workers_negate)

        self.observers.append(cc)
        yield cc.queue
        self.observers.remove(cc)

    def __run_dispatcher(self):  # pragma: no cover
        logger.info('Starting dispatcher: %s', threading.current_thread())

        while self.running:
            try:
                event_data = self.queue_input.get(timeout=1)
            except Empty:
                continue

            self._dispatch(event_data)

        logger.info('Dispatcher stopped: %s', threading.current_thread())

    def _dispatch(self, event_data):
        if isinstance(event_data, TaskData):
            op, path = TASK_OP, self.task_states
            values = (event_data.name, event_data.routing_key)
        else:
            op, path = WORKER_OP, self.worker_states
            values = (event_data.hostname,)

        # let's see who's interested.
        for q, regex, negate in map(op, self.observers):
            if not accepts(regex, negate, *values):
                continue
            for kwds in StreamingDispatcher.generate_states(event_data, path):
                # noinspection PyUnresolvedReferences,PyProtectedMember
                q.put(event_data._replace(**kwds))

    @staticmethod
    def generate_states(event_data, path):
        if event_data.created:
            yield dict(state='-')  # sends one more, to present the params
        for field in path.states_through(event_data.pre_state, event_data.state):
            yield dict(state=field, created=False)
