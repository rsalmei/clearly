# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals

import logging
import operator
from concurrent import futures

import grpc
import re
from about_time import about_time
from celery.events.state import Task, Worker

from .event_core.event_listener import EventListener
from .event_core.events import TaskData, WorkerData
from .event_core.streaming_dispatcher import StreamingDispatcher
from .protos import clearly_pb2, clearly_pb2_grpc
from .utils.colors import Colors
from .utils.data import accepts

try:
    # noinspection PyCompatibility
    from queue import Queue, Empty
except ImportError:  # pragma: no cover
    # noinspection PyCompatibility,PyUnresolvedReferences
    from Queue import Queue, Empty

ONE_DAY_IN_SECONDS = 24 * 60 * 60

logger = logging.getLogger('clearly.server')

PATTERN_PARAMS_OP = operator.attrgetter('pattern', 'negate')
WORKER_HOSTNAME_OP = operator.attrgetter('hostname')


class ClearlyServer(clearly_pb2_grpc.ClearlyServerServicer):
    """Simple and real-time monitor for celery.
    Server object, to capture events and handle tasks and workers.
    
    Attributes:
        listener (EventListener): the object that listens and keeps celery events
        dispatcher (StreamingDispatcher): the mechanism to dispatch data to clients
    """

    def __init__(self, listener, dispatcher):
        """Constructs a server instance.
        
        Args:
            listener (EventListener): the object that listens and keeps celery events
            dispatcher (StreamingDispatcher): the mechanism to dispatch data to clients
        """
        logger.info('Creating %s', ClearlyServer.__name__)

        self.listener = listener
        self.dispatcher = dispatcher

    def capture_realtime(self, request, context):
        """

        Args:
            request (clearly_pb2.CaptureRequest):
            context:

        Returns:

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

    @staticmethod
    def _event_to_pb(event):
        """Supports converting internal TaskData and WorkerData, as well as
        celery Task and Worker to proto buffers messages.

        Args:
            event (Union[TaskData|Task|WorkerData|Worker]):

        Returns:
            ProtoBuf object

        """
        if isinstance(event, (TaskData, Task)):
            key, klass = 'task', clearly_pb2.TaskMessage
        elif isinstance(event, (WorkerData, Worker)):
            key, klass = 'worker', clearly_pb2.WorkerMessage
        else:
            raise ValueError('unknown event')
        keys = klass.DESCRIPTOR.fields_by_name.keys()
        data = {str(k): v for k, v in  # str() for py2
                getattr(event, '_asdict',  # internal TaskData and WorkerData
                        lambda: {f: getattr(event, f) for f in event._fields})  # celery Task and Worker
                ().items() if k in keys}
        return key, klass(**data)

    def filter_tasks(self, request, context):
        """Filter tasks by matching patterns to name, routing key and state."""
        _log_request(request, context)
        tasks_pattern, tasks_negate = PATTERN_PARAMS_OP(request.tasks_filter)
        state_pattern = request.state_pattern
        limit, reverse = request.limit, request.reverse

        pregex = re.compile(tasks_pattern)  # pattern filter condition
        sregex = re.compile(state_pattern)  # state filter condition

        def pcondition(task):
            return accepts(pregex, tasks_negate, task.name, task.routing_key)

        def scondition(task):
            return accepts(sregex, tasks_negate, task.state)

        found_tasks = (task for _, task in
                       self.listener.memory.tasks_by_time(limit=limit or None,
                                                          reverse=reverse)
                       if pcondition(task) and scondition(task))

        def callback(t):
            logger.debug('%s iterated %d tasks in %s (%s)', self.filter_tasks.__name__,
                         t.count, t.duration_human, t.throughput_human)

        for task in about_time(callback, found_tasks):
            yield ClearlyServer._event_to_pb(task)[1]

    def filter_workers(self, request, context):
        """Filter workers by matching a pattern to hostname."""
        _log_request(request, context)
        workers_pattern, workers_negate = PATTERN_PARAMS_OP(request.workers_filter)

        hregex = re.compile(workers_pattern)  # hostname filter condition

        def hcondition(worker):
            return accepts(hregex, workers_negate, worker.hostname)  # pragma: no branch

        found_workers = (worker for worker in
                         sorted(self.listener.memory.workers.values(),
                                key=WORKER_HOSTNAME_OP)
                         if hcondition(worker))

        def callback(t):
            logger.debug('%s iterated %d workers in %s (%s)', self.filter_workers.__name__,
                         t.count, t.duration_human, t.throughput_human)

        for worker in about_time(callback, found_workers):
            yield ClearlyServer._event_to_pb(worker)[1]

    def find_task(self, request, context):
        """Finds one specific task."""
        _log_request(request, context)
        task = self.listener.memory.tasks.get(request.task_uuid)
        if not task:
            return clearly_pb2.TaskMessage()
        return ClearlyServer._event_to_pb(task)[1]

    def seen_tasks(self, request, context):
        """Returns all seen task types."""
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
        """Returns the server statistics."""
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
    logger.debug('%s { %s }', req_name, req_text)


def _setup_logging(debug):  # pragma: no cover
    f = Colors.DIM('%(asctime)s') + Colors.MAGENTA(' %(name)s') + Colors.BLUE(' %(levelname)s') + ' %(message)s'
    logging.basicConfig(level=logging.WARNING, format=f)
    logging.getLogger('clearly').setLevel(logging.DEBUG if debug else logging.INFO)


def start_server(broker, backend=None, port=12223,
                 max_tasks=10000, max_workers=100,
                 blocking=True, debug=False):  # pragma: no cover
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

    import time
    try:
        while True:
            time.sleep(ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        gserver.stop(None)
