import logging
import operator
import re
import sys
from concurrent import futures
from contextlib import ExitStack
from queue import Empty, Queue
from typing import Optional

import grpc
from about_time import about_time
from celery.events.state import State

from .event_listener import EventListener
from .streaming_dispatcher import Role, StreamingDispatcher
from ..protos.clearly_pb2 import Null, RealtimeMessage, SeenTasksMessage, StatsMessage, \
    TaskMessage, WorkerMessage
from ..protos.clearly_pb2_grpc import ClearlyServerServicer, add_ClearlyServerServicer_to_server
from ..utils.data import accept_task, accept_worker, obj_to_message

logger = logging.getLogger(__name__)

PATTERN_FILTER_OP = operator.attrgetter('pattern', 'negate')
WORKER_HOSTNAME_OP = operator.attrgetter('hostname')


class ClearlyServer:
    """Main server object, which orchestrates capturing of celery events, see to
    the connected clients' needs, and manages the RPC communication.

    Attributes:
        _memory: LRU storage object to keep celery tasks and workers
        _listener: the object that listens and keeps celery events
        _dispatcher_tasks: the mechanism to dispatch tasks to clients
        _dispatcher_workers: the mechanism to dispatch workers to clients
        _rpc: the gRPC service

    """

    def __init__(self, broker: str, backend: Optional[str] = None, max_tasks: Optional[int] = None,
                 max_workers: Optional[int] = None):  # pragma: no cover
        """Construct a Clearly Server instance.

        Args:
            broker: the broker being used by the celery system
            backend: the result backend being used by the celery system
            max_tasks: max tasks stored
            max_workers: max workers stored

        """
        max_tasks, max_workers = max_tasks or 10000, max_workers or 100
        logger.info('Creating memory: max_tasks=%d; max_workers=%d', max_tasks, max_workers)
        self._memory = State(max_tasks_in_memory=max_tasks, max_workers_in_memory=max_workers)

        queue_tasks, queue_workers = Queue(), Queue()  # hands new events to be distributed.
        try:
            self._listener = EventListener(broker, queue_tasks, queue_workers,
                                           self._memory, backend)
        except TimeoutError as e:
            logger.critical(e)
            sys.exit(1)

        self._dispatcher_tasks = StreamingDispatcher(queue_tasks, Role.TASKS)
        self._dispatcher_workers = StreamingDispatcher(queue_workers, Role.WORKERS)
        self._rpc = RPCService(self._memory, self._dispatcher_tasks, self._dispatcher_workers)

    def start_server(self, port: int = None, blocking: Optional[bool] = None) \
            -> Optional[grpc.Server]:  # pragma: no cover
        """Start the communication service in a new gRPC server instance.

        Args:
            port: the port clearly server will serve on
            blocking: if True manages gRPC server and blocks the main thread,
                just returns the server otherwise

        Returns:
            the gRPC server if not blocking, None otherwise

        """
        port = port or 12223
        logger.info('Initiating gRPC server: port=%d', port)

        gserver = grpc.server(futures.ThreadPoolExecutor())
        add_ClearlyServerServicer_to_server(self._rpc, gserver)
        gserver.add_insecure_port('[::]:{}'.format(port))

        logger.info('gRPC server ok')
        if blocking is False:
            return gserver

        gserver.start()

        one_day_in_seconds = 24 * 60 * 60
        import time
        try:
            while True:
                time.sleep(one_day_in_seconds)
        except KeyboardInterrupt:
            logger.info('Stopping gRPC server')
            gserver.stop(None)  # immediately.


