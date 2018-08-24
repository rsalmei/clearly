# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals

from datetime import datetime

import grpc
from celery import states

from .code_highlighter import create_traceback_highlighter, typed_code
from .protos import clearly_pb2, clearly_pb2_grpc
from .safe_compiler import safe_compile_text
from .utils import worker_states
from .utils.colors import Colors

HEADER_SIZE = 8
HEADER_PADDING = ' ' * HEADER_SIZE
EMPTY = Colors.DIM(':)')
DIM_NONE = Colors.DIM(Colors.CYAN('None'))
TRACEBACK_HIGHLIGHTER = create_traceback_highlighter()


class ClearlyClient(object):
    """Simple and real-time monitor for celery.
    Client object, to display and manage server captured tasks and workers.

        Attributes:
            _stub: the server stub instance
    """

    def __init__(self, host='localhost', port=12223):
        """Constructs a client instance.
        
        Args:
            host (str): the hostname of the server
            port (int): the port of the server
        """

        channel = grpc.insecure_channel('{}:{}'.format(host, port))
        self._stub = clearly_pb2_grpc.ClearlyServerStub(channel)

    def capture(self, pattern=None, negate=False, workers=None, negate_workers=False,
                params=None, success=False, error=True, stats=False):
        """Starts capturing selected events in real-time. You can filter exactly what
        you want to see, as the Clearly Server handles all tasks and workers updates
        being sent to celery. Several clients can see different sets of events at the
        same time.

        This runs in the foreground, so you can see in real-time exactly what your
        celery workers are doing.
        Press CTRL+C at any time to stop it.

        Args:
            Filter args:

            pattern (Optional[str]): a pattern to filter tasks to capture.
                ex.: '^dispatch|^email' to filter names starting with that
                      or 'dispatch.*123456' to filter that exact name and number
                      or even '123456' to filter that exact number anywhere.
            negate (bool): if True, finds tasks that do not match criteria.
            workers (Optional[str]): a pattern to filter workers to capture.
                ex.: 'service|priority' to filter names containing that
            negate_workers (bool): if True, finds workers that do not match criteria.
            params (Optional[bool]): if True shows args and kwargs in first/last state,
                doesn't show if False, and follows the successes and errors if None.
                default is None

            Display args:

            success (bool): if True shows successful tasks' results.
                default is False
            error (bool): if True shows failed and retried tasks' tracebacks.
                default is True, as you're monitoring to find errors, right?
            stats (bool): if True shows complete workers' stats.
                default is False
        """
        request = clearly_pb2.CaptureRequest(
            tasks_capture=clearly_pb2.PatternFilter(pattern=pattern or '.', negate=negate),
            workers_capture=clearly_pb2.PatternFilter(pattern=workers or '.', negate=negate_workers),
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

    def stats(self):
        """Lists some metrics of the capturing system:

            Tasks processed: the total number of reentrant tasks processed,
                which includes retry attempts.
            Events processed: number of events captured and processed.
            Tasks stored: actual number of unique tasks processed.
            Workers stored: number of unique workers already seen.
        """
        stats = self._stub.get_stats(clearly_pb2.Empty())
        print(Colors.DIM('Processed:'),
              '\ttasks', Colors.RED(stats.task_count),
              '\tevents', Colors.RED(stats.event_count))
        print(Colors.DIM('Stored:'),
              '\ttasks', Colors.RED(stats.len_tasks),
              '\tworkers', Colors.RED(stats.len_workers))

    def tasks(self, pattern=None, negate=False, state=None, limit=None, reverse=True,
              params=None, success=False, error=True):
        """Filters stored tasks and prints their current status.

        Note that, to be able to list the tasks sorted chronologically, celery retrieves
        tasks from the LRU event heap instead of the dict storage, so the total number
        of tasks fetched may be different than the server `max_tasks` setting. For
        instance, the `limit` field refers to max events searched, not max tasks.

        Args:
            Filter args:

            pattern (Optional[str]): a pattern to filter tasks
                ex.: '^dispatch|^email' to filter names starting with those
                      or 'dispatch.*123456' to filter that exact name and number
                      or even '123456' to filter that exact number anywhere.
            negate (bool): if True, finds tasks that do not match criteria
            state (Optional[str]): a state to filter tasks
            limit (int): the maximum number of events to fetch tasks from
                if None or 0, fetches all.
            reverse (bool): if True (default), shows the most recent first

            Display args:

            params (Optional[bool]): if True shows called args and kwargs,
                skips if False, and follows outcome if None.
                default is None
            success (bool): if True shows successful tasks' results
                default is False
            error (bool): if True shows failed and retried tasks' tracebacks.
                default is True, as you're monitoring to find errors, right?
        """
        request = clearly_pb2.FilterTasksRequest(
            tasks_filter=clearly_pb2.PatternFilter(pattern=pattern or '.', negate=negate),
            state_pattern=state or '.', limit=limit, reverse=reverse
        )
        i = -1
        for i, task in enumerate(self._stub.filter_tasks(request)):
            ClearlyClient._display_task(task, params, success, error)
        print(Colors.DIM('fetched:'), Colors.BOLD(i + 1))

    def workers(self, pattern=None, negate=False, stats=True):
        """Filters known workers and prints their current status.
        
        Args:
            Filter args:

            pattern (Optional[str]): a pattern to filter workers
                ex.: '^dispatch|^email' to filter names starting with those
                      or 'dispatch.*123456' to filter that exact name and number
                      or even '123456' to filter that exact number anywhere.
            negate (bool): if True, finds tasks that do not match criteria

            Display args:

            stats (bool): if True shows worker stats
        """
        request = clearly_pb2.FilterWorkersRequest(
            workers_filter=clearly_pb2.PatternFilter(pattern=pattern or '.', negate=negate),
        )
        i = -1
        for i, worker in enumerate(self._stub.filter_workers(request)):
            ClearlyClient._display_worker(worker, stats)
        print(Colors.DIM('fetched:'), Colors.BOLD(i + 1))

    def task(self, task_uuid):
        """Finds one specific task.

        Args:
            task_uuid (str): the task id
        """
        request = clearly_pb2.FindTaskRequest(task_uuid=task_uuid)
        task = self._stub.find_task(request)
        if task.uuid:
            ClearlyClient._display_task(task, True, True, True)
        else:
            print(EMPTY)

    def seen_tasks(self):
        """Shows a list of seen task types."""
        print('\n'.join(self._stub.seen_tasks(clearly_pb2.Empty()).task_types))

    def reset(self):
        """Resets all captured tasks."""
        self._stub.reset_tasks(clearly_pb2.Empty())

    @staticmethod
    def _display_task(task, params, success, error):
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
                  Colors.DIM(Colors.BLUE(task.retries)),
                  end=' ')
            print(Colors.BLUE(task.name), Colors.DIM(task.uuid))

        show_result = (task.state in states.EXCEPTION_STATES and error) \
                      or (task.state == states.SUCCESS and success)

        first_seen = bool(params) and task.created
        result = params is not False and (task.state in states.READY_STATES) and show_result
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
    def _display_worker(worker, stats):
        print(ClearlyClient._worker_state(worker.state),
              Colors.DIM(Colors.CYAN(worker.hostname)),
              Colors.DIM(Colors.YELLOW(str(worker.pid))))

        if stats:
            print(Colors.DIM('{:>{}}'.format('sw:', HEADER_SIZE)),
                  Colors.DIM(Colors.CYAN(worker.sw_sys)),
                  worker.sw_ident,
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
    def _task_state(state):
        result = '{:>{}}'.format(state, HEADER_SIZE)
        if state == states.SUCCESS:  # final state in BOLD
            return Colors.BOLD(Colors.GREEN(result))
        if state in (states.FAILURE, states.REVOKED):  # final states too
            return Colors.BOLD(Colors.RED(result))
        return Colors.YELLOW(result)  # transient states

    @staticmethod
    def _worker_state(state):
        result = '{:>{}}'.format(state, HEADER_SIZE)
        if state == worker_states.ONLINE:
            return Colors.BOLD(Colors.GREEN(result))
        return Colors.BOLD(Colors.RED(result))
