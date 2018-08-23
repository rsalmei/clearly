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


class ClearlyClient():
    """Simple and real-time monitor for celery.
    Client object, to display and manage server captured tasks and workers.

        Attributes:
            stub: the server stub instance
    """

    def __init__(self, host='localhost', port=12223):
        """Constructs a client instance.
        
        Args:
            host (str): the hostname of the server
            port (int): the port of the server
        """

        channel = grpc.insecure_channel('{}:{}'.format(host, port))
        self.stub = clearly_pb2_grpc.ClearlyServerStub(channel)

    def capture(self, pattern=None, negate=False, workers=None, negate_workers=False,
                params=None, success=False, error=True, stats=False):
        """Starts the real-time engine that captures events. It will capture
        all tasks being sent to celery and all workers known to it.

        This will be run in the foreground, so you can see in real-time
        exactly what your celery workers are doing.
        You can press CTRL+C at any time to stop it, without losing any
        updates, which are still being captured in the background.
        
        Args:
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
            for realtime in self.stub.capture_realtime(request):
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
        """Lists some metrics of your actual and capturing system.
        Those are:
            Tasks processed: the total number of reentrant tasks processed,
                which includes retry attempts.
            Events processed: number of events captured and processed.
            Tasks stored: actual number of unique tasks processed.
            Workers stored: number of unique workers already seen.
        """
        stats = self.stub.get_stats(clearly_pb2.Empty())
        print(Colors.DIM('Processed:'),
              '\ttasks', Colors.RED(stats.task_count),
              '\tevents', Colors.RED(stats.event_count))
        print(Colors.DIM('Stored:'),
              '\ttasks', Colors.RED(stats.len_tasks),
              '\tworkers', Colors.RED(stats.len_workers))

    def tasks(self, pattern=None, negate=False, state=None,
              params=None, success=False, error=True):
        """Filters stored tasks and prints their current status.
        There are a few params with different defaults from the equivalent
        capture method. This is because here we have more info about the tasks,
        and so it can use new tricks.
        
        Args:
            pattern (Optional[str]): a pattern to filter tasks
                ex.: '^dispatch|^email' to filter names starting with those
                      or 'dispatch.*123456' to filter that exact name and number
                      or even '123456' to filter that exact number anywhere.
            negate (bool): if True, finds tasks that do not match criteria
            state (Optional[str]): a state to filter tasks
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
            state_pattern=state or '.',
        )
        for task in self.stub.filter_tasks(request):
            ClearlyClient._display_task(task, params, success, error)

    def workers(self, pattern=None, negate=False, stats=True):
        """Filters known workers and prints their current status.
        
        Args:
            pattern (Optional[str]): a pattern to filter workers
                ex.: '^dispatch|^email' to filter names starting with those
                      or 'dispatch.*123456' to filter that exact name and number
                      or even '123456' to filter that exact number anywhere.
            negate (bool): if True, finds tasks that do not match criteria
            stats (bool): if True shows worker stats
        """
        request = clearly_pb2.FilterWorkersRequest(
            workers_filter=clearly_pb2.PatternFilter(pattern=pattern or '.', negate=negate),
        )
        for worker in self.stub.filter_workers(request):
            ClearlyClient._display_worker(worker, stats)

    def task(self, task_uuid):
        """Shows one specific task.

        Args:
            task_uuid (str): the task id
        """
        request = clearly_pb2.FindTaskRequest(task_uuid=task_uuid)
        task = self.stub.find_task(request)
        if task:
            ClearlyClient._display_task(task, True, True, True)
        else:
            print(EMPTY)

    def seen_tasks(self):
        """Shows a list of task types seen."""
        print('\n'.join(self.stub.seen_tasks(clearly_pb2.Empty())))

    def reset(self):
        """Resets all captured tasks."""
        self.stub.reset_tasks(clearly_pb2.Empty())

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
        result = params != False and (task.state in states.READY_STATES) and show_result
        if first_seen or result:
            print(type(task.kwargs), task.kwargs)
            safe_compile_text(task.kwargs, 1)
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
