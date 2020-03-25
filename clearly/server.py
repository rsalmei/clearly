import logging
import operator
import re
from concurrent import futures
from queue import Empty, Queue
from typing import Optional

import grpc
from about_time import about_time
from celery.events.state import Task, Worker

from .event_core.event_listener import EventListener
from .event_core.events import TaskData, WorkerData
from .event_core.streaming_dispatcher import StreamingDispatcher
from .protos import clearly_pb2, clearly_pb2_grpc
from .utils.colors import Colors
from .utils.data import accepts

logger = logging.getLogger('clearly.server')

PATTERN_PARAMS_OP = operator.attrgetter('pattern', 'negate')
WORKER_HOSTNAME_OP = operator.attrgetter('hostname')


class ClearlyServer:
    """Main server object, which orchestrates capturing of celery events, see to
    the connected clients' needs, and manages the RPC communication.

    Attributes:
        memory: LRU storage object to keep celery tasks and workers
        listener: the object that listens and keeps celery events
        dispatcher_tasks: the mechanism to dispatch tasks to clients
        dispatcher_workers: the mechanism to dispatch workers to clients
        rpc: the gRPC service

    """

    def __init__(self, broker: str, backend: Optional[str] = None,
                 max_tasks: Optional[int] = None, max_workers: Optional[int] = None):
        """Construct a Clearly Server instance.

        Args:
            broker: the broker being used by the celery system
            backend: the result backend being used by the celery system
            max_tasks: max tasks stored
            max_workers: max workers stored

        """
        max_tasks, max_workers = max_tasks or 10000, max_workers or 100
        logger.info('Creating memory: max_tasks=%d; max_workers=%d', max_tasks, max_workers)
        self.memory = State(max_tasks_in_memory=max_tasks, max_workers_in_memory=max_workers)

        queue_tasks, queue_workers = Queue(), Queue()  # hands new events to be distributed.
        try:
            self.listener = EventListener(broker, queue_tasks, queue_workers, self.memory, backend)
        except TimeoutError as e:
            logger.critical(e)
            sys.exit(1)

        self.dispatcher_tasks = StreamingDispatcher(queue_tasks, Role.TASKS)
        self.dispatcher_workers = StreamingDispatcher(queue_workers, Role.WORKERS)
        self.rpc = RPCService(self.memory, self.dispatcher_tasks, self.dispatcher_workers)
