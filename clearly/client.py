# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals

from Queue import Queue

from celery import states
from datetime import datetime
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import Python3TracebackLexer

from .safe_compiler import safe_compile_text
from .serializer import TaskInfo, WorkerInfo
from .server import ClearlyServer
from .text_highlighter import typed_text
from .utils.colors import colors

HEADER_SIZE = 8
HEADER_PADDING = ' ' * HEADER_SIZE
EMPTY = colors.DIM(':)')
DIM_NONE = colors.DIM(colors.CYAN('None'))


class ClearlyClient(object):
    """Simple and real-time monitor for celery.
    Client object, to display and manage server captured tasks and workers.

        Attributes:
            _clearly_server: the server instance
    """

    def __init__(self, app=None, broker_url=None,
                 max_tasks_in_memory=1000, max_workers_in_memory=100):
        """Constructs a client instance.
        
        Args:
            app (Optional[celery.app]): a configured celery app instance
            broker_url (Optional[str]): a broker connection string like
             'amqp://guest@localhost//'

        """

        lexer = Python3TracebackLexer()
        formatter = Terminal256Formatter(style='native')
        self._tb_highlighter = lambda tb: highlight(tb, lexer, formatter)

        self._clearly_server = ClearlyServer(app, broker_url,
                                             max_tasks_in_memory,
                                             max_workers_in_memory)

    def start(self):
        """Starts the real-time engine that captures tasks. It will capture 
        all tasks being sent to celery and all workers known to it.
        
        This will be run in the background, so you can still send other
        commands or analyze stats and real-time date without losing any
        updates.
        
        """

        self._clearly_server.start()

    def capture(self, pattern=None, negate=False,
                params=False, success=False, error=True):
        """Starts the real-time engine that captures tasks. It will capture
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
            negate (bool): if True, finds tasks that do not match criteria
            params (bool): if True shows params of all tasks
                default is False
            success (bool): if True shows successful tasks' results
                default is False
            error (bool): if True shows failed tasks' results
                default is True, as you monitoring to find errors, right?

        """
        self.start()
        with self._clearly_server \
                .client_connect(pattern, negate) as q:  # type: Queue
            try:
                while True:
                    obj = q.get(timeout=99999)
                    if isinstance(obj, TaskInfo):
                        self._display_task(obj,
                                           params and obj.created,
                                           _is_to_result(obj.state,
                                                         success,
                                                         error))
                    elif isinstance(obj, WorkerInfo):
                        self._display_worker(obj, True)
                    else:
                        print('unknown event:', obj)
            except KeyboardInterrupt:
                pass

    def stop(self):
        """Stops the background engine, without losing anything already
        captured.

        """
        self._clearly_server.stop()

    def stats(self):
        """Lists some metrics of your actual and capturing system.
        Those are:
            Tasks processed: the total number of reentrant tasks processed,
                which includes retry attempts.
            Events processed: number of events captured and processed.
            Tasks stored: actual number of unique tasks processed.
            Workers stored: number of unique workers already seen.

        """
        task_count, event_count, tasks, workers = self._clearly_server.stats()
        print(colors.DIM('Processed:'),
              '\ttasks', colors.RED(task_count),
              '\tevents', colors.RED(event_count))
        print(colors.DIM('Stored:'),
              '\ttasks', colors.RED(tasks),
              '\tworkers', colors.RED(workers))

    def tasks(self, pattern=None, state=None, negate=False,
              params=None, success=False, error=False):
        """Filters captured tasks and prints their current status.
        There are a few params with different defaults from the equivalent
        capture method. This is because here we have more info about the tasks,
        and so it can use new tricks.
        
        Args:
            pattern (Optional[str]): a pattern to filter tasks
                ex.: '^dispatch|^email' to filter names starting with those
                      or 'dispatch.*123456' to filter that exact name and number
                      or even '123456' to filter that exact number anywhere.
            state (Optional[str]): a state to filter tasks
            negate (bool): if True, finds tasks that do not match criteria
            params (Optional[bool]): if True shows params of all tasks,
                if False doesn't, if None use the success or error,
                depending on the final state
                default is None
            success (bool): if True shows successful tasks' results
                default is False
            error (bool): if True shows failed tasks' tracebacks
                default is False, to get an overview.

        """
        for task in self._clearly_server.tasks(pattern, state,
                                               negate):  # type:TaskInfo
            show = _is_to_result(task.state, success, error)
            self._display_task(task,
                               params if params is not None else show,
                               show)

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
        for worker in self._clearly_server.workers(pattern,
                                                   negate):  # type:WorkerInfo
            self._display_worker(worker, stats)

    def task(self, task_uuid):
        """Shows one specific task.

        Args:
            task_uuid (str): the task id

        """
        task = self._clearly_server.task(task_uuid)
        if task:
            self._display_task(task, True, True)

    def seen_tasks(self):
        """Shows a list of task types seen.

        """
        print('\n'.join(self._clearly_server.seen_tasks()))

    def reset(self):
        """Resets all captured tasks.
        
        """
        self._clearly_server.reset()

    def _display_task(self, task, params, result):
        ts = datetime.fromtimestamp(task.timestamp)
        print(colors.DIM(ts.strftime('%H:%M:%S.%f')[:-3]), end=' ')
        if task.created:
            print(colors.BLUE(task.name),
                  colors.MAGENTA(task.routing_key[len(task.name):] or '-'
                                 if task.routing_key else '?'),
                  colors.DIM(task.uuid))
        else:
            print(self._task_state(task.state),
                  colors.DIM(colors.BLUE(task.retries)),
                  end=' ')
            print(colors.BLUE(task.name), colors.DIM(task.uuid))

        if params:
            print(colors.DIM('{:>{}}'.format('args:', HEADER_SIZE)),
                  typed_text(safe_compile_text(task.args),
                             wrap=False) or EMPTY)
            print(colors.DIM('{:>{}}'.format('kwargs:', HEADER_SIZE)),
                  typed_text(safe_compile_text(task.kwargs),
                             wrap=False, kdict=True) or EMPTY)

        if result:
            if task.result:
                output = typed_text(task.result)
            else:
                output = self._tb_highlighter(task.traceback) \
                    .replace('\n', '\n' + HEADER_PADDING).strip()
            print(colors.DIM('{:>{}}'.format('==>', HEADER_SIZE)), output)

    def _display_worker(self, worker, stats):
        print(self._worker_state(worker.alive),
              colors.DIM(colors.CYAN(worker.hostname)),
              colors.DIM(colors.YELLOW(str(worker.pid))))

        if stats:
            print(colors.DIM('{:>{}}'.format('sw:', HEADER_SIZE)),
                  colors.DIM(colors.CYAN(worker.sw_sys)),
                  worker.sw_ident,
                  colors.ORANGE(worker.sw_ver))
            print(colors.DIM('{:>{}}'.format('load:', HEADER_SIZE)),
                  worker.loadavg or DIM_NONE,
                  colors.DIM('processed:'), worker.processed or DIM_NONE)
            if worker.alive:
                if worker.heartbeat:
                    ts = datetime.fromtimestamp(worker.heartbeat)
                    tsstr = ts.strftime('%H:%M:%S.%f')[:-3]
                else:
                    tsstr = DIM_NONE
                print(colors.DIM('{:>{}}'.format('heartbeat:', HEADER_SIZE)),
                      '/{}s'.format(worker.freq),
                      colors.DIM(tsstr))

    @staticmethod
    def _task_state(state):
        result = '{:>{}}'.format(state, HEADER_SIZE)
        if state == states.SUCCESS:  # final state in BOLD
            return colors.BOLD(colors.GREEN(result))
        if state in (states.FAILURE, states.REVOKED):  # final states too
            return colors.BOLD(colors.RED(result))
        return colors.YELLOW(result)  # transient states

    @staticmethod
    def _worker_state(alive):
        result = '{:>{}}'.format('ONLINE' if alive else 'OFFLINE', HEADER_SIZE)
        if alive:
            return colors.BOLD(colors.GREEN(result))
        return colors.BOLD(colors.RED(result))


def _is_to_result(state, success, error):
    return (state == states.FAILURE and error) \
           or (state == states.SUCCESS and success)