class RPCService(ClearlyServerServicer):
    """Service that implements the RPC communication."""

    def __init__(self, memory: State, dispatcher_tasks: StreamingDispatcher,
                 dispatcher_workers: StreamingDispatcher):
        """Construct an RPC server instance.
        
        Args:
            memory: LRU storage object to keep tasks and workers
            dispatcher_tasks: the mechanism to dispatch tasks to clients
            dispatcher_workers: the mechanism to dispatch workers to clients

        """
        logger.info('Creating %s', RPCService.__name__)

        self.memory = memory
        self.dispatcher_tasks, self.dispatcher_workers = dispatcher_tasks, dispatcher_workers

    def capture_realtime(self, request, context):
        """Initiate a streaming capture.

        Args:
            request (clearly_pb2.CaptureRequest):
            context:

        Yields:
            clearly_pb2.RealtimeEventMessage

        """
        RPCService._log_request(request, context)

        queue = Queue()
        with ExitStack() as stack:
            if request.HasField('tasks_capture'):
                stack.enter_context(
                    self.dispatcher_tasks.streaming_capture(request.tasks_capture, queue))
            if request.HasField('workers_capture'):
                stack.enter_context(
                    self.dispatcher_workers.streaming_capture(request.workers_capture, queue))
            while True:
                try:
                    message = queue.get(timeout=1)
                except Empty:  # pragma: no cover
                    continue

                key = {
                    TaskMessage: 'task',
                    WorkerMessage: 'worker',
                }[type(message)]
                yield RealtimeMessage(**{key: message})

    def filter_tasks(self, request, context):
        """Filter tasks by matching patterns to name, routing key and state.

        Yields:
            clearly_pb2.TaskMessage

        """
        RPCService._log_request(request, context)

        pattern, negate = PATTERN_FILTER_OP(request.tasks_filter)
        limit, reverse = request.limit, request.reverse
        pattern = re.compile(pattern)

        # generators are cool!
        found_tasks = (task for _, task in
                       self.memory.tasks_by_time(limit=limit or None, reverse=reverse)
                       if accept_task(pattern, negate, task))

        at = about_time(found_tasks)
        for task in at:
            yield obj_to_message(task, TaskMessage)
        logger.debug('%s iterated %d tasks in %s (%s)', self.filter_tasks.__name__,
                     at.count, at.duration_human, at.throughput_human)

    def filter_workers(self, request, context):
        """Filter workers by matching a pattern to hostname.

        Yields:
            clearly_pb2.WorkerMessage

        """
        RPCService._log_request(request, context)

        pattern, negate = PATTERN_FILTER_OP(request.workers_filter)
        pattern = re.compile(pattern)

        # generators are cool!
        found_workers = (worker for worker in
                         sorted(self.memory.workers.values(), key=WORKER_HOSTNAME_OP)
                         if accept_worker(pattern, negate, worker))

        at = about_time(found_workers)
        for worker in at:
            yield obj_to_message(worker, WorkerMessage)
        logger.debug('%s iterated %d workers in %s (%s)', self.filter_workers.__name__,
                     at.count, at.duration_human, at.throughput_human)

    def seen_tasks(self, request, context):
        """Returns all seen task types.

        Returns:
            clearly_pb2.SeenTasksMessage

        """
        RPCService._log_request(request, context)

        result = SeenTasksMessage()
        result.task_types.extend(self.memory.task_types())
        return result

    def reset_tasks(self, request, context):
        """Resets all captured tasks."""
        RPCService._log_request(request, context)

        self.memory.clear_tasks()
        return Null()

    def get_metrics(self, request, context):
        """Returns the server metrics.

        Returns:
            clearly_pb2.StatsMessage

        """
        RPCService._log_request(request, context)

        m = self.memory
        return StatsMessage(
            task_count=m.task_count,
            event_count=m.event_count,
            len_tasks=len(m.tasks),
            len_workers=len(m.workers)
        )

    @staticmethod
    def _log_request(request, context):  # pragma: no cover
        req_name = request.DESCRIPTOR.full_name
        req_text = ' '.join(part.strip() for part in str(request).splitlines())
        logger.debug('[%s] %s { %s }', context.peer(), req_name, req_text)
