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

BASE_THREAD_NAME = 'clearly-dispatcher'


class Role(Enum):
    TASKS = (accept_task,)
    WORKERS = (accept_worker,)

    def __new__(cls, func_accept):
        obj = object.__new__(cls)
        obj._value_ = len(cls.__members__) + 1
        obj.__func_accept = func_accept
        return obj

    @property
    def thread_name(self) -> str:
        return '{}-{}'.format(BASE_THREAD_NAME, self.name.lower())

    @property
    def func_accept(self) -> Callable[[Pattern, bool, Union[TaskMessage, WorkerMessage]], bool]:
        return self.__func_accept


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

    @contextmanager
    def streaming_capture(self, capture: PatternFilter, queue: Queue) -> None:
        """Put a connected client in streaming capture mode, filtering all
        incoming events in real time.

        Args:
            capture: the criteria for desired events
            queue: where to put the matching events

        """
        observer = queue, re.compile(capture.pattern), capture.negate

        # should not need any locks, thanks to GIL
        self.observers.append(observer)
        try:
            yield
        finally:
            self.observers.remove(observer)

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

    def __run(self) -> None:  # pragma: no cover
        logger.info('Starting: %r', threading.current_thread())

        while self.running:
            try:
                message = self.queue_input.get(timeout=1)
            except Empty:
                continue

            self._dispatch(message)

        logger.info('Stopped: %r', threading.current_thread())

    def _dispatch(self, message: Union[TaskMessage, WorkerMessage]) -> None:
        # let's see who's interested.
        for q, pattern, negate in self.observers:
            if self.role.func_accept(pattern, negate, message):
                q.put(message)
