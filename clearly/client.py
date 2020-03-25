import functools
from datetime import datetime
from typing import Any, Callable, Iterable, Optional

import grpc
from about_time import about_time
from about_time.core import HandleStats
from celery import states

from .protos import clearly_pb2, clearly_pb2_grpc
from .code_highlighter import traceback_highlighter_factory, typed_code
from .safe_compiler import safe_compile_text
from .utils import worker_states
from .utils.colors import Colors

HEADER_SIZE = 8
HEADER_PADDING = ' ' * HEADER_SIZE
EMPTY = Colors.DIM(':)')
DIM_NONE = Colors.CYAN_DIM('None')
TRACEBACK_HIGHLIGHTER = traceback_highlighter_factory()


def set_user_friendly_grpc_errors(fn: Callable[..., None]) -> Callable[..., None]:
    @functools.wraps(fn)
    def inner(self, *args, **kwargs):
        try:
            fn(self, *args, **kwargs)
        except grpc.RpcError as e:
            if self.debug:
                raise
            # noinspection PyUnresolvedReferences
            print('{}: {} ({})'.format(
                Colors.BOLD('Server communication error'),
                Colors.RED(e.details()),
                Colors.DIM(e.code())
            ))

    return inner


class ClearlyClient:
    """Main client object, which interfaces with the Clearly server backend, sends
    commands and displays captured events.

    Attributes:
        _stub: the server stub instance

    """

    def __init__(self, host: str = 'localhost', port: int = 12223, debug: bool = False):
        """Construct a Clearly Client instance.
        
        Args:
            host: the hostname of the server
            port: the port of the server

        """
        self.debug = debug
        channel = grpc.insecure_channel('{}:{}'.format(host, port))
        self._stub = clearly_pb2_grpc.ClearlyServerStub(channel)

    def capture_tasks(self, pattern=None, negate=False, params=None, success=False, error=True):
        """Start capturing task events in real time, so you can instantly see exactly
        what your publishers and workers are doing. Filter as much as you can to find
        what you need, and don't worry as the Clearly Server will still seamlessly
        handle all tasks updates.

        This runs in the foreground. Press CTRL+C at any time to stop it.

        Args:
            Filter args:
            ------------

            pattern (Optional[str]): a simple pattern to filter tasks by name.
                ex.: 'email' to filter task names containing that word anywhere
                     '^trigger|^email' to filter names starting with any of those words
                     'trigger.*123456' to filter names with those words in that sequence
            negate (bool): send True to filter tasks that do not match criteria.

            Display args:
            -------------

            params: if True shows args and kwargs in the first and
                last seen states, if False never shows, and if None follows the
                success and error arguments.
                default is None
            success: if True shows successful tasks' results.
                default is False
            error: if True shows failed and retried tasks' tracebacks.
                default is True, as you're monitoring to find errors, right?

        """
        return self.capture(pattern=pattern, negate=negate, workers='.', negate_workers=True,
                            params=params, success=success, error=error, stats=False)

    def capture_workers(self, pattern=None, negate=False, stats=False):
        """Start capturing worker events in real time, so you can instantly see exactly
        what your workers states are. Filter as much as you can to find
        what you need, and don't worry as the Clearly Server will still seamlessly
        handle all tasks and workers updates.

        This runs in the foreground. Press CTRL+C at any time to stop it.

        Args:
            Filter args:
            ------------

            pattern (Optional[str]): a simple pattern to filter workers by name.
                ex.: 'email' to filter worker names containing that word anywhere
                     'service|priority' to filter names containing any of those words
            negate (bool): send True to filter workers that do not match criteria.

            Display args:
            -------------

            stats: if True shows complete workers' stats, default is False

        """
        return self.capture(pattern='.', negate=True, workers=pattern, negate_workers=negate,
                            params=False, success=False, error=False, stats=stats)

    @set_user_friendly_grpc_errors
    def capture(self, pattern=None, negate=False, workers=None, negate_workers=False,
                params=None, success=False, error=True, stats=False):
        """Start capturing all events in real time, so you can instantly see exactly
        what your publishers and workers are doing. Filter as much as you can to find
        what you need, and don't worry as the Clearly Server will still seamlessly
        handle all tasks and workers updates.

        This runs in the foreground. Press CTRL+C at any time to stop it.

        See Also:
            ClearlyClient#capture_tasks()
            ClearlyClient#capture_workers()

        """
        request = clearly_pb2.CaptureRequest(
            tasks_capture=clearly_pb2.PatternFilter(pattern=pattern or '.',
                                                    negate=negate),
            workers_capture=clearly_pb2.PatternFilter(pattern=workers or '.',
                                                      negate=negate_workers),
        )
        try:
            for realtime in self._stub.capture_realtime(request):
                if realtime.HasField('task'):
                    ClearlyClient._display_task(realtime.task, params, success, error)
                elif realtime.HasField('worker'):
                    ClearlyClient._display_worker(realtime.worker, stats)
                else:
                    print('unknown event:', realtime)
                    break
        except KeyboardInterrupt:
            pass

    @set_user_friendly_grpc_errors
    def stats(self) -> None:
        """List some metrics about the capturing system itself, which of course
        reflects the actual celery pool being monitored.

        Shows:
            Tasks processed: number of tasks processed, including retries
            Events processed: number of events processed, including workers and heartbeats
            Tasks stored: number of unique tasks processed
            Workers stored: number of unique workers seen

        """
        stats = self._stub.get_stats(clearly_pb2.Empty())
        print(Colors.DIM('Processed:'),
              '\ttasks', Colors.RED(stats.task_count),
              '\tevents', Colors.RED(stats.event_count))
        print(Colors.DIM('Stored:'),
              '\ttasks', Colors.RED(stats.len_tasks),
              '\tworkers', Colors.RED(stats.len_workers))

    @staticmethod
    def _fetched_callback(at: HandleStats) -> None:  # pragma: no cover
        print('{} {} in {} ({})'.format(
            Colors.DIM('fetched:'), Colors.BOLD(at.count),
            Colors.GREEN(at.duration_human), Colors.GREEN(at.throughput_human)
        ))

    @set_user_friendly_grpc_errors
    def tasks(self, pattern=None, negate=False, state=None, limit=None, reverse=True,
              params=None, success=False, error=True):
        """Fetch current data from past tasks.

        Note that the `limit` field is just a hint, it may not be accurate.
        Even the total number of tasks fetched may be slightly different than
        the server `max_tasks` setting.

        Args:
            Filter args:
            ------------

            pattern (Optional[str]): a simple pattern to filter tasks by name.
                ex.: 'email' to filter task names containing that word anywhere
                     '^trigger|^email' to filter names starting with any of those words
                     'trigger.*123456' to filter names with those words in that sequence
            negate (bool): send True to filter tasks that do not match criteria.
            state (Optional[str]): a celery task state to filter
            limit (int): the maximum number of events to fetch
                if None or 0, fetches all.
            reverse (bool): if True (default), shows the most recent first

            Display args:
            -------------

            params: if True shows args and kwargs in the first and
                last seen states, if False never shows, and if None follows the
                success and error arguments.
                default is None
            success: if True shows successful tasks' results.
                default is False
            error: if True shows failed and retried tasks' tracebacks.
                default is True, as you're monitoring to find errors, right?

        """
        request = clearly_pb2.FilterTasksRequest(
            tasks_filter=clearly_pb2.PatternFilter(pattern=pattern or '.',
                                                   negate=negate),
            state_pattern=state or '.', limit=limit, reverse=reverse
        )

        at = about_time(self._stub.filter_tasks(request))
        for task in at:
            ClearlyClient._display_task(task, params, success, error)
        ClearlyClient._fetched_callback(at)

    @set_user_friendly_grpc_errors
    def workers(self, pattern=None, negate=False, stats=True):
        """Fetch current data from known workers.
        
        Args:
            Filter args:
            ------------

            pattern (Optional[str]): a simple pattern to filter workers by name.
                ex.: 'email' to filter worker names containing that word anywhere
                     'service|priority' to filter names containing any of those words
            negate (bool): send True to filter workers that do not match criteria.

            Display args:
            -------------

            stats: if True shows complete workers' stats, default is False

        """
        request = clearly_pb2.FilterWorkersRequest(
            workers_filter=clearly_pb2.PatternFilter(pattern=pattern or '.',
                                                     negate=negate),
        )

        at = about_time(self._stub.filter_workers(request))
        for worker in at:
            ClearlyClient._display_worker(worker, stats)
        ClearlyClient._fetched_callback(at)

    @set_user_friendly_grpc_errors
    def task(self, task_uuid: str) -> None:
        """Fetch current data from a specific task.

        Args:
            task_uuid: the task uuid

        """
        request = clearly_pb2.FindTaskRequest(task_uuid=task_uuid)
        task = self._stub.find_task(request)
        if task.uuid:
            ClearlyClient._display_task(task, True, True, True)
        else:
            print(EMPTY)

    @set_user_friendly_grpc_errors
    def seen_tasks(self) -> None:
        """Fetch a list of seen task types."""
        print('\n'.join(self._stub.seen_tasks(clearly_pb2.Empty()).task_types))

    @set_user_friendly_grpc_errors
    def reset(self) -> None:
        """Reset all captured tasks."""
        self._stub.reset_tasks(clearly_pb2.Empty())

    @staticmethod
    def _display_task(task: clearly_pb2.TaskMessage, params: bool,
                      success: bool, error: bool) -> None:
        ts = datetime.fromtimestamp(task.timestamp)
        print(Colors.DIM(ts.strftime('%H:%M:%S.%f')[:-3]), end=' ')
        if task.created:
            routing_key = task.routing_key or EMPTY
            print(Colors.BLUE(task.name),
                  Colors.MAGENTA(routing_key[len(task.name):] or '-'
                                 if routing_key.startswith(task.name)
                                 else routing_key),
                  Colors.DIM(task.uuid))
        else:
            print(ClearlyClient._task_state(task.state),
                  Colors.BLUE_DIM(task.retries),
                  end=' ')
            print(Colors.BLUE(task.name), Colors.DIM(task.uuid))

        show_result = (task.state in states.PROPAGATE_STATES and error) \
            or (task.state == states.SUCCESS and success)

        first_seen = bool(params) and task.created
        result = params is not False and show_result
        if first_seen or result:
            print(Colors.DIM('{:>{}}'.format('args:', HEADER_SIZE)),
                  typed_code(safe_compile_text(task.args),
                             wrap=False) or EMPTY)
            print(Colors.DIM('{:>{}}'.format('kwargs:', HEADER_SIZE)),
                  typed_code(safe_compile_text(task.kwargs),
                             wrap=False) or EMPTY)

        if show_result:
            if task.result:
                output = typed_code(safe_compile_text(task.result))
            elif task.traceback:
                output = TRACEBACK_HIGHLIGHTER(task.traceback) \
                    .replace('\n', '\n' + HEADER_PADDING).strip()
            else:
                output = EMPTY
            print(Colors.DIM('{:>{}}'.format('==>', HEADER_SIZE)), output)

    @staticmethod
    def _display_worker(worker: clearly_pb2.WorkerMessage, stats: bool) -> None:
        print(ClearlyClient._worker_state(worker.state),
              Colors.CYAN_DIM(worker.hostname),
              Colors.YELLOW_DIM(str(worker.pid)))

        if stats:
            print(Colors.DIM('{:>{}}'.format('sw:', HEADER_SIZE)),
                  worker.sw_ident,
                  Colors.CYAN_DIM(worker.sw_sys),
                  Colors.ORANGE(worker.sw_ver))
            print(Colors.DIM('{:>{}}'.format('load:', HEADER_SIZE)),
                  worker.loadavg or DIM_NONE,
                  Colors.DIM('processed:'), worker.processed or DIM_NONE)
            if worker.alive:
                if worker.last_heartbeat:
                    ts = datetime.fromtimestamp(worker.last_heartbeat)
                    tsstr = ts.strftime('%H:%M:%S.%f')[:-3]
                else:
                    tsstr = DIM_NONE
                print(Colors.DIM('{:>{}}'.format('heartbeat:', HEADER_SIZE)),
                      '/{}s'.format(worker.freq),
                      Colors.DIM(tsstr))

    @staticmethod
    def _task_state(state: str) -> None:
        result = '{:>{}}'.format(state, HEADER_SIZE)
        if state == states.SUCCESS:  # final state in BOLD
        if state in (states.FAILURE, states.REVOKED):  # final states too
            return Colors.GREEN_BOLD(result)
            return Colors.RED_BOLD(result)
        return Colors.YELLOW(result)  # transient states

    @staticmethod
        result = '{:>{}}'.format(state, HEADER_SIZE)
    def _worker_state(state: str) -> None:
        if state == worker_states.ONLINE:
            return Colors.GREEN_BOLD(result)
        return Colors.RED_BOLD(result)
