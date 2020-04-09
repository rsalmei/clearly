import logging
import signal
import threading
from queue import Queue
from typing import Any, Iterator, Optional, Tuple, Union

from celery import Celery
from celery.events import EventReceiver
from celery.events.state import State, Task, Worker
from celery.states import PENDING, SUCCESS

from .expected_state import ExpectedStateHandler, setup_task_states
from ..protos.clearly_pb2 import TaskMessage, WorkerMessage
from ..utils import worker_states
from ..utils.data import obj_to_message
from ..utils.env_params import get_env_int
from ..utils.safe_compiler import safe_compile_text

logger = logging.getLogger(__name__)

BROKER_CONNECT_TIMEOUT = get_env_int('BROKER_CONNECT_TIMEOUT', 5)
THREAD_NAME = 'clearly-listener'


class EventListener:
    """Listen for celery events.

    Server object, to capture events and handle tasks and workers.

    Attributes:
        app: a configured celery app instance
        queue_tasks: to send to the streaming dispatcher responsible for tasks
        queue_workers: to send to the streaming dispatcher responsible for workers
        memory: LRU storage object to keep tasks and workers
        use_result_backend: if True, there's a result backend to fetch results from
        gen_task_states: object that fills missing tasks' states

    """

    def __init__(self, broker: str, queue_tasks: Queue, queue_workers: Queue, memory: State,
                 backend: str = None):
        """Construct an event listener instance.

        Args:
            broker: the broker being used by the celery system.
            queue_tasks: to send to the streaming dispatcher responsible for tasks
            queue_workers: to send to the streaming dispatcher responsible for workers
            backend: the result backend being used by the celery system.

        """
        logger.info('Creating %s', EventListener.__name__)

        self.queue_tasks, self.queue_workers, self.memory = queue_tasks, queue_workers, memory
        self.use_result_backend = bool(backend)

        self.app = Celery(broker=broker, backend=backend)
        logger.info('broker : %s', self.app.pool.connection.as_uri())
        logger.info('backend: %s', self.app.backend.as_uri())

        # fill missing gaps in states.
        self.gen_task_states: ExpectedStateHandler = setup_task_states()

        # running engine (should be asyncio in the future)
        self._listener_thread: Optional[threading.Thread] = None
        self._celery_receiver: Optional[EventReceiver] = None

        # concurrency control
        self._wait_event = threading.Event()

        # detect shutdown.
        def sigterm_handler(_signo, _stack_frame):  # pragma: no cover
            self.__stop()

        signal.signal(signal.SIGTERM, sigterm_handler)
        self.__start()

    def __start(self) -> None:  # pragma: no cover
        """Start the real time engine that captures events."""

        assert not self._listener_thread

        self._listener_thread = threading.Thread(target=self.__run, name=THREAD_NAME)
        self._listener_thread.daemon = True
        self._listener_thread.start()

        if not self._wait_event.wait(timeout=BROKER_CONNECT_TIMEOUT):
            raise TimeoutError('Could not connect to broker.')
        self._wait_event.clear()

    def __stop(self) -> None:  # pragma: no cover
        """Stop the background engine."""

        if not self._listener_thread:
            return

        logger.info('Stopping %s', THREAD_NAME)
        self._celery_receiver.should_stop = True
        self._listener_thread.join(1)
        self._listener_thread = self._celery_receiver = None

    def __run(self) -> None:  # pragma: no cover
        logger.info('Starting: %r', threading.current_thread())

        with self.app.connection() as connection:
            self._celery_receiver: EventReceiver = self.app.events.Receiver(
                connection, handlers={
                    '*': self._process_event,
                })
            self._wait_event.set()
            self._celery_receiver.capture(limit=None, timeout=None, wakeup=True)

        logger.info('Stopped: %r', threading.current_thread())

    def _process_event(self, event: dict) -> None:
        event_type = event['type']
        if event_type.startswith('task'):
            gen, queue, to_type = self._set_task_event(event), self.queue_tasks, TaskMessage
        elif event_type.startswith('worker'):
            gen, queue, to_type = self._set_worker_event(event), self.queue_workers, WorkerMessage
        else:
            self._set_custom_event(event)
            return

        obj = next(gen)
        for state in gen:
            queue.put(obj_to_message(obj, to_type, state=state))

    def _set_task_event(self, event: dict) -> Iterator[Union[Task, str]]:
        task = self.memory.tasks.get(event['uuid'])
        pre_state = task and task.state
        (task, _), _ = self.memory.event(event)

        # fix or insert fields.
        task.result_meta = None
        if task.state == SUCCESS:
            task.result_meta, task.result = self._derive_task_result(task)
        yield task

        # fix shortcomings of `created` field: a task should be displayed as PENDING if not
        # new; if a task is first seen in any other state, it should not be new.
        if not pre_state:
            yield '' if task.state == PENDING else task.state  # empty state will mean new.
            return

        yield from self.gen_task_states.states_through(pre_state, task.state)

    def _set_worker_event(self, event: dict) -> Iterator[Union[Worker, str]]:
        (worker, _), _ = self.memory.event(event)

        # fix or insert fields.
        worker.state = worker_states.TYPES[event['type']]
        yield worker

        yield worker.state

    # noinspection PyMethodMayBeStatic
    def _set_custom_event(self, event: dict) -> None:  # pragma: no cover
        # could pass custom user events here, if the need ever arises.
        logger.warning('unknown event: %s', event)

    # noinspection PyBroadException
    def _derive_task_result(self, task: Task) -> Tuple[str, str]:
        try:  # verify if the task result is truncated.
            return 'event', EventListener.compile_task_result(task)
        except SyntaxError:  # <== this means the result is truncated.
            error = 'no-backend'
        except Exception:
            logger.exception('Failed to compile task result: %s, worker: %s',
                             task.result, task.worker)
            error = 'compile-failed'

        if self.use_result_backend:
            try:
                return 'backend', repr(self.app.AsyncResult(task.uuid).result)
            except Exception:  # probably incompatible celery versions in clearly and user code.
                logger.exception('Failed to fetch task result from result_backend: %s',
                                 task.uuid)
                error = 'fetch-failed'

        return error, task.result

    @staticmethod
    def compile_task_result(task: Task) -> Any:
        result = task.result
        # celery 4 sends results converted as strings, sometimes truncated (...)
        if task.worker.sw_ver < '4':
            # celery 3 tasks' results are converted twice.
            result = safe_compile_text(result, raises=True)
        # compile with `raises`, to detect truncated results.
        safe_compile_text(result, raises=True)
        # if compilable, returns the same, as the clients will be able to too.
        return result
