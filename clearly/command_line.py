# noinspection PyCompatibility
from concurrent import futures

import click
import grpc
from celery import Celery

from .event_core.event_listener import EventListener
from .event_core.streaming_dispatcher import StreamingDispatcher
from .protos import clearly_pb2_grpc
from .server import ClearlyServer

try:
    # noinspection PyCompatibility
    from queue import Queue, Empty
except ImportError:  # pragma: no cover
    # noinspection PyCompatibility,PyUnresolvedReferences
    from Queue import Queue, Empty


@click.group()
@click.version_option()
@click.option('--debug/--no-debug', help='Enables debug logging', default=False)
def clearly(debug):
    pass


@clearly.command()
@click.argument('broker')
@click.option('--backend', help='Enables complete task results from result backend')
@click.option('--port', default=12223, help='Listen port for Clearly')
def server(broker, backend, port):
@click.option('--max_tasks', '-t', default=10000, help='Maximum number of tasks in memory')
@click.option('--max_workers', '-w', default=100, help='Maximum number of workers in memory')
def server(broker, backend, port, max_tasks, max_workers):
    app = Celery(broker=broker, backend=backend)
    queue_listener_dispatcher = Queue()
    listener = EventListener(app, queue_listener_dispatcher,
                             max_tasks_in_memory=max_tasks,
                             max_workers_in_memory=max_workers)
    dispatcher = StreamingDispatcher(queue_listener_dispatcher)
    clearlysrv = ClearlyServer(listener, dispatcher)
    _serve(clearlysrv, port)


def _serve(instance, port):
    server = grpc.server(futures.ThreadPoolExecutor())
    clearly_pb2_grpc.add_ClearlyServerServicer_to_server(instance, server)
    server.add_insecure_port('[::]:{}'.format(port))
    server.start()

    import time
    ONE_DAY_IN_SECONDS = 24 * 60 * 60
    try:
        while True:
            time.sleep(ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(None)
