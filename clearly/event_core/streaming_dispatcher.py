import logging
import re
import signal
import threading
from contextlib import contextmanager
from enum import Enum
from queue import Empty, Queue
from typing import List, Optional, Pattern, Tuple, Union, Callable

from ..protos.clearly_pb2 import PatternFilter, TaskMessage, WorkerMessage
from ..utils.data import accept_task, accept_worker

logger = logging.getLogger(__name__)

THREAD_NAME = 'clearly-dispatcher'


class Role(Enum):
    TASKS = (accept_task,)
    WORKERS = (accept_worker,)

    @property
    def thread_name(self) -> str:
        return '{}-{}'.format(THREAD_NAME, self.name.lower())

    @property
    def func_accept(self) -> Callable[[Pattern, bool, Union[TaskMessage, WorkerMessage]], bool]:
        return self.value[0]


class StreamingDispatcher:
    """Dispatch events to connected clients.

    Server object, gets cleaned tasks and workers and send them to interested parties.
    One instance takes care of only one of those, two instances are needed.
    
    Attributes:
        queue_input: to receive from event listener
        observers: currently connected clients, interested in real time worker events
        role: current role this dispatcher is running

    """

    def __init__(self, queue_input: Queue, role: Role):
        """Construct a client dispatcher instance.
        
        Args:
            queue_input: to receive from event listener

        """
        logger.info('Creating %s', StreamingDispatcher.__name__)

        self.queue_input, self.role = queue_input, role
        self.observers: List[Tuple[Queue, Pattern, bool]] = []

        # running engine (should be asyncio in the future)
        self.dispatcher_thread: Optional[threading.Thread] = None

        # detect shutdown.
        def sigterm_handler(_signo, _stack_frame):  # pragma: no cover
            self.__stop()

        signal.signal(signal.SIGTERM, sigterm_handler)
        self.__start()

    def __start(self) -> None:  # pragma: no cover
        """Start the real time engine that captures tasks."""

        assert not self.dispatcher_thread

        self.dispatcher_thread = threading.Thread(target=self.__run, name=self.role.thread_name)
        self.dispatcher_thread.daemon = True
        self.running = True  # graceful shutdown
        self.dispatcher_thread.start()

    def __stop(self) -> None:  # pragma: no cover
        """Stop the background engine."""

        if not self.dispatcher_thread:
            return

        logger.info('Stopping %s', self.role.thread_name)
        self.running = False  # graceful shutdown
        self.dispatcher_thread.join(1)
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

    def __run(self) -> None:  # pragma: no cover
        logger.info('Starting: %r', threading.current_thread())

        while self.running:
            try:
                event_data = self.queue_input.get(timeout=1)
            except Empty:
                continue

            self._dispatch(event_data)

        logger.info('Stopped: %r', threading.current_thread())

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
