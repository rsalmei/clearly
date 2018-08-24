import logging
# noinspection PyCompatibility
from concurrent import futures

import click
import grpc
from celery import Celery

from .event_core.event_listener import EventListener
from .event_core.streaming_dispatcher import StreamingDispatcher
from .protos import clearly_pb2_grpc
from .server import ClearlyServer
from .utils.colors import Colors

try:
    # noinspection PyCompatibility
    from queue import Queue, Empty
except ImportError:  # pragma: no cover
    # noinspection PyCompatibility,PyUnresolvedReferences
    from Queue import Queue, Empty

logger = logging.getLogger('clearly.command_line')


@click.group()
@click.version_option()
@click.option('--debug', help='Enables debug logging', is_flag=True)
def clearly(debug):
    """Clearly command line tools."""
    f = Colors.DIM('%(asctime)s') + Colors.MAGENTA(' %(name)s') + Colors.BLUE(' %(levelname)s') + ' %(message)s'
    logging.basicConfig(level=logging.WARNING, format=f)
    logging.getLogger('clearly').setLevel(logging.DEBUG if debug else logging.INFO)


@clearly.command()
@click.argument('broker')
@click.option('--backend', '-b',
              help='Enables fetching task results from the result backend, like "redis://localhost"')
@click.option('--port', '-p', default=12223, help='Listen port for Clearly Server')
@click.option('--max_tasks', '-t', default=10000, help='Maximum number of tasks in memory')
@click.option('--max_workers', '-w', default=100, help='Maximum number of workers in memory')
def server(broker, backend, port, max_tasks, max_workers):
    """
    Starts the Clearly Server.

        BROKER: The broker being used by celery, like "amqp://localhost".
    """
    app = Celery(broker=broker, backend=backend)
    queue_listener_dispatcher = Queue()
    listener = EventListener(app, queue_listener_dispatcher,
                             max_tasks_in_memory=max_tasks,
                             max_workers_in_memory=max_workers)
    dispatcher = StreamingDispatcher(queue_listener_dispatcher)
    clearlysrv = ClearlyServer(listener, dispatcher)
    _serve(clearlysrv, port)


ONE_DAY_IN_SECONDS = 24 * 60 * 60


def _serve(instance, port):
    logger.info('Initiating gRPC server: port=%d', port)

    gserver = grpc.server(futures.ThreadPoolExecutor())
    clearly_pb2_grpc.add_ClearlyServerServicer_to_server(instance, gserver)
    gserver.add_insecure_port('[::]:{}'.format(port))

    logger.info('gRPC server ok')
    gserver.start()

    import time
    try:
        while True:
            time.sleep(ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        gserver.stop(None)