class RPCService(clearly_pb2_grpc.ClearlyServerServicer):
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
        """

        Args:
            request (clearly_pb2.CaptureRequest):
            context:

        Yields:
            clearly_pb2.RealtimeEventMessage

        """
        _log_request(request, context)
        tasks_pattern, tasks_negate = PATTERN_PARAMS_OP(request.tasks_capture)
        workers_pattern, workers_negate = PATTERN_PARAMS_OP(request.workers_capture)

        with self.dispatcher.streaming_client(tasks_pattern, tasks_negate,
                                              workers_pattern, workers_negate) as q:  # type: Queue
            while True:
                try:
                    event_data = q.get(timeout=1)
                except Empty:  # pragma: no cover
                    continue

                key, obj = ClearlyServer._event_to_pb(event_data)
                yield clearly_pb2.RealtimeEventMessage(**{key: obj})

    def filter_tasks(self, request, context):
        """Filter tasks by matching patterns to name, routing key and state.

        Yields:
            clearly_pb2.TaskMessage

        """
        _log_request(request, context)
        tasks_pattern, tasks_negate = PATTERN_PARAMS_OP(request.tasks_filter)
        state_pattern = request.state_pattern
        limit, reverse = request.limit, request.reverse

        pregex = re.compile(tasks_pattern)  # pattern filter condition
        sregex = re.compile(state_pattern)  # state filter condition

        # generators are cool!
        found_tasks = (task for _, task in
                       self.listener.memory.tasks_by_time(limit=limit or None,
                                                          reverse=reverse)
                       if accepts(pregex, tasks_negate, task.name, task.routing_key)
                       and accepts(sregex, tasks_negate, task.state))

        at = about_time(found_tasks)
        for task in at:
            yield ClearlyServer._event_to_pb(task)[1]
        logger.debug('%s iterated %d tasks in %s (%s)', self.filter_tasks.__name__,
                     at.count, at.duration_human, at.throughput_human)

    def filter_workers(self, request, context):
        """Filter workers by matching a pattern to hostname.

        Yields:
            clearly_pb2.WorkerMessage

        """
        _log_request(request, context)
        workers_pattern, workers_negate = PATTERN_PARAMS_OP(request.workers_filter)

        hregex = re.compile(workers_pattern)  # hostname filter condition

        # generators are cool!
        found_workers = (worker for worker in
                         sorted(self.listener.memory.workers.values(),
                                key=WORKER_HOSTNAME_OP)
                         if accepts(hregex, workers_negate, worker.hostname))

        at = about_time(found_workers)
        for worker in at:
            yield ClearlyServer._event_to_pb(worker)[1]
        logger.debug('%s iterated %d workers in %s (%s)', self.filter_workers.__name__,
                     at.count, at.duration_human, at.throughput_human)

    def find_task(self, request, context):
        """Finds one specific task.

        Returns:
            clearly_pb2.TaskMessage

        """
        _log_request(request, context)
        task = self.listener.memory.tasks.get(request.task_uuid)
        if not task:
            return clearly_pb2.TaskMessage()
        return ClearlyServer._event_to_pb(task)[1]

    def seen_tasks(self, request, context):
        """Returns all seen task types.

        Returns:
            clearly_pb2.SeenTasksMessage

        """
        _log_request(request, context)
        result = clearly_pb2.SeenTasksMessage()
        result.task_types.extend(self.listener.memory.task_types())
        return result

    def reset_tasks(self, request, context):
        """Resets all captured tasks."""
        _log_request(request, context)
        self.listener.memory.clear_tasks()
        return clearly_pb2.Empty()

    def get_stats(self, request, context):
        """Returns the server statistics.

        Returns:
            clearly_pb2.StatsMessage

        """
        _log_request(request, context)
        m = self.listener.memory
        return clearly_pb2.StatsMessage(
            task_count=m.task_count,
            event_count=m.event_count,
            len_tasks=len(m.tasks),
            len_workers=len(m.workers)
        )


def _log_request(request, context):  # pragma: no cover
    req_name = request.DESCRIPTOR.full_name
    req_text = ' '.join(part.strip() for part in filter(None, str(request).split('\n')))
    logger.debug('[%s] %s { %s }', context.peer(), req_name, req_text)


def _setup_logging(debug):  # pragma: no cover
    f = Colors.DIM('%(asctime)s') + Colors.MAGENTA(' %(name)s') \
        + Colors.BLUE(' %(levelname)s') + ' %(message)s'
    logging.basicConfig(level=logging.WARNING, format=f)
    logging.getLogger('clearly').setLevel(logging.DEBUG if debug else logging.INFO)


def start_server(broker, backend=None, port=12223,
                 max_tasks=10000, max_workers=100,
                 blocking=False, debug=False):  # pragma: no cover
    """Starts a Clearly Server programmatically."""
    _setup_logging(debug)

    queue_listener_dispatcher = Queue()
    listener = EventListener(broker, queue_listener_dispatcher, backend=backend,
                             max_tasks_in_memory=max_tasks,
                             max_workers_in_memory=max_workers)
    dispatcher = StreamingDispatcher(queue_listener_dispatcher)
    clearlysrv = ClearlyServer(listener, dispatcher)
    return _serve(clearlysrv, port, blocking)


def _serve(instance, port, blocking):  # pragma: no cover
    logger.info('Initiating gRPC server: port=%d', port)

    gserver = grpc.server(futures.ThreadPoolExecutor())
    clearly_pb2_grpc.add_ClearlyServerServicer_to_server(instance, gserver)
    gserver.add_insecure_port('[::]:{}'.format(port))

    logger.info('gRPC server ok')
    gserver.start()

    if not blocking:
        return gserver

    one_day_in_seconds = 24 * 60 * 60
    import time
    try:
        while True:
            time.sleep(one_day_in_seconds)
    except KeyboardInterrupt:
        gserver.stop(None)
